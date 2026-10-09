"""Günlük paylaşım: format seç → varyasyon + tempo taraması → render → kalite kontrolü → yayın → geçmiş.

  python3 -m auto.daily                      # sıradaki format, sırlar varsa yayınlar
  python3 -m auto.daily --dry-run            # yayınlamadan üret + kontrol et
  python3 -m auto.daily --format galton --dry-run

Format seçimi: en uzun süredir paylaşılmayan format (12 günlük döngü; aynı format üst üste gelmez).
Aynı format için kullanılmış tohum tekrar seçilmez → her gün yeni bir video.
Çıkış kodu 0 değilse GitHub Actions e-posta ile bildirir (başarısız üretim, kalite veya yayın).
"""
import argparse
import datetime as dt
import json
import multiprocessing as mp
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from auto import captions, publish, qa  # noqa: E402
from auto import formats as F  # noqa: E402

HISTORY = os.environ.get("AUTO_HISTORY", os.path.join(ROOT, "auto", "history.jsonl"))   # testte başka dosya
ORDER = ["multiply", "rings", "pendulum", "colorwar", "laser", "breakout", "heptagon", "galton", "survivor",
         "grow", "marble_race", "domino"]


def load_history():
    if not os.path.exists(HISTORY):
        return []
    with open(HISTORY) as fh:
        return [json.loads(l) for l in fh if l.strip()]


def append_history(rec):
    with open(HISTORY, "a") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def pick_format(hist):
    """Önizlemeler (dry_run) sırayı ilerletmez; sadece gerçekten yayınlananlar sayılır."""
    last = {}
    for i, r in enumerate(hist):
        if r.get("status") in ("published", "partial"):
            last[r["format"]] = i
    return min(ORDER, key=lambda f: (last.get(f, -1), ORDER.index(f)))


def _check(arg):
    fmt, seed = arg
    try:
        return seed, F.check(fmt, seed)
    except Exception as e:                       # tek tohumun hatası taramayı durdurmasın
        print(f"  tohum {seed} hata: {e!r}", flush=True)
        return seed, None


def find_seeds(fmt, used, today, batches=30):
    """Tempo kontrolünden geçen tohumları puana göre sıralı döndürür (iyi olan önce)."""
    rng = random.Random(today.toordinal() * 1009 + ORDER.index(fmt))
    if F.FORMATS[fmt]["check"] is None:
        return [s for s in rng.sample(range(1, 10 ** 6), 5) if s not in used]
    n = max(2, os.cpu_count() or 2)
    ctx = mp.get_context("fork")
    good = []
    with ctx.Pool(n) as pool:
        for b in range(batches):
            cand = [s for s in rng.sample(range(1, 10 ** 6), n * 3) if s not in used]
            t0 = time.time()
            res = pool.map(_check, [(fmt, s) for s in cand])
            ok = sorted((sc, s) for s, sc in res if sc is not None)
            print(f"  tarama {b + 1}: {len(ok)}/{len(cand)} uygun ({time.time() - t0:.0f} sn)", flush=True)
            good += ok
            if len(good) >= 2:
                break
    return [s for _, s in sorted(good)]


def run(fmt=None, dry_run=False, out_root=None):
    today = dt.date.today()
    hist = load_history()
    fmt = fmt or pick_format(hist)
    used = {r["seed"] for r in hist if r["format"] == fmt and "seed" in r}
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M")
    out_root = out_root or os.path.join(ROOT, "out", "daily")
    print(f"[{stamp}] format={fmt} kullanılmış tohum={len(used)}", flush=True)

    rec = {"date": today.isoformat(), "stamp": stamp, "format": fmt}
    seeds = find_seeds(fmt, used, today)
    result = None
    for seed in seeds[:3]:
        out = os.path.join(out_root, f"{stamp}_{fmt}_{seed}")
        t0 = time.time()
        r = F.make(fmt, seed, out)
        m = qa.check(r["final"], r["complete"])
        print(f"  tohum {seed}: render {time.time() - t0:.0f} sn, kalite {'TAMAM' if m['ok'] else m['problems']}",
              flush=True)
        if m["ok"]:
            result = (seed, r, m, out)
            break
        rec.setdefault("rejected", []).append({"seed": seed, "problems": m["problems"]})
    if result is None:
        rec["status"] = "failed_quality" if seeds else "failed_no_seed"
        append_history(rec)
        print("UYGUN VİDEO ÜRETİLEMEDİ", flush=True)
        return 1

    seed, r, m, out = result
    cap = captions.build(fmt, r["params"], seed)
    rec.update({"seed": seed, "params": r["params"], "info": r["info"], "qa": m, "caption": cap,
                "video": os.path.relpath(r["final"], ROOT)})
    with open(os.path.join(out, "post.json"), "w") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    print(f"  açıklama: {cap['caption']}\n  YouTube: {cap['youtube_title']}", flush=True)

    if dry_run or not publish.configured():
        rec["status"] = "dry_run"
        append_history(rec)
        print("DRY-RUN: yayınlanmadı" + ("" if dry_run else " (UPLOAD_POST_API_KEY / UPLOAD_POST_USER yok)"), flush=True)
        return 0

    request_id = f"ps-{stamp}-{fmt}-{seed}"
    rec["request_id"] = request_id
    try:
        rec["upload"] = publish.upload(r["final"], cap, request_id)
        rec["result"] = publish.wait(request_id)
    except Exception as e:
        rec["status"] = "failed_publish"
        rec["error"] = repr(e)
        append_history(rec)
        print(f"YAYIN HATASI: {e!r}", flush=True)
        return 1
    res = rec["result"].get("results") or []
    oks = {x.get("platform"): bool(x.get("success")) for x in res}
    rec["platforms"] = oks
    rec["status"] = "published" if oks and all(oks.values()) and len(oks) == len(publish.PLATFORMS) else "partial"
    append_history(rec)
    print(f"YAYIN: {rec['status']} {oks}", flush=True)
    return 0 if rec["status"] == "published" else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", choices=list(F.FORMATS))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    sys.exit(run(a.format, a.dry_run, a.out))
