"""Profil fotoğrafı (1080×1080 PNG), gravür tarzı: dişli kenarlı pul + kazıma gökyüzü + kubbeli yapı + kırmızı
posta damgası. Yazı yok (dairede ~110 px'e küçülüyor, okunmaz). Platformlar daireye kırpar: her şey merkezdeki 0,87 R içinde kalır.

  python3 story/avatar.py out/story/avatar
"""
import math
import os
import sys

import skia

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from story.style import paint  # noqa: E402

S = 1080
BG = {"en": "#1E2233", "tr": "#C23B22"}       # gravür paleti: mürekkep / damga kırmızısı (iki hesap karışmasın)


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
    from story import gravur as G
    bg = BG[lang]
    surf = skia.Surface(S, S)
    c = surf.getCanvas()
    c.drawRect(skia.Rect(0, 0, S, S), paint(bg))
    w, h = 600, 720
    x0, y0 = (S - w) / 2, (S - h) / 2
    c.drawRect(skia.Rect(x0, y0, x0 + w, y0 + h), paint(G.PAPER))
    r, gap = 15, 40                                                                  # pul dişleri
    for i in range(int(w / gap) + 1):
        for yy in (y0, y0 + h):
            c.drawCircle(x0 + i * w / int(w / gap), yy, r, paint(bg))
    for i in range(int(h / gap) + 1):
        for xx in (x0, x0 + w):
            c.drawCircle(xx, y0 + i * h / int(h / gap), r, paint(bg))
    m = 52
    win = skia.Rect(x0 + m, y0 + m, x0 + w - m, y0 + h - m)
    c.save()
    c.clipRect(win)
    y = win.top() + 4
    while y < win.bottom():                                                          # kazıma gökyüzü
        wd = 6.0 - 5.0 * (y - win.top()) / win.height()
        c.drawLine(0, y, S, y, paint(G.INK, stroke=max(1.5, wd), cap=skia.Paint.kButt_Cap))
        y += 14
    sx, sy = S / 2 + 140, win.top() + 150
    c.drawCircle(sx, sy, 70, paint(G.PAPER))
    c.drawCircle(sx, sy, 70, paint(G.INK, stroke=5))
    base = win.bottom() - 60
    c.drawRect(skia.Rect(win.left(), base, win.right(), win.bottom()), paint(G.INK))
    for a in range(8):                                                               # yapı: kâğıt + kontur
        c.save()
        c.translate(5 * math.cos(a * math.pi / 4), 5 * math.sin(a * math.pi / 4))
        dome(c, S / 2, base + 2, 1.0, G.INK, G.INK)
        c.restore()
    dome(c, S / 2, base + 2, 1.0, G.PAPER, G.INK)
    c.restore()
    c.drawRect(win, paint(G.INK, stroke=6))
    c.save()                                                                         # posta damgası
    c.translate(x0 + w - 20, y0 + 40)
    c.rotate(-12)
    c.drawCircle(0, 0, 120, paint(G.RED, stroke=12, alpha=0.95))
    c.drawCircle(0, 0, 84, paint(G.RED, stroke=5, alpha=0.95))
    c.restore()
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    surf.makeImageSnapshot().save(out, skia.kPNG)
    return out


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "out/story/avatar"
    for lang in ("en", "tr"):
        print(avatar(lang, os.path.join(d, f"avatar_{lang}.png")))
