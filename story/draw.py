"""Kodla çizim kütüphanesi (Yol 2): gökyüzü, Paris silueti, parametrik Eyfel, Panthéon, damga, belge kartları,
perde, telsiz dalgası, Mors, küre, bayrak dizisi, kalabalık, rüzgârölçer. Hepsi sahne boyutundan bağımsız
(konum/ölçek parametreli) ve zamana bağlı hareket alır (t, saniye)."""
import math
import random

import numpy as np
import skia

from story.style import (C, CREAM, INK, IRON, IRON_LIT, MUSTARD, NIGHT, PAPER, RUST, SERIF, SERIF_B, SANS_B,
                         SANS_K, SANS_XB, TERRA, TEAL, VELVET, VELVET_D, linear, measure, paint, radial, text)

W, H = 1080, 1920


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


# ---------------------------------------------------------------- gökyüzü
SKIES = {
    "night": ["#121B30", "#22304F", "#3A4569"],
    "dusk": ["#2B2F52", "#8C4E5A", "#E59A5B"],
    "day": ["#7FB3B0", "#B9D3C4", "#F1E3C4"],
    "war": ["#1A1420", "#4A1F25", "#8A3A2E"],
}


def sky(c, kind):
    cols = SKIES[kind]
    c.drawRect(skia.Rect(0, 0, W, H), linear(0, 0, 0, H * 0.75, cols, [0.0, 0.6, 1.0]))


def stars(c, t, seed=3, n=70, ymax=900, alpha=0.9):
    rng = random.Random(seed)
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(0, ymax)
        r = rng.uniform(1.2, 3.2)
        a = alpha * (0.45 + 0.55 * (0.5 + 0.5 * math.sin(t * rng.uniform(1.0, 3.0) + rng.uniform(0, 6))))
        c.drawCircle(x, y, r, paint(CREAM, alpha=a))


def moon(c, x, y, r):
    a = skia.Path()
    a.addCircle(x, y, r)
    b = skia.Path()
    b.addCircle(x + r * 0.45, y - r * 0.2, r * 0.92)
    try:
        cres = skia.Op(a, b, skia.PathOp.kDifference_PathOp)
    except Exception:
        cres = a
    c.drawCircle(x, y, r * 2.4, radial(x, y, r * 2.4, [C(CREAM, 0.18), C(CREAM, 0.0)]))
    c.drawPath(cres, paint("#F6E9C8"))


def cloud(c, x, y, s, color, alpha=1.0):
    p = paint(color, alpha=alpha)
    for dx, dy, r in ((0, 0, 60), (55, -25, 70), (120, 0, 55), (60, 15, 60), (-50, 10, 45)):
        c.drawCircle(x + dx * s, y + dy * s, r * s, p)


def clouds(c, t, seed, color, alpha=1.0, n=4, ymin=250, ymax=800, speed=12):
    rng = random.Random(seed)
    for _ in range(n):
        x0, y, s = rng.uniform(-200, W), rng.uniform(ymin, ymax), rng.uniform(0.6, 1.3)
        x = (x0 + speed * t * s) % (W + 400) - 200
        cloud(c, x, y, s, color, alpha)


def birds(c, t, seed=5, n=5, color=INK, x0=200, y0=520, spread=300):
    rng = random.Random(seed)
    for i in range(n):
        x = x0 + rng.uniform(-spread, spread) + 40 * t
        y = y0 + rng.uniform(-80, 80) + 6 * math.sin(t * 1.3 + i)
        flap = math.sin(t * 9 + i * 1.7)
        s = rng.uniform(10, 16)
        p = skia.Path()
        p.moveTo(x - s, y - s * 0.5 * flap)
        p.quadTo(x - s * 0.4, y - s * 0.2, x, y)
        p.quadTo(x + s * 0.4, y - s * 0.2, x + s, y - s * 0.5 * flap)
        c.drawPath(p, paint(color, stroke=3))


# ---------------------------------------------------------------- Paris silueti
def skyline(c, y_base, seed, body, roof, win=None, lit=0.0, scale=1.0, t=0.0, xmin=-200, xmax=W + 200):
    rng = random.Random(seed)
    x = xmin
    pb, pr = paint(body), paint(roof)
    while x < xmax:
        w = rng.uniform(80, 160) * scale
        h = rng.uniform(170, 360) * scale
        top = y_base - h
        c.drawRect(skia.Rect(x, top, x + w, y_base + 600), pb)
        # mansart çatı
        rh = 38 * scale
        roofp = skia.Path()
        roofp.moveTo(x - 4 * scale, top)
        roofp.lineTo(x + 10 * scale, top - rh)
        roofp.lineTo(x + w - 10 * scale, top - rh)
        roofp.lineTo(x + w + 4 * scale, top)
        roofp.close()
        c.drawPath(roofp, pr)
        for _ in range(rng.randint(1, 3)):
            cx = x + rng.uniform(0.15, 0.85) * w
            c.drawRect(skia.Rect(cx - 7 * scale, top - rh - 26 * scale, cx + 7 * scale, top - rh + 2), pr)
        if win:
            cols = max(2, int(w / (34 * scale)))
            floors = max(2, int(h / (52 * scale)))
            for i in range(cols):
                for j in range(floors):
                    wx = x + (i + 0.5) * w / cols - 7 * scale
                    wy = top + 22 * scale + j * 50 * scale
                    if wy > y_base - 20 * scale:
                        continue
                    on = rng.random() < lit
                    if on:
                        flick = 0.75 + 0.25 * math.sin(t * rng.uniform(0.3, 1.2) + rng.uniform(0, 6))
                        c.drawRect(skia.Rect(wx, wy, wx + 14 * scale, wy + 22 * scale), paint(MUSTARD, alpha=0.85 * flick))
                    else:
                        c.drawRect(skia.Rect(wx, wy, wx + 14 * scale, wy + 22 * scale), paint(win))
        x += w + rng.uniform(-6, 10) * scale


# ---------------------------------------------------------------- Eyfel Kulesi (parametrik)
_F = [0, 0.08, 0.17, 0.26, 0.35, 0.5, 0.7, 0.85, 0.95, 1.0]
_Wd = [0.205, 0.165, 0.128, 0.092, 0.064, 0.046, 0.030, 0.018, 0.009, 0.004]


def tower_path(x, y, h):
    ys = np.linspace(0, 1, 60)
    ws = np.interp(ys, _F, _Wd)
    p = skia.Path()
    p.moveTo(x - ws[0] * h, y)
    for f, w in zip(ys, ws):
        p.lineTo(x - w * h, y - f * h)
    for f, w in zip(ys[::-1], ws[::-1]):
        p.lineTo(x + w * h, y - f * h)
    a0 = 0.108 * h
    p.lineTo(x + a0, y)
    p.cubicTo(x + a0, y - 0.15 * h, x - a0, y - 0.15 * h, x - a0, y)
    p.close()
    return p


def tower(c, x, y, h, lit=False, t=0.0, sparkle=0.0, color=None, alpha=1.0, antenna=False):
    """x, y: taban ortası; h: yükseklik (piksel)."""
    path = tower_path(x, y, h)
    base = color or (IRON_LIT if lit else IRON)
    if lit:
        c.drawPath(path, linear(x, y - h, x, y, ["#F6D58A", IRON_LIT, "#C88B3A"]))
    else:
        c.drawPath(path, paint(base, alpha=alpha))
    c.save()
    c.clipPath(path, doAntiAlias=True)
    step = 0.022 * h
    lp = paint(INK if not lit else "#8A5A24", stroke=max(1.0, h * 0.0022), alpha=0.45 * alpha)
    k = -h
    while k < h:
        c.drawLine(x + k, y, x + k + h, y - h, lp)
        c.drawLine(x - k, y, x - k - h, y - h, lp)
        k += step
    c.restore()
    for f, extra in ((0.176, 1.18), (0.356, 1.22), (0.85, 1.6)):
        w = float(np.interp(f, _F, _Wd)) * h * extra
        th = max(3.0, 0.014 * h)
        c.drawRect(skia.Rect(x - w, y - f * h - th, x + w, y - f * h + th * 0.3),
                   paint(INK if not lit else "#7A4A1C", alpha=0.85 * alpha))
    c.drawPath(path, paint(INK if not lit else "#6B3E14", stroke=max(1.5, h * 0.004), alpha=0.9 * alpha))
    top = y - h
    c.drawLine(x, top, x, top - 0.05 * h, paint(INK, stroke=max(1.5, h * 0.004), alpha=alpha))
    if antenna:
        for dx in (-0.06, 0.06):
            c.drawLine(x, top - 0.05 * h, x + dx * h * 3, y - 0.2 * h, paint(INK, stroke=1.5, alpha=0.6 * alpha))
    if sparkle > 0:
        rng = random.Random(int(t * 12))
        for _ in range(int(60 * sparkle)):
            f = rng.random() * 0.95
            w = float(np.interp(f, _F, _Wd)) * h
            px = x + rng.uniform(-w, w)
            c.drawCircle(px, y - f * h, rng.uniform(1.5, 3.5), paint("#FFF6D8", alpha=rng.uniform(0.5, 1.0)))
    return top


def tower_top(x, y, h):
    return x, y - h


# ---------------------------------------------------------------- Panthéon
def pantheon(c, x, y, s, color, accent=None):
    p = paint(color)
    c.drawRect(skia.Rect(x - 130 * s, y - 90 * s, x + 130 * s, y), p)              # gövde
    ped = skia.Path()
    ped.moveTo(x - 140 * s, y - 90 * s)
    ped.lineTo(x, y - 140 * s)
    ped.lineTo(x + 140 * s, y - 90 * s)
    ped.close()
    c.drawPath(ped, p)
    c.drawRect(skia.Rect(x - 70 * s, y - 230 * s, x + 70 * s, y - 120 * s), p)     # kasnak
    dome = skia.Path()
    dome.addOval(skia.Rect(x - 72 * s, y - 330 * s, x + 72 * s, y - 150 * s))
    c.drawPath(dome, p)
    c.drawRect(skia.Rect(x - 14 * s, y - 370 * s, x + 14 * s, y - 320 * s), p)     # fener
    c.drawCircle(x, y - 372 * s, 14 * s, p)
    if accent:
        for i in range(-5, 6):
            c.drawLine(x + i * 12 * s, y - 225 * s, x + i * 12 * s, y - 125 * s, paint(accent, stroke=2 * s, alpha=0.5))


# ---------------------------------------------------------------- hareketli öğeler
def radio_waves(c, x, y, t, color=MUSTARD, n=4, rmax=520, period=1.4, width=6, arc=None):
    for k in range(n):
        ph = ((t / period) + k / n) % 1.0
        r = 20 + ph * rmax
        a = (1 - ph) ** 1.5
        p = paint(color, stroke=width * (1 - 0.5 * ph), alpha=a)
        if arc:
            c.drawArc(skia.Rect(x - r, y - r, x + r, y + r), arc[0], arc[1], False, p)
        else:
            c.drawCircle(x, y, r, p)


def morse(c, x0, y0, x1, y1, t, color=CREAM, speed=0.35, code="·−· ·− −·· ·· −−−", alpha=1.0):
    """Mors işaretleri iki nokta arasında akar."""
    syms = [ch for ch in code if ch in "·−"]
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    c.drawLine(x0, y0, x1, y1, paint(color, stroke=2, alpha=0.25 * alpha))
    gap = 0.07
    for i, s in enumerate(syms):
        f = (t * speed - i * gap) % 1.0
        px, py = x0 + ux * f * L, y0 + uy * f * L
        a = alpha * math.sin(math.pi * f)
        if s == "·":
            c.drawCircle(px, py, 7, paint(color, alpha=a))
        else:
            c.drawLine(px - ux * 14, py - uy * 14, px + ux * 14, py + uy * 14, paint(color, stroke=10, alpha=a))


def globe(c, x, y, r, t, land=TEAL, sea="#1F3F5B"):
    c.drawCircle(x, y, r, paint(sea))
    c.save()
    clip = skia.Path()
    clip.addCircle(x, y, r)
    c.clipPath(clip, doAntiAlias=True)
    for k in range(-3, 4):
        yy = y + k * r / 3.5
        c.drawLine(x - r, yy, x + r, yy, paint(CREAM, stroke=1.5, alpha=0.25))
    for k in range(6):
        ph = (k / 6 + t * 0.03) % 1.0
        rx = abs(math.cos(ph * math.pi)) * r
        c.drawOval(skia.Rect(x - rx, y - r, x + rx, y + r), paint(CREAM, stroke=1.5, alpha=0.25))
    c.restore()
    c.drawCircle(x, y, r, paint(CREAM, stroke=4, alpha=0.8))


def bunting(c, x0, y0, x1, y1, t, sag=60, n=14, colors=(TERRA, MUSTARD, TEAL, CREAM)):
    pts = []
    for i in range(n + 1):
        f = i / n
        sway = 6 * math.sin(t * 2 + f * 6)
        pts.append((x0 + (x1 - x0) * f, y0 + (y1 - y0) * f + sag * 4 * f * (1 - f) + sway))
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        c.drawLine(ax, ay, bx, by, paint(INK, stroke=2))
    for i, ((ax, ay), (bx, by)) in enumerate(zip(pts, pts[1:])):
        tri = skia.Path()
        mx, my = (ax + bx) / 2, (ay + by) / 2
        tri.moveTo(ax + 3, ay)
        tri.lineTo(bx - 3, by)
        tri.lineTo(mx, my + 34)
        tri.close()
        c.drawPath(tri, paint(colors[i % len(colors)]))


def crowd(c, y, t, seed=9, n=40, x0=0, x1=W, scale=1.0):
    rng = random.Random(seed)
    cols = [TERRA, TEAL, INK, RUST, "#6C5A49", MUSTARD]
    for _ in range(n):
        x = rng.uniform(x0, x1)
        s = rng.uniform(0.8, 1.2) * scale
        bob = 2 * math.sin(t * rng.uniform(2, 4) + rng.uniform(0, 6))
        col = rng.choice(cols)
        c.drawRoundRect(skia.Rect(x - 11 * s, y - 40 * s + bob, x + 11 * s, y + 10 * s), 9 * s, 9 * s, paint(col))
        c.drawCircle(x, y - 50 * s + bob, 9 * s, paint("#E2B48F"))
        if rng.random() < 0.4:      # şapka
            c.drawRect(skia.Rect(x - 10 * s, y - 64 * s + bob, x + 10 * s, y - 57 * s + bob), paint(INK))
            c.drawRect(skia.Rect(x - 6 * s, y - 76 * s + bob, x + 6 * s, y - 62 * s + bob), paint(INK))


def anemometer(c, x, y, s, t, color=INK):
    c.drawLine(x, y, x, y - 120 * s, paint(color, stroke=5 * s))
    a0 = t * 7
    for k in range(3):
        a = a0 + k * 2 * math.pi / 3
        ex = x + math.cos(a) * 60 * s
        ey = y - 120 * s + math.sin(a) * 14 * s
        c.drawLine(x, y - 120 * s, ex, ey, paint(color, stroke=4 * s))
        c.drawCircle(ex, ey, 14 * s * (0.6 + 0.4 * abs(math.cos(a))), paint(TERRA))


def wind_lines(c, t, seed=4, n=9, color=CREAM, y0=300, y1=1100, alpha=0.6):
    rng = random.Random(seed)
    for _ in range(n):
        y = rng.uniform(y0, y1)
        sp = rng.uniform(250, 420)
        L = rng.uniform(120, 260)
        x = (rng.uniform(0, W) + sp * t) % (W + 400) - 200
        p = skia.Path()
        p.moveTo(x, y)
        p.cubicTo(x + L * 0.3, y - 18, x + L * 0.6, y + 18, x + L, y)
        c.drawPath(p, paint(color, stroke=5, alpha=alpha))


# ---------------------------------------------------------------- kartlar ve damgalar
def shadow_card(c, rect, radius=18, color=PAPER, shadow=0.35):
    sh = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, shadow),
                    MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18))
    r2 = skia.Rect(rect.left() + 10, rect.top() + 18, rect.right() + 10, rect.bottom() + 18)
    c.drawRoundRect(r2, radius, radius, sh)
    c.drawRoundRect(rect, radius, radius, paint(color))


def stamp(c, x, y, lines, t_in, t, color=TERRA, angle=-9, w=560, h=230):
    """Damga: t_in anında ekrana çarpar (büyükten küçüğe), sonra hafif titrer."""
    if t < t_in:
        return
    k = ease_out((t - t_in) / 0.2)
    s = 2.2 - 1.2 * k
    a = min(1.0, (t - t_in) / 0.08)
    shake = 4 * math.exp(-(t - t_in) * 12) * math.sin((t - t_in) * 80)
    c.save()
    c.translate(x + shake, y)
    c.rotate(angle)
    c.scale(s, s)
    r = skia.Rect(-w / 2, -h / 2, w / 2, h / 2)
    c.drawRoundRect(r, 22, 22, paint(color, stroke=12, alpha=0.92 * a))
    r2 = skia.Rect(-w / 2 + 18, -h / 2 + 18, w / 2 - 18, h / 2 - 18)
    c.drawRoundRect(r2, 14, 14, paint(color, stroke=4, alpha=0.85 * a))
    n = len(lines)
    for i, (s_txt, size) in enumerate(lines):
        yy = (i - (n - 1) / 2) * size * 1.05 + size * 0.36
        text(c, s_txt, 0, yy, size, color=color, face=SANS_K, alpha=0.95 * a, spacing=3, max_w=w - 70)
    c.restore()


def place_card(c, x, y, name, sub, year, t_in, t, w=780, h=330):
    """Kartpostal yer kartı: aşağıdan kayarak gelir."""
    if t < t_in:
        return
    k = ease_out((t - t_in) / 0.45)
    yy = y + (1 - k) * 500
    rect = skia.Rect(x - w / 2, yy - h / 2, x + w / 2, yy + h / 2)
    shadow_card(c, rect, 20, CREAM)
    inner = skia.Rect(rect.left() + 18, rect.top() + 18, rect.right() - 18, rect.bottom() - 18)
    p = paint(TERRA, stroke=4)
    p.setPathEffect(skia.DashPathEffect.Make([18, 10], 0))
    c.drawRoundRect(inner, 12, 12, p)
    text(c, name.upper(), x - 60, yy - 10, 74, color=INK, face=SANS_K, max_w=w - 260)
    text(c, sub.upper(), x - 60, yy + 70, 34, color=TERRA, face=SANS_B, spacing=6, max_w=w - 260)
    # posta damgası
    px, py = x + w / 2 - 120, yy - 10
    c.save()
    c.translate(px, py)
    c.rotate(-14)
    c.drawCircle(0, 0, 78, paint(RUST, stroke=5))
    c.drawCircle(0, 0, 62, paint(RUST, stroke=2))
    text(c, year, 0, 16, 48, color=RUST, face=SANS_K)
    c.restore()


def permit(c, x, y, t_in, t, years_from=1889, years_to=1909, count_dur=2.2, lang="en"):
    if t < t_in:
        return
    k = ease_out((t - t_in) / 0.4)
    w, h = 720, 860
    yy = y + (1 - k) * 700
    rect = skia.Rect(x - w / 2, yy - h / 2, x + w / 2, yy + h / 2)
    shadow_card(c, rect, 10, "#F1E4C6")
    c.drawRect(skia.Rect(rect.left() + 30, rect.top() + 30, rect.right() - 30, rect.bottom() - 30), paint(INK, stroke=3))
    head = "CONCESSION" if lang == "en" else "İMTİYAZ"
    text(c, head, x, rect.top() + 130, 70, color=INK, face=SERIF_B, spacing=4)
    text(c, "Champ-de-Mars · Paris", x, rect.top() + 185, 34, color=RUST, face=SERIF)
    for i in range(5):
        ly = rect.top() + 250 + i * 34
        c.drawLine(rect.left() + 90, ly, rect.right() - 90 - (i % 2) * 120, ly, paint(INK, stroke=3, alpha=0.25))
    big = "20 YEARS" if lang == "en" else "20 YIL"
    text(c, big, x, rect.top() + 560, 120, color=TERRA, face=SANS_K)
    f = ease((t - t_in - 0.6) / count_dur)
    yr = int(round(years_from + (years_to - years_from) * f))
    text(c, f"{years_from}  →  {yr}", x, rect.top() + 680, 64, color=INK, face=SANS_XB)
    c.drawCircle(rect.right() - 140, rect.bottom() - 120, 62, paint(VELVET, alpha=0.9))
    c.drawCircle(rect.right() - 140, rect.bottom() - 120, 48, paint("#B4463F"))


def newspaper(c, x, y, t_in, t, lang="en"):
    if t < t_in:
        return
    k = ease_out((t - t_in) / 0.35)
    ang = -4 + (1 - k) * 25
    s = 0.6 + 0.4 * k
    w, h = 820, 1040
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    c.scale(s, s)
    rect = skia.Rect(-w / 2, -h / 2, w / 2, h / 2)
    shadow_card(c, rect, 6, "#EFE5D0")
    text(c, "LE TEMPS", 0, -h / 2 + 150, 120, color=INK, face=SERIF_B, spacing=6)
    c.drawLine(-w / 2 + 40, -h / 2 + 185, w / 2 - 40, -h / 2 + 185, paint(INK, stroke=4))
    text(c, "14 FÉVRIER 1887", 0, -h / 2 + 230, 34, color=INK, face=SERIF, spacing=3)
    c.drawLine(-w / 2 + 40, -h / 2 + 250, w / 2 - 40, -h / 2 + 250, paint(INK, stroke=2))
    text(c, "« INUTILE", 0, -h / 2 + 370, 92, color=INK, face=SERIF_B)
    text(c, "ET MONSTRUEUSE »", 0, -h / 2 + 470, 92, color=INK, face=SERIF_B, max_w=w - 80)
    sub = "“useless and monstrous”" if lang == "en" else "“yararsız ve korkunç”"
    text(c, sub, 0, -h / 2 + 545, 44, color=RUST, face=SERIF)
    rng = random.Random(7)
    for col in range(3):
        cx0 = -w / 2 + 50 + col * (w - 100) / 3
        for i in range(12):
            ly = -h / 2 + 610 + i * 32
            c.drawLine(cx0, ly, cx0 + (w - 100) / 3 - 30 - rng.uniform(0, 60), ly, paint(INK, stroke=6, alpha=0.18))
    c.restore()


def curtains(c, t, t0, dur=0.9, title="BEHIND THE LANDMARK"):
    """Seri jeneriği: kapalı perde + başlık, sonra iki yana açılır."""
    k = ease((t - t0) / dur)
    if k >= 1.0:
        return
    half = W / 2
    off = k * (half + 60)
    for side in (-1, 1):
        x0 = 0 if side < 0 else half
        c.save()
        c.translate(-off if side < 0 else off, 0)
        c.drawRect(skia.Rect(x0, 0, x0 + half, H), linear(x0, 0, x0 + half, 0, [VELVET_D, VELVET, VELVET_D]))
        for i in range(7):
            fx = x0 + (i + 0.5) * half / 7
            c.drawRect(skia.Rect(fx - 10, 0, fx + 10, H), paint(VELVET_D, alpha=0.45))
        c.restore()
    a = max(0.0, 1 - k * 2.5)
    if a > 0:
        text(c, title, W / 2, H * 0.47, 64, color=MUSTARD, face=SANS_K, spacing=6, alpha=a, max_w=W - 120)


def badge(c, label="BEHIND THE LANDMARK", y=258):
    tw = measure(label, 28, SANS_XB) + 9 * (len(label) - 1)
    r = skia.Rect(W / 2 - tw / 2 - 28, y - 40, W / 2 + tw / 2 + 28, y + 14)
    c.drawRoundRect(r, 27, 27, paint("#000000", alpha=0.35))
    text(c, label, W / 2, y, 28, color=MUSTARD, face=SANS_XB, spacing=9)
