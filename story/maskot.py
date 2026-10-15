"""Seri maskotu adayları (kullanıcı: "farklı, karakteristik, kendini hatırlatan bir çizgi film karakteri").
Hepsi kodla çizilir, Siluet Sinema ışığına uyar ama her birinin tek bir imza rengi/özelliği var.

  soru(c, x, y, s, t, mood, k_aha)   "?" gövdeli yaratık; aha anında "!"e dönüşür (k_aha 0→1)
  ampul(c, x, y, s, t, mood, glow)   ampul kafalı; unutunca söner, anlayınca yanar (glow 0..1)
  tekgoz(c, x, y, s, t, mood)        tek kocaman gözlü yuvarlak yaratık, ucu parlayan anten

mood: calm | confused | aha | angry | sleepy
"""
import math

import skia

from story.style import C, paint

PLUS = skia.BlendMode.kPlus
WHITE, PUPIL = "#FFFFFF", "#0B0E18"


def _blur(sigma, col, a, plus=True):
    p = skia.Paint(AntiAlias=True, Color4f=C(col, a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma))
    if plus:
        p.setBlendMode(PLUS)
    return p


def _eye(c, x, y, r, look=(0.3, 0.0), kind="open", lid_col="#000000"):
    if kind == "closed":
        p = skia.Path()
        p.addArc(skia.Rect(x - r, y - r * 0.4, x + r, y + r * 0.8), 20, 140)
        c.drawPath(p, paint(WHITE, stroke=r * 0.28))
        return
    if kind == "happy":
        p = skia.Path()
        p.addArc(skia.Rect(x - r, y - r * 0.3, x + r, y + r * 1.1), 200, 140)
        c.drawPath(p, paint(WHITE, stroke=r * 0.3))
        return
    c.drawOval(skia.Rect(x - r, y - r * 1.25, x + r, y + r * 1.25), paint(WHITE))
    pr = r * 0.55
    px, py = x + look[0] * (r - pr - 2), y + look[1] * (r * 1.25 - pr - 2)
    c.drawCircle(px, py, pr, paint(PUPIL))
    c.drawCircle(px - pr * 0.35, py - pr * 0.35, pr * 0.3, paint(WHITE))
    if kind == "sleepy":
        c.drawRect(skia.Rect(x - r - 2, y - r * 1.3, x + r + 2, y - r * 0.1), paint(lid_col))
    if kind == "angry":
        p = skia.Path()
        p.moveTo(x - r - 3, y - r * 1.3)
        p.lineTo(x + r + 3, y - r * 1.3)
        p.lineTo(x + r + 3, y - r * 0.3)
        p.close()
        c.drawPath(p, paint(lid_col))


def _mouth(c, x, y, r, kind):
    if kind == "smile":
        p = skia.Path()
        p.addArc(skia.Rect(x - r, y - r * 0.7, x + r, y + r * 0.5), 20, 140)
        c.drawPath(p, paint(WHITE, stroke=r * 0.26))
    elif kind == "o":
        c.drawOval(skia.Rect(x - r * 0.45, y - r * 0.3, x + r * 0.45, y + r * 0.7), paint(WHITE))
    elif kind == "grin":
        p = skia.Path()
        p.addArc(skia.Rect(x - r, y - r * 0.6, x + r, y + r * 0.9), 0, 180)
        p.close()
        c.drawPath(p, paint(WHITE))
    elif kind == "frown":
        p = skia.Path()
        p.addArc(skia.Rect(x - r, y, x + r, y + r), 200, 140)
        c.drawPath(p, paint(WHITE, stroke=r * 0.26))
    else:
        c.drawLine(x - r * 0.7, y + r * 0.2, x + r * 0.7, y + r * 0.2, paint(WHITE, stroke=r * 0.24))


FACE = {"calm": ("open", "smile"), "confused": ("open", "flat"), "aha": ("open", "grin"), "angry": ("angry", "frown"),
        "sleepy": ("sleepy", "flat"), "wow": ("open", "o"), "happy": ("happy", "grin")}


# ---------------------------------------------------------------- 1) Soru: "?" gövdeli, "!"e dönüşen
SORU_COL, SORU_GLOW = "#FF6B4A", "#FFB08A"                      # imza rengi: mercan turuncu


def soru(c, x, y, s, t, mood="calm", k_aha=0.0, col=SORU_COL, look=(0.3, 0.0)):
    """x, y: noktanın (ayağın) zemine değdiği yer. k_aha: 0 = "?", 1 = "!" (kanca düzleşir, zıplar)."""
    hop = abs(math.sin(t * 3.2)) * 18 * s if mood in ("calm", "aha", "happy") else 0.0
    bend = 1.0 - k_aha
    c.save()
    c.translate(x, y - hop)
    c.drawCircle(0, -34 * s, 34 * s, paint(col))                       # nokta = ayak/top
    w = 46 * s
    p = skia.Path()                                                    # gövde: "?" kancası → "!" çizgisi
    p.moveTo(0, -110 * s)
    p.lineTo(0, -170 * s)
    p.cubicTo(0, -200 * s, 100 * s * bend, -210 * s, 100 * s * bend, -290 * s - 40 * s * k_aha)
    p.cubicTo(100 * s * bend, -380 * s - 30 * k_aha * s, 0, -400 * s - 20 * k_aha * s,
              -90 * s * bend, -340 * s - 80 * s * k_aha)
    c.drawPath(p, paint(col, stroke=w))
    if k_aha > 0.5:
        c.drawCircle(0, -250 * s, 160 * s, _blur(40 * s, SORU_GLOW, 0.35 * (k_aha - 0.5) * 2))
    ex, ey = 45 * s * bend, -330 * s - 20 * s * k_aha                  # gözler kancanın tepesinde
    ek, mk = FACE.get(mood, FACE["calm"])
    for side in (-1, 1):
        _eye(c, ex + side * 24 * s, ey, 15 * s, look, ek, col)
    _mouth(c, ex + 4 * s, ey + 36 * s, 16 * s, mk)
    for side in (-1, 1):                                               # minik kollar: gövdeden yana, simetrik
        up = -70 if mood in ("aha", "happy") else (35 if mood != "angry" else -10)
        ex2, ey2 = side * 78 * s, -150 * s + up * s
        c.drawLine(side * 20 * s, -165 * s, ex2, ey2, paint(col, stroke=14 * s))
        c.drawCircle(ex2, ey2, 11 * s, paint(col))
    c.restore()


# ---------------------------------------------------------------- 2) Ampul: kafası ampul, anlayınca yanar
AMPUL_BODY, AMPUL_GLOW = "#1A1F33", "#FFD27A"


def ampul(c, x, y, s, t, mood="calm", glow=0.6, look=(0.3, 0.0), body=AMPUL_BODY):
    flick = 1.0 if glow < 0.95 else 0.92 + 0.08 * math.sin(t * 30)
    c.save()
    c.translate(x, y)
    for side in (-1, 1):                                               # bacaklar
        c.drawLine(side * 20 * s, -90 * s, side * 26 * s, -8 * s, paint(body, stroke=18 * s))
        c.drawOval(skia.Rect(side * 26 * s - 18 * s, -18 * s, side * 26 * s + 18 * s, 2 * s), paint(body))
    c.drawRoundRect(skia.Rect(-46 * s, -200 * s, 46 * s, -80 * s), 40 * s, 40 * s, paint(body))
    for side in (-1, 1):
        c.drawLine(side * 42 * s, -178 * s, side * 72 * s, -110 * s, paint(body, stroke=15 * s))
    for i in range(3):                                                 # vida dişleri (boyun)
        c.drawRoundRect(skia.Rect(-34 * s, -228 * s - i * 16 * s, 34 * s, -214 * s - i * 16 * s), 6 * s, 6 * s,
                        paint("#8E96A8" if i % 2 == 0 else "#6C7486"))
    bx, by, br = 0, -340 * s, 100 * s                                  # cam
    bulb = skia.Path()
    bulb.addCircle(bx, by, br)
    neck = skia.Path()
    neck.moveTo(-40 * s, -262 * s)
    neck.cubicTo(-50 * s, -290 * s, -70 * s, -280 * s, -80 * s, by + 40 * s)
    neck.lineTo(80 * s, by + 40 * s)
    neck.cubicTo(70 * s, -280 * s, 50 * s, -290 * s, 40 * s, -262 * s)
    neck.close()
    g = glow * flick
    if g > 0.05:
        c.drawCircle(bx, by, br * 2.4, _blur(60 * s, AMPUL_GLOW, 0.55 * g))
    glass = mix_col("#3A4258", "#FFF2C8", g)
    c.drawPath(neck, paint(glass))
    c.drawPath(bulb, paint(glass))
    c.drawPath(bulb, paint("#FFFFFF", stroke=4 * s, alpha=0.35))
    fil = skia.Path()                                                  # flaman: kaş gibi
    fil.moveTo(-40 * s, by + 60 * s)
    fil.lineTo(-40 * s, by + 10 * s)
    fil.quadTo(0, by - 30 * s * (1 if mood != "angry" else -0.4), 40 * s, by + 10 * s)
    fil.lineTo(40 * s, by + 60 * s)
    c.drawPath(fil, paint("#C9822F" if g > 0.3 else "#6C7486", stroke=5 * s))
    ek, mk = FACE.get(mood, FACE["calm"])
    for side in (-1, 1):
        _eye(c, side * 32 * s, by + 5 * s, 17 * s, look, ek, glass)
    _mouth(c, 0, by + 52 * s, 18 * s, mk)
    c.restore()


def mix_col(a, b, k):
    ca, cb = C(a), C(b)
    return skia.Color4f(ca.fR + (cb.fR - ca.fR) * k, ca.fG + (cb.fG - ca.fG) * k, ca.fB + (cb.fB - ca.fB) * k, 1)


# ---------------------------------------------------------------- 3) Tek göz: yuvarlak gövde, tek dev göz, anten
TEKGOZ_COL, TEKGOZ_TIP = "#3FB6A8", "#FFE36A"                    # imza rengi: turkuaz


def tekgoz(c, x, y, s, t, mood="calm", look=(0.3, 0.0), col=TEKGOZ_COL):
    squash = 1 + 0.04 * math.sin(t * 4)
    c.save()
    c.translate(x, y)
    for side in (-1, 1):
        c.drawLine(side * 40 * s, -60 * s, side * 46 * s, -10 * s, paint(col, stroke=20 * s))
        c.drawOval(skia.Rect(side * 46 * s - 22 * s, -22 * s, side * 46 * s + 22 * s, 2 * s), paint(col))
    c.save()
    c.scale(1 / squash, squash)
    c.drawCircle(0, -190 * s, 140 * s, paint(col))
    c.drawCircle(-40 * s, -240 * s, 60 * s, paint("#FFFFFF", alpha=0.10))
    c.restore()
    ant = skia.Path()
    ant.moveTo(0, -325 * s)
    ant.quadTo(30 * s, -380 * s, 10 * s + 8 * s * math.sin(t * 3), -420 * s)
    c.drawPath(ant, paint(col, stroke=10 * s))
    tip_on = 1.0 if mood in ("aha", "happy") else 0.35
    c.drawCircle(10 * s + 8 * s * math.sin(t * 3), -425 * s, 20 * s, paint(TEKGOZ_TIP, alpha=0.4 + 0.6 * tip_on))
    c.drawCircle(10 * s + 8 * s * math.sin(t * 3), -425 * s, 50 * s, _blur(18 * s, TEKGOZ_TIP, 0.5 * tip_on))
    ek, mk = FACE.get(mood, FACE["calm"])
    _eye(c, 0, -215 * s, 56 * s, look, ek, col)
    _mouth(c, 0, -110 * s, 30 * s, mk)
    for side in (-1, 1):
        c.drawLine(side * 130 * s, -170 * s, side * 175 * s, -120 * s + (-80 * s if mood == "aha" else 0),
                   paint(col, stroke=16 * s))
    c.restore()
