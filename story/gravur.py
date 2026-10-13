"""Seri tasarım dili: Pul Gravürü (kullanıcı seçti, 2026-10-13; seçenekler story/TASARIM.md).

Kurallar: krem kâğıt + tek mürekkep (koyu lacivert) + tek vurgu (kırmızı damga). Ton = kazıma çizgisi yoğunluğu.
Gökyüzü taraması kameradan bağımsız (ekrana sabit): her karede kaymadığı için sıkıştırmada az bit yer; ölçüm
story/TASARIM.md. Çizgiler ≥ 1,5 px (2,5 Mbps'te daha incesi kayboluyor).
Çerçeve: çift çizgili pul penceresi; üst boşlukta bölüm no., seri adı, yer · yıl. Altyazı: kâğıt etiket.
Jenerik: perde yerine posta damgası (seri adı halkada) iner.
"""
import math
import random

import numpy as np
import skia

from story import draw as D
from story import style
from story.brand import BRAND
from story.style import paint, typeface

W, H = D.W, D.H
PAPER, INK, RED = "#EEE4CC", "#1E2233", "#C23B22"
DISPLAY, SMALL = "PlayfairDisplay-900.ttf", "CormorantGaramond-700.ttf"
WIN = skia.Rect(44, 210, W - 44, H - 44)       # sahne penceresi


def tr_upper(s, lang="tr"):
    return s.replace("i", "İ").replace("ı", "I").upper() if lang == "tr" else s.upper()


def L(ctx, en, tr):
    return en if ctx["lang"] == "en" else tr


def font(face, size):
    f = skia.Font(typeface(face), size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def say(c, s, x, y, size, color=INK, face=DISPLAY, align="center", spacing=0.0, alpha=1.0, halo=None, max_w=None):
    """Yazı; halo verilirse kâğıt renkli kontur (taralı zeminde okunsun)."""
    f = font(face, size)
    w = f.measureText(s) + spacing * max(0, len(s) - 1)
    if max_w and w > max_w:
        return say(c, s, x, y, size * max_w / w, color, face, align, spacing, alpha, halo)
    x0 = x - w / 2 if align == "center" else (x - w if align == "right" else x)
    paints = []
    if halo:
        hp = skia.Paint(AntiAlias=True, Color4f=style.C(PAPER, alpha), Style=skia.Paint.kStroke_Style,
                        StrokeWidth=halo, StrokeJoin=skia.Paint.kRound_Join)
        paints.append(hp)
    paints.append(paint(color, alpha=alpha))
    for p in paints:
        xx = x0
        if spacing:
            for ch in s:
                c.drawString(ch, xx, y, f, p)
                xx += f.measureText(ch) + spacing
        else:
            c.drawString(s, xx, y, f, p)
    return w


# ---------------------------------------------------------------- kamera (matris: gökyüzü delikleri ekrana eşlenir)
def cam(u, dur, push=0.07, rise=0.0):
    k = D.ease(u / max(dur, 0.1))
    s = 1 + push * k
    m = skia.Matrix()
    m.preTranslate(W / 2, H / 2)
    m.preScale(s, s)
    m.preTranslate(-W / 2, -H / 2 - rise * k)
    return m, k


def circle_hole(m, x, y, r):
    p = m.mapXY(x, y)
    h = skia.Path()
    h.addCircle(p.x(), p.y(), r * m.getScaleX())
    return h


# ---------------------------------------------------------------- doku yardımcıları
def fill_pattern(c, shape, pattern):
    c.saveLayer(None, None)
    shape(c)
    c.saveLayer(None, skia.Paint(BlendMode=skia.BlendMode.kSrcIn))
    pattern(c)
    c.restore()
    c.restore()


def outlined(c, draw, w=3.0):
    """Herhangi bir dolgu çizimine mürekkep kontur: 8 yönde mürekkeple, sonra kâğıtla çizer."""
    for a in range(8):
        c.save()
        c.translate(w * math.cos(a * math.pi / 4), w * math.sin(a * math.pi / 4))
        draw(c, INK)
        c.restore()
    draw(c, PAPER)


def vlines(c, x0, x1, y0, y1, gap, width, alpha=1.0):
    p = paint(INK, stroke=width, alpha=alpha, cap=skia.Paint.kButt_Cap)
    x = x0
    while x < x1:
        c.drawLine(x, y0, x, y1, p)
        x += gap


def hlines(c, x0, x1, y0, y1, gap, width, alpha=1.0):
    p = paint(INK, stroke=width, alpha=alpha, cap=skia.Paint.kButt_Cap)
    y = y0
    while y < y1:
        c.drawLine(x0, y, x1, y, p)
        y += gap


def dlines(c, rect, gap, width, alpha=1.0, slope=1.0):
    c.save()
    c.clipRect(rect)
    p = paint(INK, stroke=width, alpha=alpha, cap=skia.Paint.kButt_Cap)
    hgt = rect.height()
    x = rect.left() - hgt * slope
    while x < rect.right():
        c.drawLine(x, rect.bottom(), x + hgt * slope, rect.top(), p)
        x += gap
    c.restore()


def hatched_shadow(c, rect, dx=20, dy=26, radius=0):
    r = skia.Rect(rect.left() + dx, rect.top() + dy, rect.right() + dx, rect.bottom() + dy)
    dlines(c, r, 7, 2.2, alpha=0.9)


# ---------------------------------------------------------------- gökyüzü, ay, yıldız, bulut
SKY = {"night": (9, 4.6, 0.7), "dusk": (9, 3.2, 0.5), "day": (12, 2.0, 0.0), "war": (8, 5.6, 1.6)}


def sky(c, kind, holes=()):
    """Ekrana sabit yatay kazıma; kalınlık yukarıdan aşağı azalır. holes: ekran koordinatında boş bırakılan yollar."""
    gap, wt, wb = SKY[kind]
    c.drawRect(skia.Rect(0, 0, W, H), paint(PAPER))
    c.save()
    for h in holes:
        c.clipPath(h, skia.ClipOp.kDifference, True)
    y = WIN.top() + 4
    while y < 1700:
        w = float(np.interp(y, [210, 1350], [wt, wb]))
        if w >= 0.6:
            c.drawLine(0, y, W, y, paint(INK, stroke=max(1.5, w) if w >= 1.0 else 1.5, alpha=min(1.0, w / 1.5),
                                         cap=skia.Paint.kButt_Cap))
        y += gap
    c.restore()


def moon(c, x, y, r):
    for rr in (r + 26, r + 42):
        c.drawCircle(x, y, rr, paint(INK, stroke=1.6, alpha=0.75))
    c.drawCircle(x, y, r, paint(PAPER))
    c.drawCircle(x, y, r, paint(INK, stroke=3))
    cres = skia.Path()
    cres.addCircle(x + r * 0.38, y - r * 0.14, r * 0.9)
    mp = skia.Path()
    mp.addCircle(x, y, r)
    c.save()
    c.clipPath(mp, doAntiAlias=True)
    c.clipPath(cres, skia.ClipOp.kDifference, True)
    k = -r * 1.5
    while k < r * 1.5:
        c.drawLine(x - r * 1.4, y + k, x + r * 1.4, y + k - r * 0.7, paint(INK, stroke=1.8))
        k += 7
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


def stars(c, t, seed=3, n=40, ymax=900, avoid=None, color=PAPER):
    rng = random.Random(seed)
    for _ in range(n):
        x, y = rng.uniform(70, W - 70), rng.uniform(260, ymax)
        r = rng.uniform(7, 13)
        tw = 0.75 + 0.25 * math.sin(t * rng.uniform(1.5, 3.5) + rng.uniform(0, 6))
        if avoid and math.hypot(x - avoid[0], y - avoid[1]) < avoid[2]:
            continue
        star4(c, x, y, r * tw, paint(color))


_cloud = {}


def cloud_path(s):
    k = round(s, 2)
    if k not in _cloud:
        p = None
        for dx, dy, r in ((0, 0, 60), (55, -25, 70), (120, 0, 55), (60, 15, 60), (-50, 10, 45)):
            q = skia.Path()
            q.addCircle(dx * s, dy * s, r * s)
            p = q if p is None else skia.Op(p, q, skia.PathOp.kUnion_PathOp)
        _cloud[k] = p
    return _cloud[k]


def clouds(c, t, seed, n=4, ymin=280, ymax=800, speed=12):
    rng = random.Random(seed)
    for _ in range(n):
        x0, y, s = rng.uniform(-200, W), rng.uniform(ymin, ymax), rng.uniform(0.6, 1.3)
        x = (x0 + speed * t * s) % (W + 400) - 200
        p = skia.Path(cloud_path(s))
        p.offset(x, y)
        c.drawPath(p, paint(PAPER))
        c.save()
        c.clipPath(p, doAntiAlias=True)
        c.clipRect(skia.Rect(x - 200, y + 8 * s, x + 300, y + 200))
        hlines(c, x - 120 * s, x + 200 * s, y + 10 * s, y + 90 * s, 6, 1.6)
        c.restore()
        c.drawPath(p, paint(INK, stroke=2.6))


# ---------------------------------------------------------------- yapılar
def skyline_hatch(c, y_base, seed, scale=1.0, gap=7, width=2.4, cross=False):
    def pat(cc):
        cc.drawRect(skia.Rect(0, 0, W, H), paint(PAPER))
        vlines(cc, -10, W + 10, y_base - 700 * scale, y_base + 700, gap, width)
        if cross:
            hlines(cc, -10, W + 10, y_base - 700 * scale, y_base + 700, gap + 2, width * 0.8)
    fill_pattern(c, lambda cc: _skyline_solid(cc, y_base, seed, scale), pat)


def _skyline_solid(c, y_base, seed, scale):
    """D.skyline binalar arasında ≤ 10 px boşluk bırakıyor (kâğıt zeminde beyaz çizgi olarak görünüyordu):
    ±5 px kaydırılmış iki kopya boşlukları kapatır."""
    for dx in (-5, 5, 0):
        c.save()
        c.translate(dx, 0)
        D.skyline(c, y_base, seed, INK, INK, None, scale=scale)
        c.restore()


def skyline_ink(c, y_base, seed, scale=1.0, windows=True, lit=0.0, t=0.0):
    for dx in (-5, 5):
        c.save()
        c.translate(dx, 0)
        D.skyline(c, y_base, seed, INK, INK, None, scale=scale)
        c.restore()
    D.skyline(c, y_base, seed, INK, INK, PAPER if windows else None, lit=0.0, scale=scale, t=t)
    c.drawRect(skia.Rect(-200, y_base, W + 200, H + 400), paint(INK))


def tower(c, x, y, h, alpha=1.0, ink=False, antenna=False, shade=True):
    if ink:
        D.tower(c, x, y, h, color=INK, alpha=alpha, antenna=antenna)
        return
    D.tower(c, x, y, h, color=PAPER, alpha=alpha, antenna=antenna)
    if shade:
        c.save()
        c.clipPath(D.tower_path(x, y, h), doAntiAlias=True)
        c.clipRect(skia.Rect(x, y - h - 20, x + h, y + 10))
        vlines(c, x + 3, x + 0.25 * h, y - h, y + 10, 6, 1.6, alpha=0.85 * alpha)
        c.restore()


def pantheon(c, x, y, s):
    outlined(c, lambda cc, col: D.pantheon(cc, x, y, s, col), w=3)
    c.save()
    c.clipRect(skia.Rect(x - 130 * s, y - 85 * s, x + 130 * s, y))                 # sütunlar
    vlines(c, x - 120 * s, x + 125 * s, y - 85 * s, y, 22 * s, 7 * s)
    c.restore()
    p = skia.Path()
    p.addOval(skia.Rect(x - 72 * s, y - 330 * s, x + 72 * s, y - 150 * s))
    c.save()
    c.clipPath(p, doAntiAlias=True)
    c.clipRect(skia.Rect(x + 5, y - 340 * s, x + 80 * s, y))
    vlines(c, x + 5, x + 75 * s, y - 335 * s, y - 140 * s, 6, 1.6)
    c.restore()


def bunting(c, x0, y0, x1, y1, t, sag=60, n=14):
    pts = []
    for i in range(n + 1):
        f = i / n
        sway = 6 * math.sin(t * 2 + f * 6)
        pts.append((x0 + (x1 - x0) * f, y0 + (y1 - y0) * f + sag * 4 * f * (1 - f) + sway))
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        c.drawLine(ax, ay, bx, by, paint(INK, stroke=2.5))
    for i, ((ax, ay), (bx, by)) in enumerate(zip(pts, pts[1:])):
        tri = skia.Path()
        mx, my = (ax + bx) / 2, (ay + by) / 2
        tri.moveTo(ax + 3, ay)
        tri.lineTo(bx - 3, by)
        tri.lineTo(mx, my + 36)
        tri.close()
        c.drawPath(tri, paint(RED if i % 2 == 0 else PAPER))
        c.drawPath(tri, paint(INK, stroke=2))


def crowd(c, y, t, seed=9, n=40, x0=0, x1=W, scale=1.0):
    def fig(cc, col):
        rng = random.Random(seed)
        for _ in range(n):
            x = rng.uniform(x0, x1)
            s = rng.uniform(0.8, 1.2) * scale
            bob = 2 * math.sin(t * rng.uniform(2, 4) + rng.uniform(0, 6))
            hat = rng.random() < 0.4
            cc.drawRoundRect(skia.Rect(x - 11 * s, y - 40 * s + bob, x + 11 * s, y + 10 * s), 9 * s, 9 * s, paint(col))
            cc.drawCircle(x, y - 50 * s + bob, 9 * s, paint(col))
            if hat:
                cc.drawRect(skia.Rect(x - 10 * s, y - 64 * s + bob, x + 10 * s, y - 57 * s + bob), paint(col))
                cc.drawRect(skia.Rect(x - 6 * s, y - 76 * s + bob, x + 6 * s, y - 62 * s + bob), paint(col))
    outlined(c, fig, w=2.5)


def anemometer(c, x, y, s, t):
    c.drawLine(x, y, x, y - 120 * s, paint(INK, stroke=5 * s))
    a0 = t * 7
    for k in range(3):
        a = a0 + k * 2 * math.pi / 3
        ex = x + math.cos(a) * 60 * s
        ey = y - 120 * s + math.sin(a) * 14 * s
        c.drawLine(x, y - 120 * s, ex, ey, paint(INK, stroke=4 * s))
        r = 14 * s * (0.6 + 0.4 * abs(math.cos(a)))
        c.drawCircle(ex, ey, r, paint(RED))
        c.drawCircle(ex, ey, r, paint(INK, stroke=2.5))


def globe(c, x, y, r, t):
    c.drawCircle(x, y, r, paint(PAPER))
    clip = skia.Path()
    clip.addCircle(x, y, r)
    c.save()
    c.clipPath(clip, doAntiAlias=True)
    for k in range(-3, 4):
        yy = y + k * r / 3.5
        c.drawLine(x - r, yy, x + r, yy, paint(INK, stroke=1.8))
    for k in range(6):
        ph = (k / 6 + t * 0.03) % 1.0
        rx = abs(math.cos(ph * math.pi)) * r
        c.drawOval(skia.Rect(x - rx, y - r, x + rx, y + r), paint(INK, stroke=1.8))
    sh = skia.Path()
    sh.addCircle(x - r * 0.35, y - r * 0.3, r * 1.05)
    c.clipPath(sh, skia.ClipOp.kDifference, True)
    dlines(c, skia.Rect(x - r, y - r, x + r, y + r), 6, 2.0)
    c.restore()
    c.drawCircle(x, y, r, paint(INK, stroke=4))


def radio_waves(c, x, y, t, color=INK, n=4, rmax=520, period=1.4, width=5):
    for k in range(n):
        ph = ((t / period) + k / n) % 1.0
        r = 20 + ph * rmax
        a = (1 - ph) ** 1.2
        c.drawCircle(x, y, r, paint(color, stroke=max(1.6, width * (1 - 0.5 * ph)), alpha=a))


# ---------------------------------------------------------------- damgalar, belgeler, kartlar
_spk = {}


def rubber(c, x, y, lines, t_in, t, color=RED, angle=-9, w=560, h=230):
    """Kauçuk damga: D.stamp + aşınma (mürekkep boşlukları)."""
    if t < t_in:
        return
    if (w, h) not in _spk:
        rng = random.Random(8)
        _spk[(w, h)] = [(rng.uniform(-w * 0.6, w * 0.6), rng.uniform(-h * 0.8, h * 0.8), rng.uniform(0.8, 3.0))
                        for _ in range(int(w * h / 140))]
    c.saveLayer(None, None)
    D.stamp(c, x, y, lines, t_in, t, color=color, angle=angle, w=w, h=h)
    er = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kDstOut)
    for dx, dy, r in _spk[(w, h)]:
        c.drawCircle(x + dx, y + dy, r, er)
    c.restore()


def arc_text(c, s, radius, center_deg, size, color, alpha, spacing=3.0, inside=False):
    """Yay üstüne yazı, center_deg merkezli (−90 üst). inside=True: alt yayda soldan sağa okunur."""
    f = font(DISPLAY, size)
    ws = [f.measureText(ch) + spacing for ch in s]
    total = sum(ws)
    sign = -1 if inside else 1
    ang = math.radians(center_deg) - sign * total / 2 / radius
    for ch, w in zip(s, ws):
        mid = ang + sign * (w / 2) / radius
        c.save()
        c.translate(radius * math.cos(mid), radius * math.sin(mid))
        c.rotate(math.degrees(mid) + (90 if not inside else -90))
        c.drawString(ch, -f.measureText(ch) / 2, size * 0.35 if not inside else size * 0.35, f, paint(color, alpha=alpha))
        c.restore()
        ang += sign * w / radius


def postmark(c, x, y, ring, center, sub, t_in, t, hold=1.05, color=RED, r=200, bottom=""):
    """Posta damgası: halkada seri adı, ortada yer, sağda dalgalı iptal çizgileri. Çarpar, bekler, solar."""
    if t < t_in or t > t_in + hold + 0.3:
        return
    k = D.ease_out((t - t_in) / 0.18)
    s = 2.0 - 1.0 * k
    a = min(1.0, (t - t_in) / 0.06) * (1 - D.ease((t - t_in - hold) / 0.3))
    shake = 5 * math.exp(-(t - t_in) * 12) * math.sin((t - t_in) * 80)
    c.save()
    c.translate(x + shake, y)
    c.rotate(-8)
    c.scale(s, s)
    p = paint(color, stroke=9, alpha=a)
    c.drawCircle(0, 0, r, p)
    c.drawCircle(0, 0, r - 62, paint(color, stroke=4, alpha=a))
    arc_text(c, ring, r - 44, -90, 34, color, a)                   # üst yay: seri adı
    arc_text(c, bottom, r - 44, 90, 30, color, a, inside=True)     # alt yay: bölüm no.
    say(c, center, 0, 8, 62, color=color, alpha=a, max_w=2 * (r - 80))
    say(c, sub, 0, 62, 40, color=color, face=SMALL, alpha=a, spacing=4)
    for i in range(5):                                            # iptal dalgaları
        pth = skia.Path()
        yy = -80 + i * 40
        pth.moveTo(r + 20, yy)
        for xx in range(int(r + 20), int(r + 520), 10):
            pth.lineTo(xx, yy + 14 * math.sin(xx / 34))
        c.drawPath(pth, paint(color, stroke=7, alpha=a))
    c.restore()


def place_card(c, x, y, name, sub, year, t_in, t, w=800, h=360):
    """Kartpostal: aşağıdan kayar; sağ üstte minik pul + kırmızı posta damgası."""
    if t < t_in:
        return
    k = D.ease_out((t - t_in) / 0.45)
    yy = y + (1 - k) * 500
    rect = skia.Rect(x - w / 2, yy - h / 2, x + w / 2, yy + h / 2)
    hatched_shadow(c, rect)
    c.drawRect(rect, paint(PAPER))
    c.drawRect(rect, paint(INK, stroke=4))
    c.drawRect(skia.Rect(rect.left() + 16, rect.top() + 16, rect.right() - 16, rect.bottom() - 16), paint(INK, stroke=1.6))
    c.drawLine(x + 120, rect.top() + 60, x + 120, rect.bottom() - 60, paint(INK, stroke=1.6))   # kartpostal ayırıcı
    say(c, name, rect.left() + 50, yy + 10, 78, align="left", max_w=w / 2 + 60)
    say(c, sub, rect.left() + 52, yy + 80, 38, face=SMALL, align="left", spacing=4, max_w=w / 2 + 40)
    for i in range(3):
        c.drawLine(x + 160, yy + 40 + i * 50, rect.right() - 50, yy + 40 + i * 50, paint(INK, stroke=1.6))
    sx, sy, sw, sh = rect.right() - 170, rect.top() + 40, 120, 140                  # minik pul
    c.drawRect(skia.Rect(sx, sy, sx + sw, sy + sh), paint(PAPER))
    for i in range(7):
        for yy2 in (sy, sy + sh):
            c.drawCircle(sx + i * sw / 6, yy2, 5, paint(INK, stroke=1.5))
    c.drawRect(skia.Rect(sx + 10, sy + 10, sx + sw - 10, sy + sh - 10), paint(INK, stroke=2))
    tower(c, sx + sw / 2, sy + sh - 14, sh - 34, shade=False)
    c.save()
    c.translate(sx - 10, sy + sh - 6)
    c.rotate(-14)
    c.drawCircle(0, 0, 70, paint(RED, stroke=5, alpha=0.9))
    c.drawCircle(0, 0, 56, paint(RED, stroke=2, alpha=0.9))
    say(c, year, 0, 16, 44, color=RED, alpha=0.95)
    c.restore()


def permit(c, x, y, t_in, t, lang, years_from=1889, years_to=1909, count_dur=2.2):
    if t < t_in:
        return
    k = D.ease_out((t - t_in) / 0.4)
    w, h = 720, 860
    yy = y + (1 - k) * 700
    rect = skia.Rect(x - w / 2, yy - h / 2, x + w / 2, yy + h / 2)
    hatched_shadow(c, rect)
    c.drawRect(rect, paint(PAPER))
    c.drawRect(rect, paint(INK, stroke=3))
    c.drawRect(skia.Rect(rect.left() + 26, rect.top() + 26, rect.right() - 26, rect.bottom() - 26), paint(INK, stroke=5))
    c.drawRect(skia.Rect(rect.left() + 36, rect.top() + 36, rect.right() - 36, rect.bottom() - 36), paint(INK, stroke=1.5))
    say(c, "CONCESSION" if lang == "en" else "İMTİYAZ", x, rect.top() + 140, 76, spacing=4)
    say(c, "Champ-de-Mars · Paris", x, rect.top() + 195, 38, face=SMALL)
    for i in range(5):
        ly = rect.top() + 255 + i * 34
        c.drawLine(rect.left() + 90, ly, rect.right() - 90 - (i % 2) * 120, ly, paint(INK, stroke=2, alpha=0.5))
    say(c, "20 YEARS" if lang == "en" else "20 YIL", x, rect.top() + 560, 128, color=RED)
    f = D.ease((t - t_in - 0.6) / count_dur)
    yr = int(round(years_from + (years_to - years_from) * f))
    say(c, f"{years_from} – {yr}", x, rect.top() + 680, 66)
    sx, sy = rect.right() - 140, rect.bottom() - 120                               # mühür
    c.drawCircle(sx, sy, 60, paint(RED))
    c.drawCircle(sx, sy, 44, paint(PAPER, stroke=3, alpha=0.7))
    c.drawCircle(sx, sy, 60, paint(INK, stroke=2.5))


def newspaper(c, x, y, t_in, t, lang):
    if t < t_in:
        return
    k = D.ease_out((t - t_in) / 0.35)
    ang = -4 + (1 - k) * 25
    s = 0.6 + 0.4 * k
    w, h = 820, 1040
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    c.scale(s, s)
    rect = skia.Rect(-w / 2, -h / 2, w / 2, h / 2)
    hatched_shadow(c, rect, 24, 30)
    c.drawRect(rect, paint("#F2EAD6"))
    c.drawRect(rect, paint(INK, stroke=3))
    say(c, "LE TEMPS", 0, -h / 2 + 150, 124, spacing=6)
    c.drawLine(-w / 2 + 40, -h / 2 + 185, w / 2 - 40, -h / 2 + 185, paint(INK, stroke=4))
    say(c, "14 FÉVRIER 1887", 0, -h / 2 + 232, 38, face=SMALL, spacing=3)
    c.drawLine(-w / 2 + 40, -h / 2 + 252, w / 2 - 40, -h / 2 + 252, paint(INK, stroke=2))
    say(c, "« INUTILE", 0, -h / 2 + 372, 96)
    say(c, "ET MONSTRUEUSE »", 0, -h / 2 + 472, 96, max_w=w - 80)
    say(c, "“useless and monstrous”" if lang == "en" else "“yararsız ve korkunç”", 0, -h / 2 + 548, 46,
        color=RED, face=SMALL)
    rng = random.Random(7)
    for col in range(3):
        cx0 = -w / 2 + 50 + col * (w - 100) / 3
        for i in range(12):
            ly = -h / 2 + 610 + i * 32
            c.drawLine(cx0, ly, cx0 + (w - 100) / 3 - 30 - rng.uniform(0, 60), ly, paint(INK, stroke=5, alpha=0.35))
    c.restore()


def desk(c):
    c.drawRect(skia.Rect(0, 0, W, H), paint(PAPER))
    dlines(c, skia.Rect(0, 0, W, H), 8, 3.4, slope=0.18)
    for i in range(15):
        c.drawLine(0, 140 * i + 30, W, 140 * i + 52, paint(INK, stroke=9))


# ---------------------------------------------------------------- sahneler (scenes.py ile aynı yerleşim)
def hook(c, u, dur, ctx):
    t = ctx["t"]
    m, k = cam(u, dur, push=0.10)
    mx, my, mr = 820, 420 + 30 * k, 58
    sky(c, "night", holes=[circle_hole(m, mx, my, mr + 12)])
    c.concat(m)
    moon(c, mx, my, mr)
    stars(c, t, avoid=(mx, my, mr + 70))
    c.save(); c.translate(0, 20 * k); skyline_hatch(c, 1500, 11, scale=0.8); c.restore()
    tower(c, 540, 1520, 1050)
    c.save(); c.translate(0, -25 * k); skyline_ink(c, 1660, 12); c.restore()
    rubber(c, 540, 860, [(L(ctx, "EXPIRES", "SON TARİH"), 70), ("1909", 120)], 1.25, u)


def place(c, u, dur, ctx):
    t, pl, lang = ctx["t"], ctx["place"], ctx["lang"]
    m, k = cam(u, dur, push=0.06, rise=-40)
    sky(c, "day")
    c.concat(m)
    clouds(c, t, 4, n=4)
    c.save(); c.translate(-30 * k, 0); skyline_hatch(c, 1480, 21, scale=0.7, gap=9, width=1.8); c.restore()
    tower(c, 540, 1560, 1100)
    bunting(c, -20, 1250, 1100, 1240, t)
    c.save(); c.translate(-80 * k, 0)
    skyline_hatch(c, 1700, 22, scale=1.0, gap=6, width=2.6, cross=True)
    c.drawRect(skia.Rect(-200, 1700, W + 200, H + 200), paint(INK))
    crowd(c, 1730, t, n=36)
    c.restore()
    name = pl["name"] if lang == "en" else pl.get("name_tr", pl["name"])
    country = pl["country"] if lang == "en" else pl.get("country_tr", pl["country"])
    place_card(c, 540, 620, name, f"{pl['city']} · {country}", pl["year"], 0.55, u)


def permit_s(c, u, dur, ctx):
    m, k = cam(u, dur, push=0.05)
    sky(c, "dusk")
    c.concat(m)
    fade = 1.0 - 0.7 * D.ease((u - 3.2) / 1.2)                   # "yıkılması gerekiyordu": kule solar
    skyline_hatch(c, 1580, 31, gap=8, width=2.0)
    tower(c, 820, 1640, 1050, alpha=fade)
    skyline_ink(c, 1720, 32, scale=1.1, windows=False)
    permit(c, 470, 900, 0.15, u, ctx["lang"])


def news(c, u, dur, ctx):
    desk(c)
    m, k = cam(u, dur, push=0.08)
    c.concat(m)
    newspaper(c, 540, 880, 0.1, u, ctx["lang"])


def science(c, u, dur, ctx):
    t = ctx["t"]
    m, k = cam(u, dur, push=0.05, rise=60)
    sky(c, "day")
    c.concat(m)
    clouds(c, t, 8, n=6, speed=70)
    tower(c, 540, 4100, 3600)                                     # yakın plan: tepe
    plat_y = 4100 - 0.85 * 3600
    anemometer(c, 680, plat_y - 20, 2.2, t)
    anemometer(c, 400, plat_y - 20, 1.6, t + 0.4)
    D.wind_lines(c, t, n=12, color=INK, alpha=0.8)


def radio(c, u, dur, ctx):
    t = ctx["t"]
    m, k = cam(u, dur, push=0.06)
    sky(c, "day")
    c.concat(m)
    skyline_hatch(c, 1520, 41, scale=0.6, gap=9, width=1.8)
    pantheon(c, 830, 1540, 0.75)
    tx, ty = 300, 1650 - 1150
    tower(c, 300, 1650, 1150)
    skyline_hatch(c, 1720, 42, scale=0.9, gap=6, width=2.6, cross=True)
    c.drawRect(skia.Rect(-200, 1720, W + 200, H + 200), paint(INK))
    radio_waves(c, tx, ty - 50, t, color=INK, rmax=420)
    D.morse(c, tx + 20, ty - 40, 830, 1540 - 0.75 * 372, t, color=RED, speed=0.45)
    if u > 0.4:
        a = min(1.0, (u - 0.4) / 0.3)
        say(c, "1898", 830, 860, 104, alpha=a, halo=12)
        say(c, "≈ 4 km", 830, 930, 50, color=RED, alpha=a, halo=10)


def military(c, u, dur, ctx):
    t = ctx["t"]
    m, k = cam(u, dur, push=0.04)
    sky(c, "dusk")
    c.concat(m)
    skyline_hatch(c, 1600, 51, scale=0.8, gap=8, width=2.0)
    tower(c, 540, 1700, 1150, ink=True, antenna=True)
    radio_waves(c, 540, 1700 - 1150 - 60, t, color=RED, n=5, rmax=1100, period=2.0, width=7)
    skyline_ink(c, 1760, 52, windows=False)
    if u > 1.0:
        a = min(1.0, (u - 1.0) / 0.4)
        c.save(); c.translate(810, 560); c.scale(0.6 + 0.4 * a, 0.6 + 0.4 * a)
        globe(c, 0, 0, 150, t)
        c.restore()
        say(c, "6,000 km" if ctx["lang"] == "en" else "6.000 km", 810, 800, 70, alpha=a, halo=12)


def renewal(c, u, dur, ctx):
    t = ctx["t"]
    m, k = cam(u, dur, push=0.06)
    sky(c, "night")
    c.concat(m)
    stars(c, t)
    skyline_hatch(c, 1500, 11, scale=0.8)
    tower(c, 540, 1520, 1050)
    skyline_ink(c, 1660, 12)
    rubber(c, 540, 640, [(L(ctx, "EXPIRES", "SON TARİH"), 54), ("1909", 92)], -1.0, u, color=INK, w=440, h=190)
    if u > 0.5:
        f = D.ease((u - 0.5) / 0.25)
        c.drawLine(330, 560, 330 + 420 * f, 720, paint(RED, stroke=14))
    rubber(c, 540, 1040, [(L(ctx, "EXTENDED", "UZATILDI"), 66), ("1910", 112)], 0.9, u, angle=6)
    s14 = ctx["S"][14] - ctx["start"]
    if u > s14:
        a = min(1.0, (u - s14) / 0.25)
        say(c, L(ctx, "+70 YEARS", "+70 YIL"), 540, 1270, int(116 + 30 * (1 - a)), color=RED, alpha=a, halo=14)


def war(c, u, dur, ctx):
    t = ctx["t"]
    m, k = cam(u, dur, push=0.06)
    beams = []
    for i, ang in enumerate((-25, 18)):                           # projektörler: taramadan oyulmuş ışık
        a = ang + 8 * math.sin(t * 0.7 + i)
        p = skia.Path()
        p.moveTo(-10, 0); p.lineTo(-130, -1500); p.lineTo(130, -1500); p.lineTo(10, 0); p.close()
        mm = skia.Matrix()
        mm.setTranslate(200 + 680 * i, 1700)
        mm.preRotate(a)
        p.transform(mm)
        beams.append(p)
    holes = []
    for p in beams:
        q = skia.Path(p)
        q.transform(m)
        holes.append(q)
    sky(c, "war", holes=holes)
    c.concat(m)
    for p in beams:
        c.drawPath(p, paint(INK, stroke=1.6, alpha=0.6))
    skyline_hatch(c, 1600, 61, scale=0.8, gap=6, width=2.8)
    tower(c, 540, 1700, 1150, ink=True, antenna=True)
    top = (540, 1700 - 1150 - 50)
    for i, (sx, sy) in enumerate(((1100, 420), (1100, 900), (-20, 700))):
        D.morse(c, sx, sy, top[0], top[1], t + i * 0.3, color=RED, speed=0.5, alpha=0.95)
    skyline_ink(c, 1760, 62, windows=False)
    if u > 0.3:
        a = min(1.0, (u - 0.3) / 0.3)
        say(c, "1914 · MARNE", 540, 1225, 80, alpha=a, spacing=4, halo=14)


def today(c, u, dur, ctx):
    t = ctx["t"]
    m, k = cam(u, dur, push=-0.05)                                # son sahne: geri çekilir
    sky(c, "night", holes=[circle_hole(m, 230, 380, 52)])
    c.concat(m)
    moon(c, 230, 380, 40)
    stars(c, t, seed=5, avoid=(230, 380, 110))
    skyline_hatch(c, 1500, 71, scale=0.8)
    tower(c, 540, 1520, 1050)
    rng = random.Random(int(t * 10))                              # pırıltı: kırmızı yıldızcıklar
    for _ in range(14):
        f = rng.random() * 0.9
        w = float(np.interp(f, D._F, D._Wd)) * 1050
        star4(c, 540 + rng.uniform(-w, w), 1520 - f * 1050, rng.uniform(6, 12), paint(RED))
    skyline_ink(c, 1660, 72)
    radio_waves(c, 540, 1520 - 1050 - 55, t, color=RED, n=3, rmax=300, period=2.4, width=5)


SCENES = {"hook": hook, "place_card": place, "permit": permit_s, "newspaper": news, "science": science,
          "radio": radio, "military": military, "renewal": renewal, "war": war, "today": today}


# ---------------------------------------------------------------- kaplama: çerçeve, altyazı etiketi, jenerik
_frame = {}


def frame(c, ep, lang):
    """Pul penceresi + üst boşluk yazıları. Bir kez çizilip önbellekten basılır."""
    key = (ep["id"], lang)
    if key not in _frame:
        surf = skia.Surface(W, H)
        f = surf.getCanvas()
        f.clear(skia.Color4f(0, 0, 0, 0))
        p = paint(PAPER)
        for r in (skia.Rect(0, 0, W, WIN.top()), skia.Rect(0, 0, WIN.left(), H),
                  skia.Rect(WIN.right(), 0, W, H), skia.Rect(0, WIN.bottom(), W, H)):
            f.drawRect(r, p)
        f.drawRect(WIN, paint(INK, stroke=5))
        f.drawRect(skia.Rect(28, WIN.top() - 16, W - 28, H - 28), paint(INK, stroke=1.6))
        title = BRAND[lang]["badge"]
        tw = say(f, title, W / 2, 160, 46, spacing=7)
        for x0, x1 in ((44, W / 2 - tw / 2 - 24), (W / 2 + tw / 2 + 24, W - 44)):
            f.drawLine(x0, 143, x1, 143, paint(INK, stroke=2))
        pl = ep["place"]
        say(f, f"No. {ep.get('no', 1):03d}", 44, 80, 34, face=SMALL, align="left")
        say(f, f"{tr_upper(pl['city'], lang)} · {pl['year']}", W - 44, 80, 34, face=SMALL, align="right")
        _frame[key] = surf.makeImageSnapshot()
    c.drawImage(_frame[key], 0, 0)


def caption(c, ch, t, y=1440, size=66):
    """Kâğıt etiket altyazı: mürekkep yazı, söylenen kelime kırmızı, gelecek kelimeler soluk."""
    f = font(DISPLAY, size)
    toks = [w["w"] for w in ch["words"]]
    widths = [f.measureText(x) for x in toks]
    sp = f.measureText(" ")
    lines = [list(range(len(toks)))]
    if sum(widths) + sp * (len(toks) - 1) > 860 and len(toks) > 1:
        half = len(toks) // 2
        lines = [list(range(half)), list(range(half, len(toks)))]
    lw = [sum(widths[i] for i in idx) + sp * (len(idx) - 1) for idx in lines]
    bw, lh = max(lw) + 56, size * 1.18
    bh = lh * len(lines) + 34
    box = skia.Rect(W / 2 - bw / 2, y - bh / 2 - size * 0.32, W / 2 + bw / 2, y + bh / 2 - size * 0.32)
    c.drawRect(skia.Rect(box.left() + 9, box.top() + 11, box.right() + 9, box.bottom() + 11), paint(INK))
    c.drawRect(box, paint(PAPER))
    c.drawRect(box, paint(INK, stroke=3))
    for li, idx in enumerate(lines):
        x = W / 2 - lw[li] / 2
        yy = y + (li - (len(lines) - 1) / 2) * lh
        for i in idx:
            w = ch["words"][i]
            nxt = ch["words"][i + 1]["s"] if i + 1 < len(toks) else ch["e"]
            if w["s"] <= t < nxt:
                col, a = RED, 1.0
            elif w["s"] <= t:
                col, a = INK, 1.0
            else:
                col, a = INK, 0.35
            c.drawString(toks[i], x, yy, f, paint(col, alpha=a))
            x += widths[i] + sp


def overlay(c, t, fi, ctx):
    """Sahnelerin üstüne: gren, vinyet, çerçeve, jenerik damgası, altyazı."""
    style.grain(c, W, H, fi, alpha=0.10)
    style.vignette(c, W, H, 0.22)
    s1, ep, lang = ctx["s1"], ctx["ep"], ctx["lang"]
    pl = ep["place"]
    postmark(c, 400, 900, BRAND[lang]["badge"], tr_upper(pl["city"], lang), pl["year"], s1 - 0.35, t,
             bottom=f"No. {ep.get('no', 1):03d}")
    frame(c, ep, lang)
    for ch in ctx["caps"]:
        if ch["s"] <= t < ch["e"]:
            caption(c, ch, t)
            break


def sting_sfx(s1):
    return [(s1 - 0.35 + 0.12, "thud", 34, 1.0), (s1 - 0.35 + 0.12, "tick", 60, 0.8)]
