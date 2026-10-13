"""Tasarım dili denemeleri: aynı an (Eyfel kancası: gece Paris + "SON TARİH 1909" damgası + altyazı) dört özgün
tarzda. Seçilen tarz sonra draw/scenes'e taşınacak. Piksel sanatı bilerek yok (rakip @bit_wonder'ın tarzı).

  python3 story/looks.py out/story/looks
"""
import math
import os
import random
import sys

import numpy as np
import skia

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from story import draw as D  # noqa: E402
from story import style  # noqa: E402
from story.style import C, paint, linear, typeface  # noqa: E402

W, H = D.W, D.H
BADGE = "KARTPOSTALIN ARKASI"
STAMP = [("SON TARİH", 70), ("1909", 120)]
WORDS, CUR = ["Eyfel", "Kulesi'nin", "bir"], 1
HATCH = 9          # gravür çizgi aralığı (px)
CELL = 11.0        # risograf yarım ton hücresi (px)


# ---------------------------------------------------------------- yardımcılar
def font(face, size):
    f = skia.Font(typeface(face), size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def say(c, s, x, y, face, size, color, align="center", spacing=0.0, alpha=1.0, stroke=None):
    f = font(face, size)
    w = f.measureText(s) + spacing * max(0, len(s) - 1)
    x0 = x - w / 2 if align == "center" else (x - w if align == "right" else x)
    for pnt in ([stroke] if stroke else []) + [paint(color, alpha=alpha)]:
        xx = x0
        if spacing:
            for ch in s:
                c.drawString(ch, xx, y, f, pnt)
                xx += f.measureText(ch) + spacing
        else:
            c.drawString(s, xx, y, f, pnt)
    return w


def tr_upper(s):
    return s.replace("i", "İ").replace("ı", "I").upper()


def caption(c, face, size, fill, hi, stroke_col, stroke_w, y=1440, upper=False):
    words = [tr_upper(w) if upper else w for w in WORDS]
    f = font(face, size)
    sp = f.measureText(" ")
    ws = [f.measureText(w) for w in words]
    x = W / 2 - (sum(ws) + sp * (len(ws) - 1)) / 2
    st = skia.Paint(AntiAlias=True, Color4f=C(stroke_col), Style=skia.Paint.kStroke_Style, StrokeWidth=stroke_w,
                    StrokeJoin=skia.Paint.kRound_Join)
    for i, (w, wd) in enumerate(zip(words, ws)):
        if stroke_w:
            c.drawString(w, x, y, f, st)
        c.drawString(w, x, y, f, paint(hi if i == CUR else fill))
        x += wd + sp


def fill_pattern(c, shape, pattern):
    """shape'in kapladığı alana pattern çizer (shape rengi önemsiz)."""
    c.saveLayer(None, None)
    shape(c)
    c.saveLayer(None, skia.Paint(BlendMode=skia.BlendMode.kSrcIn))
    pattern(c)
    c.restore()
    c.restore()


def shadowed(c, draw, dy=6, sigma=12, alpha=0.55):
    sh = skia.ImageFilters.DropShadow(0, dy, sigma, sigma, skia.Color4f(0, 0, 0, alpha).toColor())
    c.saveLayer(None, skia.Paint(ImageFilter=sh))
    draw(c)
    c.restore()


def star4(c, x, y, r, p):
    s = skia.Path()
    s.moveTo(x, y - r)
    for k in range(1, 8):
        a = k * math.pi / 4
        rr = r if k % 2 == 0 else r * 0.28
        s.lineTo(x + rr * math.sin(a), y - rr * math.cos(a))
    s.close()
    c.drawPath(s, p)


def star5(c, x, y, r, p):
    s = skia.Path()
    for k in range(10):
        a = k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        (s.moveTo if k == 0 else s.lineTo)(x + rr * math.sin(a), y - rr * math.cos(a))
    s.close()
    c.drawPath(s, p)


def surface_png(draw, out):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(skia.Color4f(0, 0, 0, 1))
    draw(c)
    surf.makeImageSnapshot().save(out, skia.kPNG)
    return out


# ---------------------------------------------------------------- 1) Pul gravürü
def gravur(c):
    PAPER, INK, RED = "#EEE4CC", "#1E2233", "#C23B22"
    c.drawRect(skia.Rect(0, 0, W, H), paint(PAPER))
    win = skia.Rect(44, 210, W - 44, H - 44)
    c.save()
    c.clipRect(win)
    mx, my, mr = 820, 430, 58
    c.save()                                                     # gök: kalınlığı azalan yatay kazıma çizgileri
    hole = skia.Path()
    hole.addCircle(mx, my, mr + 14)
    c.clipPath(hole, skia.ClipOp.kDifference, True)
    y = 214
    while y < 1560:
        wdt = float(np.interp(y, [210, 1350], [4.6, 0.7])) * HATCH / 9
        c.drawLine(0, y, W, y, paint(INK, stroke=wdt, cap=skia.Paint.kButt_Cap))
        y += HATCH
    c.restore()
    for r in (mr + 26, mr + 40, mr + 56):
        c.drawCircle(mx, my, r, paint(INK, stroke=1.2, alpha=0.7))
    c.drawCircle(mx, my, mr, paint(INK, stroke=2.5))
    cres = skia.Path()
    cres.addCircle(mx + 22, my - 8, mr * 0.9)
    c.save()
    c.clipPath(cres, skia.ClipOp.kDifference, True)
    mp = skia.Path()
    mp.addCircle(mx, my, mr)
    c.clipPath(mp, doAntiAlias=True)
    for k in range(-80, 80, 7):
        c.drawLine(mx - 80, my + k, mx + 80, my + k - 40, paint(INK, stroke=1.6))
    c.restore()
    rng = random.Random(3)
    for _ in range(46):
        x, yy = rng.uniform(60, W - 60), rng.uniform(240, 900)
        if math.hypot(x - mx, yy - my) < mr + 70:
            continue
        star4(c, x, yy, rng.uniform(6, 13), paint(PAPER))
    fill_pattern(c, lambda cc: D.skyline(cc, 1500, 11, INK, INK, None, scale=0.8),
                 lambda cc: (cc.drawRect(skia.Rect(0, 0, W, H), paint(PAPER)),
                             [cc.drawLine(x, 900, x, 1700, paint(INK, stroke=2.4 * HATCH / 9)) for x in range(0, W, HATCH - 2)]))
    D.tower(c, 540, 1520, 1050, color=PAPER)
    c.save()                                                     # kule gölgesi: sağ yarıya dikey tarama
    c.clipPath(D.tower_path(540, 1520, 1050), doAntiAlias=True)
    c.clipRect(skia.Rect(540, 0, W, H))
    for x in range(540, 800, HATCH - 3):
        c.drawLine(x, 400, x, 1600, paint(INK, stroke=1.5, alpha=0.8))
    c.restore()
    D.skyline(c, 1660, 12, INK, INK, PAPER, lit=0.0)
    c.drawRect(skia.Rect(0, 1660, W, H), paint(INK))
    c.save()                                                     # damga: aşınmış kauçuk mürekkep
    c.saveLayer(None, None)
    D.stamp(c, 540, 860, STAMP, 0.0, 1.0, color=RED)
    rng = random.Random(8)
    er = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kDstOut)
    for _ in range(900):
        c.drawCircle(rng.uniform(220, 860), rng.uniform(700, 1020), rng.uniform(0.8, 3.2), er)
    c.restore()
    c.restore()
    caption(c, "PlayfairDisplay-900.ttf", 78, PAPER, "#F0C36A", INK, 14)
    c.restore()
    c.drawRect(win, paint(INK, stroke=5))                       # pul çerçevesi: kalın + ince çift çizgi
    c.drawRect(skia.Rect(28, 194, W - 28, H - 28), paint(INK, stroke=1.6))
    tw = say(c, BADGE, W / 2, 160, "PlayfairDisplay-900.ttf", 46, INK, spacing=7)
    for x0, x1 in ((44, W / 2 - tw / 2 - 24), (W / 2 + tw / 2 + 24, W - 44)):
        c.drawLine(x0, 143, x1, 143, paint(INK, stroke=2))
    say(c, "No. 001", 44, 80, "CormorantGaramond-700.ttf", 34, INK, align="left")
    say(c, "PARİS · 1889", W - 44, 80, "CormorantGaramond-700.ttf", 34, INK, align="right")
    style.grain(c, W, H, 1, alpha=0.10)


# ---------------------------------------------------------------- 2) Seyahat afişi (Art Deco)
def afis(c):
    NAVY, CREAM, GOLD, GOLD_D, ORANGE = "#101A33", "#F4E9D0", "#F2C14E", "#C9822F", "#E07A3F"
    bands = ["#101A33", "#14213F", "#1A2A4E", "#22355E", "#2E3F6C", "#4A4775", "#7D4F6E", "#B85E5C", "#E3895A"]
    hz = 1500
    edges = [0] + [hz * (1 - (1 - k / len(bands)) ** 0.55) for k in range(1, len(bands) + 1)]
    for i, col in enumerate(bands):
        c.drawRect(skia.Rect(0, edges[i], W, edges[i + 1] + 1), paint(col))
    TH = 1000
    cx, cy = 540, 1520 - TH                                      # güneş ışınları
    c.save()
    c.clipRect(skia.Rect(0, 0, W, hz))
    for k in range(0, 40, 2):
        a0, a1 = k * math.pi / 20, (k + 1) * math.pi / 20
        p = skia.Path()
        p.moveTo(cx, cy)
        p.lineTo(cx + 2400 * math.cos(a0), cy + 2400 * math.sin(a0))
        p.lineTo(cx + 2400 * math.cos(a1), cy + 2400 * math.sin(a1))
        p.close()
        c.drawPath(p, paint(CREAM, alpha=0.06))
    c.restore()
    c.drawCircle(850, 640, 58, paint(GOLD))
    c.drawCircle(850, 640, 84, paint(GOLD, stroke=4, alpha=0.6))
    rng = random.Random(4)
    for _ in range(14):
        star4(c, rng.uniform(80, W - 80), rng.uniform(560, 900), rng.uniform(8, 16), paint(GOLD, alpha=0.9))
    D.skyline(c, 1500, 11, "#1A2748", "#1A2748", None, scale=0.8)
    tp = D.tower_path(540, 1520, TH)
    c.save()
    c.clipPath(tp, doAntiAlias=True)
    c.drawRect(skia.Rect(0, 0, 540, H), paint(GOLD))
    c.drawRect(skia.Rect(540, 0, W, H), paint(GOLD_D))
    levels = [0, 0.176, 0.356, 0.5, 0.65, 0.85]
    for a, b in zip(levels, levels[1:]):                          # sade Deco kafes: kat başına bir X
        y0, y1 = 1520 - a * TH, 1520 - b * TH
        wa = float(np.interp(a, D._F, D._Wd)) * TH
        wb = float(np.interp(b, D._F, D._Wd)) * TH
        lp = paint("#8E5A22", stroke=7)
        c.drawLine(540 - wa, y0, 540 + wb, y1, lp)
        c.drawLine(540 + wa, y0, 540 - wb, y1, lp)
    c.restore()
    for f, extra in ((0.176, 1.18), (0.356, 1.22), (0.85, 1.6)):
        w = float(np.interp(f, D._F, D._Wd)) * TH * extra
        c.drawRect(skia.Rect(540 - w, 1520 - f * TH - 12, 540 + w, 1520 - f * TH + 4), paint(NAVY))
    c.drawLine(540, 1520 - TH, 540, 1470 - TH, paint(GOLD, stroke=6))
    D.skyline(c, 1660, 12, "#0D1530", "#0D1530", None)
    rng = random.Random(12)
    for _ in range(40):
        x, y = rng.uniform(0, W), rng.uniform(1420, 1640)
        c.drawRect(skia.Rect(x, y, x + 12, y + 18), paint(GOLD, alpha=0.8))
    c.drawRect(skia.Rect(0, 1660, W, H), paint("#0D1530"))
    say(c, "PARİS", W / 2, 400, "BebasNeue-400.ttf", 230, CREAM, spacing=26)
    c.drawLine(250, 440, 450, 440, paint(GOLD, stroke=3))
    c.drawLine(W - 450, 440, W - 250, 440, paint(GOLD, stroke=3))
    say(c, "1889", W / 2, 462, "BebasNeue-400.ttf", 58, GOLD, spacing=8)
    c.drawCircle(540, 900, 175, paint(ORANGE))                   # damga yerine Deco madalyon
    c.drawCircle(540, 900, 152, paint(CREAM, stroke=5))
    say(c, "SON TARİH", 540, 840, "BebasNeue-400.ttf", 54, CREAM, spacing=6)
    say(c, "1909", 540, 980, "BebasNeue-400.ttf", 150, CREAM, spacing=4)
    caption(c, "BebasNeue-400.ttf", 118, CREAM, GOLD, NAVY, 12, upper=True)
    c.drawRect(skia.Rect(13, 13, W - 13, H - 13), paint(CREAM, stroke=26))
    c.drawRect(skia.Rect(40, 40, W - 40, H - 40), paint(GOLD, stroke=2.5))
    c.drawRoundRect(skia.Rect(W / 2 - 250, 105, W / 2 + 250, 175), 35, 35, paint(NAVY))
    say(c, BADGE, W / 2, 158, "BebasNeue-400.ttf", 52, GOLD, spacing=6)
    style.grain(c, W, H, 2, alpha=0.08)


# ---------------------------------------------------------------- 3) Risograf (numpy: yarım ton + üst baskı)
INKS = {"blue": ((0x00, 0x78, 0xBF), 15, (0, 0)), "pink": ((0xFF, 0x48, 0xB0), 75, (5, 3)),
        "yellow": ((0xFF, 0xE8, 0x00), 0, (-4, 2))}


def density(draw):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(skia.Color4f(0, 0, 0, 0))
    draw(c)
    return surf.makeImageSnapshot().toarray()[..., 3].astype(np.float32) / 255


def halftone(d, angle, cell=None):
    cell = cell or CELL
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a = math.radians(angle)
    u = xx * math.cos(a) + yy * math.sin(a)
    v = -xx * math.sin(a) + yy * math.cos(a)
    fu = (u % cell) - cell / 2
    fv = (v % cell) - cell / 2
    thr = np.sqrt(fu * fu + fv * fv) / (cell / math.sqrt(2))
    return np.clip((d - thr) * cell * 0.5 + 0.5, 0, 1) * (d > 0.003)


def riso(out):
    A = lambda a: skia.Color4f(0, 0, 0, a)                      # noqa: E731
    clear = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kClear)
    rng = random.Random(3)
    stars = [(rng.uniform(60, W - 60), rng.uniform(150, 950), rng.uniform(7, 13)) for _ in range(40)]
    mx, my, mr = 820, 430, 70
    tp = D.tower_path(540, 1520, 1050)
    f = font("ArchivoBlack-400.ttf", 82)
    ws = [f.measureText(w) for w in WORDS]
    sp = f.measureText(" ")
    xs, x = [], W / 2 - (sum(ws) + sp * (len(ws) - 1)) / 2
    for wd in ws:
        xs.append(x)
        x += wd + sp
    boxes = [skia.Rect(x - 10, 1360, x + wd + 10, 1470) for x, wd in zip(xs, ws)]

    def knock(c, draw):
        c.saveLayer(None, skia.Paint(BlendMode=skia.BlendMode.kDstOut))
        draw(c)
        c.restore()

    def blue(c):
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeLinear(
            [(0, 0), (0, 1450)], [A(1.0).toColor(), A(0.30).toColor()])))
        for x, y, r in stars:
            star4(c, x, y, r, clear)
        c.drawCircle(mx, my, mr + 6, clear)
        D.skyline(c, 1500, 11, A(0.8), A(0.8), None, scale=0.8)
        c.save()
        c.clipPath(tp, doAntiAlias=True)
        c.drawRect(skia.Rect(0, 0, W, H), clear)
        k = -1050
        while k < 1050:
            c.drawLine(540 + k, 1520, 540 + k + 1050, 470, skia.Paint(AntiAlias=True, Color4f=A(1), StrokeWidth=4,
                                                                      Style=skia.Paint.kStroke_Style))
            c.drawLine(540 - k, 1520, 540 - k - 1050, 470, skia.Paint(AntiAlias=True, Color4f=A(1), StrokeWidth=4,
                                                                      Style=skia.Paint.kStroke_Style))
            k += 30
        c.restore()
        c.drawPath(tp, skia.Paint(AntiAlias=True, Color4f=A(1), Style=skia.Paint.kStroke_Style, StrokeWidth=5))
        D.skyline(c, 1660, 12, A(1), A(1), None, lit=0.0)
        c.drawRect(skia.Rect(0, 1660, W, H), skia.Paint(Color4f=A(1)))
        knock(c, lambda cc: D.skyline(cc, 1660, 12, A(0), A(0), A(1), lit=0.0))
        knock(c, lambda cc: D.stamp(cc, 540, 860, STAMP, 0.0, 1.0, color=A(1)))
        for i, (w, x, b) in enumerate(zip(WORDS, xs, boxes)):
            c.drawRect(b, clear)
            if i != CUR:
                c.drawString(w, x, 1442, f, skia.Paint(AntiAlias=True, Color4f=A(1)))
        c.drawRoundRect(skia.Rect(W / 2 - 330, 110, W / 2 + 330, 190), 40, 40, clear)
        say(c, BADGE, W / 2, 168, "SpaceGrotesk-700.ttf", 48, "#000000", spacing=5)

    def pink(c):
        c.drawRect(skia.Rect(0, 700, W, 1500), skia.Paint(Shader=skia.GradientShader.MakeLinear(
            [(0, 700), (0, 1480)], [A(0.0).toColor(), A(0.6).toColor()])))
        c.drawPath(tp, skia.Paint(AntiAlias=True, Color4f=A(1)))
        D.skyline(c, 1660, 12, A(0.35), A(0.35), None)
        D.stamp(c, 540, 860, STAMP, 0.0, 1.0, color=A(1))
        for b in boxes:
            c.drawRect(b, clear)
        c.drawString(WORDS[CUR], xs[CUR], 1442, f, skia.Paint(AntiAlias=True, Color4f=A(1)))
        c.drawRoundRect(skia.Rect(W / 2 - 330, 110, W / 2 + 330, 190), 40, 40, skia.Paint(AntiAlias=True, Color4f=A(1)))

    def yellow(c):
        c.drawCircle(mx, my, mr, skia.Paint(AntiAlias=True, Color4f=A(1)))
        for x, y, r in stars[::3]:
            star4(c, x, y, r, skia.Paint(AntiAlias=True, Color4f=A(1)))
        c.save()
        c.clipPath(tp, doAntiAlias=True)
        c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=skia.GradientShader.MakeLinear(
            [(0, 470), (0, 1520)], [A(0.85).toColor(), A(0.25).toColor()])))
        c.restore()
        D.skyline(c, 1660, 12, A(0), A(0), A(1), lit=0.0)
        for b in boxes:
            c.drawRect(b, clear)
        D.stamp(c, 540, 860, STAMP, 0.0, 1.0, color=A(0.9))

    paper = np.array([0xF2, 0xEE, 0xE3], np.float32) / 255
    img = np.ones((H, W, 3), np.float32) * paper
    nrng = np.random.default_rng(5)
    for name, fn in (("yellow", yellow), ("pink", pink), ("blue", blue)):
        col, ang, (dx, dy) = INKS[name]
        cov = halftone(density(fn), ang)
        cov = np.roll(cov, (dy, dx), axis=(0, 1))
        cov *= 1 - 0.35 * (nrng.random((H, W)) > 0.9)             # riso: mürekkep boşlukları
        colv = np.array(col, np.float32) / 255
        img *= 1 - cov[..., None] * (1 - colv)
    img *= 1 - 0.05 * nrng.random((H, W, 1))
    from PIL import Image
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(out)
    return out


# ---------------------------------------------------------------- 4) Kâğıt kesik diorama
def kagit(c):
    BG, CREAM, GOLD, CORAL = "#171A35", "#F5EBDD", "#E8B04B", "#E46F5A"
    c.drawRect(skia.Rect(0, 0, W, H), paint(BG))

    def wave(y, amp, seed, col):
        def f(cc):
            rng = random.Random(seed)
            p = skia.Path()
            p.moveTo(-20, H)
            p.lineTo(-20, y)
            ph = rng.uniform(0, 6)
            for x in range(-20, W + 40, 20):
                p.lineTo(x, y + amp * math.sin(x / 140 + ph) + amp * 0.4 * math.sin(x / 53 + ph * 2))
            p.lineTo(W + 20, H)
            p.close()
            cc.drawPath(p, paint(col))
        return f

    for y, amp, seed, col in ((620, 26, 1, "#1D2142"), (860, 30, 2, "#232850"), (1100, 28, 3, "#2A3060")):
        shadowed(c, wave(y, amp, seed, col), dy=-4, sigma=16, alpha=0.6)
    shadowed(c, lambda cc: (cc.drawCircle(820, 420, 78, paint(GOLD)), cc.drawCircle(808, 410, 56, paint("#F1C878"))),
             dy=8, sigma=16, alpha=0.6)
    rng = random.Random(3)
    pts = [(rng.uniform(60, W - 60), rng.uniform(150, 560), rng.uniform(7, 12)) for _ in range(22)]
    shadowed(c, lambda cc: [star5(cc, x, y, r, paint(CREAM)) for x, y, r in pts], dy=3, sigma=4, alpha=0.6)
    shadowed(c, lambda cc: D.skyline(cc, 1500, 11, "#353C74", "#353C74", None, scale=0.8), dy=-3, sigma=14)

    def tower(cc):
        tp = D.tower_path(540, 1520, 1050)
        cc.drawPath(tp, paint(CREAM))
        cc.save()
        cc.clipPath(tp, doAntiAlias=True)
        cc.drawRect(skia.Rect(540, 0, W, H), paint("#E2D4BF"))      # kâğıt kıvrımı: sağ yarı gölgede
        cl = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kClear, Style=skia.Paint.kStroke_Style,
                        StrokeWidth=6)
        k = -1050
        while k < 1050:
            cc.drawLine(540 + k, 1520, 540 + k + 1050, 470, cl)
            cc.drawLine(540 - k, 1520, 540 - k - 1050, 470, cl)
            k += 52
        cc.restore()
        for f, extra in ((0.176, 1.18), (0.356, 1.22), (0.85, 1.6)):
            w = float(np.interp(f, D._F, D._Wd)) * 1050 * extra
            cc.drawRect(skia.Rect(540 - w, 1520 - f * 1050 - 14, 540 + w, 1520 - f * 1050 + 4), paint(CREAM))
        cc.drawRect(skia.Rect(536, 420, 544, 472), paint(CREAM))

    shadowed(c, tower, dy=10, sigma=14, alpha=0.6)
    shadowed(c, lambda cc: (D.skyline(cc, 1660, 12, "#101329", "#101329", GOLD, lit=1.0),
                            cc.drawRect(skia.Rect(0, 1660, W, H), paint("#101329"))), dy=-5, sigma=16, alpha=0.7)

    def label(cc):
        cc.save()
        cc.translate(540, 860)
        cc.rotate(-6)
        cc.drawRoundRect(skia.Rect(-280, -130, 280, 130), 10, 10, paint(CORAL))
        cc.drawRoundRect(skia.Rect(-258, -108, 258, 108), 6, 6, paint(CREAM, stroke=4))
        say(cc, "SON TARİH", 0, -18, "Fraunces-900.ttf", 64, CREAM)
        say(cc, "1909", 0, 88, "Fraunces-900.ttf", 112, CREAM)
        cc.restore()

    shadowed(c, label, dy=12, sigma=14, alpha=0.6)

    def pill(cc):
        tw = style.measure(BADGE, 40, "Fraunces-900.ttf") + 4 * (len(BADGE) - 1)
        cc.drawRoundRect(skia.Rect(W / 2 - tw / 2 - 40, 112, W / 2 + tw / 2 + 40, 186), 37, 37, paint(CREAM))
        say(cc, BADGE, W / 2, 163, "Fraunces-900.ttf", 40, BG, spacing=4)

    shadowed(c, pill, dy=6, sigma=8, alpha=0.6)
    caption(c, "Fraunces-900.ttf", 80, CREAM, GOLD, "#101329", 12)
    style.grain(c, W, H, 3, alpha=0.16)
    style.vignette(c, W, H, 0.35)


LOOKS = {"1_gravur": gravur, "2_afis": afis, "4_kagit": kagit}


def sheet(paths, labels, out, w=540):
    from PIL import Image, ImageDraw, ImageFont
    h = int(w * H / W)
    pad, top = 16, 70
    im = Image.new("RGB", (len(paths) * (w + pad) + pad, h + top + pad), (24, 24, 28))
    dr = ImageDraw.Draw(im)
    fnt = ImageFont.truetype(os.path.join(style.FONTS, "Montserrat-800.ttf"), 30)
    for i, (p, lab) in enumerate(zip(paths, labels)):
        x = pad + i * (w + pad)
        im.paste(Image.open(p).convert("RGB").resize((w, h), Image.LANCZOS), (x, top))
        dr.text((x + 4, 18), lab, font=fnt, fill=(240, 232, 214))
    im.save(out, quality=90)
    return out


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "out/story/looks"
    os.makedirs(d, exist_ok=True)
    for name, fn in LOOKS.items():
        print(surface_png(fn, os.path.join(d, f"{name}.png")))
    print(riso(os.path.join(d, "3_riso.png")))
