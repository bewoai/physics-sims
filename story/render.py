"""Bölüm render'ı (Yol 2): bölüm JSON'u + anlatım (narrate çıktısı) → 1080×1920 30 fps video + miks + kontrol şeridi.

  python story/render.py story/episodes/eiffel.json out/story/eiffel_en.json en out/story/eiffel_en_code
"""
import json
import os
import sys

import skia

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from lib import canvas, encode  # noqa: E402
from story import draw as D  # noqa: E402
from story import music, style  # noqa: E402
from story.scenes import SCENES  # noqa: E402
from story.style import CREAM, INK, MUSTARD, SANS_K, typeface  # noqa: E402

FPS = 30
XF = 0.35          # sahne geçişi (çapraz)
LEAD = 0.15        # görüntü anlatımdan biraz önce değişsin
TAIL = 0.9
BADGE = {"en": "BEHIND THE LANDMARK", "tr": "MEKÂNIN HİKÂYESİ"}


def timeline(ep, narr):
    S = [s["s"] for s in narr["sentences"]]
    total = narr["duration"] + TAIL
    sc = []
    for i, s in enumerate(ep["scenes"]):
        start = 0.0 if i == 0 else max(0.0, S[s["from"]] - LEAD)
        sc.append({"kind": s["kind"], "start": start})
    for i, s in enumerate(sc):
        s["end"] = sc[i + 1]["start"] if i + 1 < len(sc) else total
    return sc, S, total


def chunks(words, max_words=4, gap=0.35):
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        brk = (len(cur) >= max_words or w["w"][-1] in ".,!?:;"
               or (nxt is not None and nxt["s"] - w["e"] > gap))
        if brk or nxt is None:
            out.append(cur)
            cur = []
    for i, ch in enumerate(out):
        ch_end = out[i + 1][0]["s"] if i + 1 < len(out) else ch[-1]["e"] + 0.6
        out[i] = {"words": ch, "s": ch[0]["s"] - 0.05, "e": ch_end}
    return out


def draw_caption(c, ch, t, y=1440, size=70):
    font = skia.Font(typeface(SANS_K), size)
    toks = [w["w"] for w in ch["words"]]
    widths = [font.measureText(x) for x in toks]
    space = font.measureText(" ")
    lines = [list(range(len(toks)))]
    if sum(widths) + space * (len(toks) - 1) > 940 and len(toks) > 1:
        half = len(toks) // 2
        lines = [list(range(half)), list(range(half, len(toks)))]
    stroke = skia.Paint(AntiAlias=True, Color4f=style.C(INK), Style=skia.Paint.kStroke_Style, StrokeWidth=12,
                        StrokeJoin=skia.Paint.kRound_Join)
    for li, idxs in enumerate(lines):
        lw = sum(widths[i] for i in idxs) + space * (len(idxs) - 1)
        x = D.W / 2 - lw / 2
        yy = y + (li - (len(lines) - 1) / 2) * size * 1.15
        for i in idxs:
            w = ch["words"][i]
            if w["s"] <= t:
                col, a = (MUSTARD, 1.0) if t < (ch["words"][i + 1]["s"] if i + 1 < len(toks) else ch["e"]) else (CREAM, 1.0)
            else:
                col, a = CREAM, 0.5
            pop = 1.0 + 0.08 * max(0.0, 1 - (t - w["s"]) / 0.12) if w["s"] <= t else 1.0
            c.save()
            c.translate(x + widths[i] / 2, yy)
            c.scale(pop, pop)
            stroke.setAlphaf(a)
            c.drawString(toks[i], -widths[i] / 2, 0, font, stroke)
            c.drawString(toks[i], -widths[i] / 2, 0, font, style.paint(col, alpha=a))
            c.restore()
            x += widths[i] + space


def render(ep_path, narr_path, lang, out_dir):
    ep = json.load(open(ep_path))
    narr = json.load(open(narr_path))
    sc, S, total = timeline(ep, narr)
    caps = chunks(narr["words"])
    os.makedirs(out_dir, exist_ok=True)
    vid = os.path.join(out_dir, "video.mp4")
    rd = canvas.Renderer(vid, bg=(0.07, 0.08, 0.12), glow=0.18, glow_sigma=10, fps=FPS)
    alt = skia.Surface(D.W, D.H)
    s1 = S[1]
    n = int(total * FPS)
    for fi in range(n):
        t = fi / FPS
        i = next(k for k, s in enumerate(sc) if s["start"] <= t < s["end"] or k == len(sc) - 1)
        cur = sc[i]

        def scene(c, s):
            c.save()
            SCENES[s["kind"]](c, t - s["start"], s["end"] - s["start"],
                              {"t": t, "lang": lang, "S": S, "start": s["start"]})
            c.restore()

        def draw(c):
            scene(c, cur)
            if i + 1 < len(sc) and t > cur["end"] - XF:            # sonraki sahneye çapraz geçiş
                a = (t - (cur["end"] - XF)) / XF
                ac = alt.getCanvas()
                ac.clear(skia.Color4f(0, 0, 0, 1))
                scene(ac, sc[i + 1])
                c.drawImage(alt.makeImageSnapshot(), 0, 0, skia.SamplingOptions(), skia.Paint(Alphaf=D.ease(a)))

        def overlay(c):
            style.grain(c, D.W, D.H, fi)
            style.vignette(c, D.W, D.H, 0.4)
            # perde jeneriği: 1. cümleden hemen önce kapanır, sonra açılır
            if s1 - 0.4 <= t < s1 - 0.08:
                kk = D.ease((t - (s1 - 0.4)) / 0.32)
                D.curtains(c, 1.0 - kk, 0.0, dur=1.0, title=BADGE[lang])
            elif s1 - 0.08 <= t < s1 + 0.9:
                D.curtains(c, t, s1 - 0.08, dur=0.95, title=BADGE[lang])
            D.badge(c, BADGE[lang])
            for ch in caps:
                if ch["s"] <= t < ch["e"]:
                    draw_caption(c, ch, t)
                    break

        rd.frame(draw, overlay)
    rd.close()

    # ses: anlatım + müzik yatağı + efektler
    sfx = [(sc[0]["start"] + 1.25, "thud", 34, 1.0), (sc[0]["start"] + 1.25, "tick", 60, 0.8),
           (s1 - 0.4, "whoosh", 60, 0.8), (s1 - 0.05, "whoosh", 60, 0.9)]
    for s in sc[1:]:
        sfx.append((s["start"] - 0.1, "whoosh", 60, 0.35))
        if s["kind"] in ("radio", "war"):
            for k in range(3):
                sfx.append((s["start"] + 0.5 + k * 1.9, "beepseq", 0, 0.12))
        if s["kind"] == "renewal":
            sfx += [(s["start"] + 0.5, "tick", 60, 0.9), (s["start"] + 0.9, "thud", 34, 1.0)]
        if s["kind"] == "newspaper":
            sfx.append((s["start"] + 0.1, "thud", 46, 0.6))
        if s["kind"] == "today":
            sfx += [(s["start"] + 0.3 + 0.12 * q, "bell", m, 0.18) for q, m in enumerate((74, 78, 81, 86))]
    wav = music.mix(narr["wav"], total, sfx, os.path.join(out_dir, "mix.wav"))
    final = encode.mux(vid, wav, os.path.join(out_dir, "final.mp4"))
    encode.contact_sheet(final, os.path.join(out_dir, "sheet.jpg"), every=total / 16, cols=8, rows=2)
    return final, total


if __name__ == "__main__":
    import time
    t0 = time.time()
    f, total = render(*sys.argv[1:5])
    print("çıktı", f, f"{total:.1f} sn", encode.loudness(f), f"render {time.time() - t0:.0f} sn", flush=True)
