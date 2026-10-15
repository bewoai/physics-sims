"""Çakışma denetimi (kullanıcı: "üst üste gelen semboller, simgeler, yazılar var"). Videoyu 0,2 sn adımla örnekler,
her karede çizilen yazı (başlık, altyazı, etiket) ve nesne (simge, dekor, Mango) kutularını toplar, kurallara göre
çakışanları raporlar. Geçişte giden sahnenin öğeleri ilk yarıda, gelenin öğeleri ikinci yarıda sayılır.

  python3 story/overlap_qa.py kapi tr        # → çakışma listesi; 0 satır = temiz

Kurallar (kesişim ≥ 6 px her iki eksende):
  yazı × yazı · yazı × simge · yazı × Mango · başlık × dekor · simge × simge · simge × dekor (aynı nesne değilse)
Bilinçli üst üste binmeler (ör. anahtar balonun içinde) kayda zaten girmiyor.
"""
import json
import os
import sys

import skia

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from story import neden as N  # noqa: E402
from story import siluet as SL  # noqa: E402
from story.render import XF, chunks, timeline  # noqa: E402

MIN = 6.0
ALLOW = {("balon", "saat"), ("bank", "telefon"), ("balon", "dolap"), ("balon", "kapı")}   # bilinçli: saat balonda,
# telefon bankta, düşünce çekmeceye uçar, balon kapıda patlar (bölümün esprisi)
RULES = {("text", "text"), ("text", "icon"), ("text", "cat"), ("title", "prop"), ("title", "icon"), ("title", "cat"),
         ("title", "text"), ("icon", "icon"), ("icon", "prop"), ("caption", "icon"), ("caption", "cat"),
         ("caption", "text"), ("caption", "prop")}


def inter(a, b):
    x0, y0 = max(a.left(), b.left()), max(a.top(), b.top())
    x1, y1 = min(a.right(), b.right()), min(a.bottom(), b.bottom())
    return (x1 - x0, y1 - y0) if x1 - x0 >= MIN and y1 - y0 >= MIN else None


def frame_boxes(ep, narr, lang, sc, S, caps, t, surf):
    i = next(k for k, s in enumerate(sc) if s["start"] <= t < s["end"] or k == len(sc) - 1)
    boxes = []
    c = surf.getCanvas()

    def scene(s, keep):
        N.BOXES.clear()
        n0 = len(SL._text_boxes)
        ctx = {"t": t, "lang": lang, "S": S, "start": s["start"], "place": {}, "ep": ep, "cta": ep.get("cta_from"), "texts": [],
               "strike": None}
        c.save()
        N.SCENES[s["kind"]](c, t - s["start"], s["end"] - s["start"], ctx)
        c.restore()
        N.draw_texts(c, ctx["texts"], None)
        if keep:
            boxes.extend((k, n, r) for k, n, r in N.BOXES)
            boxes.extend(("text", f"etiket:{s['kind']}", skia.Rect(*b)) for b in SL._text_boxes[n0:])
    SL._text_boxes.clear()
    a = 0.0
    if i + 1 < len(sc) and t > sc[i]["end"] - XF:
        a = (t - (sc[i]["end"] - XF)) / XF
    scene(sc[i], a < 0.5)
    if a > 0:
        scene(sc[i + 1], a >= 0.5)
    n0 = len(SL._text_boxes)
    N.overlay(c, t, 0, {"ep": ep, "lang": lang, "s1": S[1], "caps": caps})
    title_n = len(N._title_lines(ep, lang))
    for j, b in enumerate(SL._text_boxes[n0:]):
        boxes.append(("title" if j < title_n else "caption", "başlık" if j < title_n else "altyazı", skia.Rect(*b)))
    return boxes


def check(ep_id, lang, step=0.2):
    ep = json.load(open(f"story/episodes/{ep_id}.json"))
    narr = json.load(open(f"out/story/{ep_id}_{lang}.json"))
    sc, S, total = timeline(ep, narr, N.TAIL)
    caps = chunks(narr["words"])
    surf = skia.Surface(1080, 1920)
    hits = {}
    t = 0.0
    while t < total:
        bx = frame_boxes(ep, narr, lang, sc, S, caps, t, surf)
        for p in range(len(bx)):
            for q in range(p + 1, len(bx)):
                (k1, n1, r1), (k2, n2, r2) = bx[p], bx[q]
                if (k1, k2) not in RULES and (k2, k1) not in RULES:
                    continue
                if n1 == n2 or (n1, n2) in ALLOW or (n2, n1) in ALLOW:
                    continue
                d = inter(r1, r2)
                if d:
                    key = tuple(sorted((n1, n2)))
                    h = hits.setdefault(key, [t, t, 0])
                    h[1] = t
                    h[2] = max(h[2], d[0] * d[1])
        t += step
    return hits


if __name__ == "__main__":
    ep_id, lang = sys.argv[1], sys.argv[2]
    hits = check(ep_id, lang)
    for (a, b), (t0, t1, area) in sorted(hits.items(), key=lambda kv: kv[1][0]):
        print(f"{t0:5.1f}–{t1:5.1f} sn  {a}  ×  {b}  (en büyük kesişim {area:.0f} px²)")
    print(f"{ep_id} {lang}: {len(hits)} çakışma")
