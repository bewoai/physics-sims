"""Profil fotoğrafı (1080×1080 PNG), Siluet Sinema dili: ışık kaynağının önünde kubbeli yapı silueti. Yazı yok (dairede ~110 px'e küçülüyor, okunmaz). Platformlar daireye kırpar: her şey merkezdeki 0,87 R içinde kalır.

  python3 story/avatar.py out/story/avatar
"""
import math
import os
import sys

import skia

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from story.style import paint  # noqa: E402

S = 1080
LIGHT = {"en": "night", "tr": "dusk"}        # iki hesap telefonda karışmasın: gece mavisi / gün batımı


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
    """Siluet Sinema: ışık kaynağının önünde kubbeli yapı silueti, huzmeler, sis. Kubbe genel (tek bir yere ait değil)."""
    from story import siluet as SL
    from story.style import C, linear, radial
    Lt = SL.LIGHTS[LIGHT[lang]]
    surf = skia.Surface(S, S)
    c = surf.getCanvas()
    c.drawRect(skia.Rect(0, 0, S, S), linear(0, 0, 0, S, Lt["sky"], [0.0, 0.4, 0.75, 1.0]))
    mx, my, r = S / 2, S * 0.47, 250
    c.drawCircle(mx, my, 900, radial(mx, my, 900, [C(Lt["glow"], 0.5), C(Lt["glow"], 0.0)]))
    rp = SL.blurp(14, Lt["glow"], 0.10, SL.PLUS)
    for k in range(18):                                                              # huzmeler
        a0 = k * 2 * math.pi / 18 + 0.1
        p = skia.Path()
        p.moveTo(mx, my)
        p.lineTo(mx + 900 * math.cos(a0 - 0.04), my + 900 * math.sin(a0 - 0.04))
        p.lineTo(mx + 900 * math.cos(a0 + 0.04), my + 900 * math.sin(a0 + 0.04))
        p.close()
        c.drawPath(p, rp)
    if Lt["src"] == "moon":
        c.drawCircle(mx, my, r, radial(mx - 60, my - 70, r * 1.3, ["#FBFCF6", "#E3EEEA", "#C9DCDA"], [0, 0.6, 1]))
    else:
        c.drawCircle(mx, my, r * 1.2, SL.blurp(60, Lt["glow"], 0.8))
        c.drawCircle(mx, my, r, radial(mx, my, r, ["#FFFDF4", Lt["glow"]], [0.55, 1.0]))
    base = S * 0.80
    fog = Lt["fog"]
    c.drawRect(skia.Rect(0, base - 180, S, base + 40), linear(0, base - 180, 0, base + 40, [C(fog, 0.0), C(fog, 0.5)]))
    dome(c, S / 2, base, 1.25, Lt["fg"], Lt["fg"])
    c.drawRect(skia.Rect(0, base - 2, S, S), paint(Lt["fg"]))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    surf.makeImageSnapshot().save(out, skia.kPNG)
    return out


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "out/story/avatar"
    for lang in ("en", "tr"):
        print(avatar(lang, os.path.join(d, f"avatar_{lang}.png")))
