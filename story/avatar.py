"""Profil fotoğrafı (1080×1080 PNG): dişli kenarlı pul + kubbeli simge yapı silueti. Yazı yok (dairede ~110 px'e
küçülüyor, okunmaz). Platformlar daireye kırpar: her şey merkezdeki 0,87 R içinde kalır.

  python3 story/avatar.py out/story/avatar
"""
import os
import sys

import skia

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from story.style import CREAM, INK, MUSTARD, NIGHT, TEAL, TEAL_D, TERRA, linear, paint  # noqa: E402

S = 1080
SKY = {"en": (MUSTARD, TERRA), "tr": ("#9CC7C2", TEAL)}       # iki hesap telefonda karışmasın: sıcak / serin


def dome(c, x, b, s, color, gap):
    """Genel kubbeli yapı (Panthéon / Ayasofya / Capitol karışımı): tek bir yere ait değil, seri her yeri anlatıyor."""
    p = paint(color)
    c.drawRect(skia.Rect(x - 112 * s, b - 250 * s, x + 112 * s, b - 140 * s), p)                  # kasnak
    d = skia.Path()
    d.addArc(skia.Rect(x - 118 * s, b - 365 * s, x + 118 * s, b - 135 * s), 180, 180)
    c.drawPath(d, p)                                                                              # kubbe
    c.drawRect(skia.Rect(x - 16 * s, b - 405 * s, x + 16 * s, b - 355 * s), p)                    # fener
    c.drawCircle(x, b - 410 * s, 13 * s, p)
    ped = skia.Path()
    ped.moveTo(x - 215 * s, b - 120 * s); ped.lineTo(x, b - 190 * s); ped.lineTo(x + 215 * s, b - 120 * s); ped.close()
    c.drawPath(ped, p)                                                                            # alınlık
    c.drawRect(skia.Rect(x - 195 * s, b - 122 * s, x + 195 * s, b), p)                            # gövde
    for i in range(-3, 4):                                                                        # sütun araları
        c.drawRect(skia.Rect(x + (i * 52 - 9) * s, b - 100 * s, x + (i * 52 + 9) * s, b - 14 * s), paint(gap))


def avatar(lang, out):
    surf = skia.Surface(S, S)
    c = surf.getCanvas()
    c.clear(skia.Color4f(0, 0, 0, 1))
    c.drawRect(skia.Rect(0, 0, S, S), paint(NIGHT))
    w, h = 600, 720
    x0, y0 = (S - w) / 2, (S - h) / 2
    c.drawRect(skia.Rect(x0 + 14, y0 + 20, x0 + w + 14, y0 + h + 20), paint("#000000", alpha=0.35))   # gölge
    c.drawRect(skia.Rect(x0, y0, x0 + w, y0 + h), paint(CREAM))
    r, gap = 15, 40                                                                  # pul dişleri
    for i in range(int(w / gap) + 1):
        for yy in (y0, y0 + h):
            c.drawCircle(x0 + i * w / int(w / gap), yy, r, paint(NIGHT))
    for i in range(int(h / gap) + 1):
        for xx in (x0, x0 + w):
            c.drawCircle(xx, y0 + i * h / int(h / gap), r, paint(NIGHT))
    m = 52
    ix0, iy0, ix1, iy1 = x0 + m, y0 + m, x0 + w - m, y0 + h - m
    top, bot = SKY[lang]
    c.save()
    c.clipRect(skia.Rect(ix0, iy0, ix1, iy1))
    c.drawRect(skia.Rect(ix0, iy0, ix1, iy1), linear(0, iy0, 0, iy1, [top, bot]))
    c.drawCircle(S / 2 + 140, iy0 + 150, 62, paint(CREAM, alpha=0.9))                # güneş
    base = iy1 - 60
    c.drawRect(skia.Rect(ix0, base, ix1, iy1), paint(INK))
    dome(c, S / 2, base + 2, 1.0, INK, bot)
    c.restore()
    c.drawRect(skia.Rect(ix0, iy0, ix1, iy1), paint(TEAL_D if lang == "tr" else INK, stroke=6, alpha=0.6))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    surf.makeImageSnapshot().save(out, skia.kPNG)
    return out


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "out/story/avatar"
    for lang in ("en", "tr"):
        print(avatar(lang, os.path.join(d, f"avatar_{lang}.png")))
