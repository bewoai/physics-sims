"""Seri tasarım dili: Siluet Sinema (kullanıcı seçti, 2026-10-13; seçenekler story/TASARIM.md).

Dil: katı nesneler karanlık siluet, duygu ışıktan gelir. Her sahnenin bir ışığı var (LIGHTS: gece ayı, altın
öğleden sonra, gün batımı, mavi saat, şafak, savaş). Işık kaynağı + huzmeler + sis katmanları (uzak katman sise
karışır) + ışıkta toz. Parlayan şeyler (telsiz dalgası, Mors, rakamlar) ışık rengiyle ve bloom'la.
Süs yok: çerçeve, rozet, numara, seri adı yok (kullanıcı: "No. 1 gibi klasik süs ekleme").
Yazılar yalnız story/safezone.SAFE içinde (x 92–920, y 285–1440); taşarsa küçültülür, en sonda assert ile denetlenir.
"""
import math
import random

import numpy as np
import skia

from story import draw as D
from story import music, style
from story.safezone import CX, SAFE
from story.style import C, linear, paint, radial, typeface

W, H = D.W, D.H
PLUS = skia.BlendMode.kPlus
AMBER = "#FFC46B"
BOLD, BLACK, SERIF = "Montserrat-800.ttf", "Montserrat-900.ttf", "PlayfairDisplay-700.ttf"

LIGHTS = {
    "night": dict(sky=["#060B18", "#0E2240", "#24506E", "#4E8396"], src="moon", glow="#CFEAF2", fog="#5C93A6",
                  layers=["#3D6C83", "#25485F", "#13293C"], fg="#03060D", stars=True, rays=0.07, dust="#E9F7FB",
                  warm=True),
    "golden": dict(sky=["#5E93B3", "#9DBFCB", "#EBCFA3", "#F4B877"], src="sun", glow="#FFE3B0", fog="#F1C795",
                   layers=["#B08A72", "#7F6253", "#4B3A33"], fg="#1E1614", stars=False, rays=0.06, dust="#FFF1D6",
                   warm=False),
    "dusk": dict(sky=["#170E2B", "#47213F", "#B24F48", "#F2A35A"], src="sun", glow="#FFC07A", fog="#D47A5A",
                 layers=["#8A4650", "#5A2C3C", "#2C1522"], fg="#10070C", stars=False, rays=0.08, dust="#FFD9A8",
                 warm=True),
    "blue": dict(sky=["#0A1230", "#1E3160", "#56699D", "#C496A6"], src=None, glow="#D9C7E6", fog="#8C8DB8",
                 layers=["#4E5888", "#313A64", "#1A2040"], fg="#070A18", stars=True, rays=0.0, dust="#E6E2F5",
                 warm=True),
    "day": dict(sky=["#3F86B8", "#7FB4D2", "#C9E0E6", "#EDE6CF"], src="sun", glow="#FFF6DC", fog="#DCE8EA",
                layers=["#93AAB4", "#677F8B", "#3B4C56"], fg="#16212A", stars=False, rays=0.05, dust="#FFFFFF",
                warm=False),
    "dawn": dict(sky=["#1A1838", "#583866", "#DD776A", "#FFD496"], src="sun", glow="#FFE2A8", fog="#EFA287",
                 layers=["#955668", "#643A54", "#311D33"], fg="#120A14", stars=True, rays=0.09, dust="#FFE8C8",
                 warm=True),
    "war": dict(sky=["#0A0507", "#2A0D10", "#6A1D14", "#C24E1D"], src=None, glow="#FF9A4A", fog="#7A2A1A",
                layers=["#4A1A14", "#2C0F0D", "#170807"], fg="#060203", stars=False, rays=0.0, dust="#FFB060",
                warm=True),
}


# ---------------------------------------------------------------- yardımcılar
def font(face, size):
    f = skia.Font(typeface(face), size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def blurp(sigma, color, alpha=1.0, blend=None):
    p = skia.Paint(AntiAlias=True, Color4f=C(color, alpha) if isinstance(color, str) else color,
                   MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma))
    if blend:
        p.setBlendMode(blend)
    return p


def mix(a, b, k):
    ca, cb = C(a), C(b)
    return skia.Color4f(ca.fR + (cb.fR - ca.fR) * k, ca.fG + (cb.fG - ca.fG) * k, ca.fB + (cb.fB - ca.fB) * k, 1.0)


def cam(c, u, dur, push=0.07, rise=0.0, cx=W / 2, cy=H / 2):
    k = D.ease(u / max(dur, 0.1))
    s = 1 + push * k
    c.translate(cx, cy)
    c.scale(s, s)
    c.translate(-cx, -cy - rise * k)
    return k


def L(ctx, en, tr):
    return en if ctx["lang"] == "en" else tr


def tr_upper(s, lang):
    return s.replace("i", "İ").replace("ı", "I").upper() if lang == "tr" else s.upper()


def appear(u, at, dur=0.35):
    return D.ease((u - at) / dur) if u >= at else 0.0


# ---------------------------------------------------------------- yazı (yalnız SAFE içinde)
_text_boxes = []          # QA: çizilen yazı kutuları (güvenli alan denetimi)


def _fit(s, face, size, spacing, max_w):
    f = font(face, size)
    w = f.measureText(s) + spacing * max(0, len(s) - 1)
    if w > max_w:
        k = max_w / w
        return _fit(s, face, size * k, spacing * k, max_w)
    return f, w, size, spacing


def text(c, s, x, y, size, color="#FFFFFF", face=BLACK, align="left", alpha=1.0, spacing=0.0, glow=None,
         shadow=True, max_w=None):
    """Ekran koordinatında yazı (kamera dönüşümü dışında çağrılır). SAFE'e sığmazsa küçülür."""
    if alpha <= 0.001:
        return 0
    lim = max_w or (SAFE.right() - x if align == "left" else SAFE.width())
    f, w, size, spacing = _fit(s, face, size, spacing, lim)
    x0 = x if align == "left" else (CX - w / 2 if align == "center" else x - w)
    _text_boxes.append((x0, y - size * 0.75, x0 + w, y + size * 0.22))

    def draw(p, dx=0.0, dy=0.0):
        xx = x0 + dx
        if spacing:
            for ch in s:
                c.drawString(ch, xx, y + dy, f, p)
                xx += f.measureText(ch) + spacing
        else:
            c.drawString(s, xx, y + dy, f, p)
    if shadow:
        draw(blurp(max(4, size * 0.08), "#000000", 0.7 * alpha), 2, size * 0.06)
    if glow:
        draw(blurp(max(8, size * 0.12), glow, 0.6 * alpha, PLUS))
    draw(paint(color, alpha=alpha))
    return w


def caption(c, ch, t, y=1392, size=66):
    """Kelime kelime altyazı: beyaz, söylenen kelime kehribar; SAFE genişliğine göre 1–2 satır."""
    f = font(BLACK, size)
    toks = [w["w"] for w in ch["words"]]
    sp = f.measureText(" ")
    widths = [f.measureText(x) for x in toks]
    maxw = SAFE.width() - 40
    lines = [list(range(len(toks)))]
    if sum(widths) + sp * (len(toks) - 1) > maxw and len(toks) > 1:
        half = (len(toks) + 1) // 2
        lines = [list(range(half)), list(range(half, len(toks)))]
    scale = 1.0
    for idx in lines:
        lw = sum(widths[i] for i in idx) + sp * (len(idx) - 1)
        scale = min(scale, maxw / lw)
    if scale < 1.0:
        return caption(c, ch, t, y, size * scale)
    lh = size * 1.18
    top_y = y - (len(lines) - 1) * lh - size * 0.8
    mw = max(sum(widths[i] for i in idx) + sp * (len(idx) - 1) for idx in lines)
    c.drawRoundRect(skia.Rect(CX - mw / 2 - 30, top_y - 10, CX + mw / 2 + 30, y + size * 0.35), 40, 40,
                    blurp(28, "#000000", 0.38))                   # yumuşak karartma: açık gökte okunurluk
    for li, idx in enumerate(lines):
        lw = sum(widths[i] for i in idx) + sp * (len(idx) - 1)
        x = CX - lw / 2
        yy = y - (len(lines) - 1 - li) * lh
        _text_boxes.append((x, yy - size * 0.75, x + lw, yy + size * 0.22))
        for i in idx:
            w = ch["words"][i]
            nxt = ch["words"][i + 1]["s"] if i + 1 < len(toks) else ch["e"]
            col = AMBER if w["s"] <= t < nxt else "#FFFFFF"
            a = 1.0 if w["s"] <= t else 0.55
            pop = 1.0 + 0.06 * max(0.0, 1 - (t - w["s"]) / 0.12) if w["s"] <= t else 1.0
            c.save()
            c.translate(x + widths[i] / 2, yy)
            c.scale(pop, pop)
            c.drawString(toks[i], -widths[i] / 2 + 2, size * 0.06, f, blurp(6, "#000000", 0.8 * a))
            c.drawString(toks[i], -widths[i] / 2, 0, f, paint(col, alpha=a))
            c.restore()
            x += widths[i] + sp


# ---------------------------------------------------------------- sahne zemini
def stage(c, L_, t, src_xy=None, src_r=200, layers_y=(1330, 1420, 1520), seeds=(21, 22, 23), scales=(0.55, 0.72, 0.9),
          drift=1.0, rays=True, pt=0.0):
    """Gökyüzü, ışık kaynağı, huzmeler, yıldız, sis + siluet katmanları (paralaks). Kamera dönüşümünden sonra çağrılır;
    gök gradyanı ekranı her koşulda kaplasın diye taşırılır."""
    c.drawRect(skia.Rect(-300, -300, W + 300, H + 300), linear(0, -100, 0, 1550, L_["sky"], [0.0, 0.42, 0.78, 1.0]))
    rng = random.Random(2)
    if src_xy:
        mx, my = src_xy
        c.drawCircle(mx, my, 1150, radial(mx, my, 1150, [C(L_["glow"], 0.45), C(L_["glow"], 0.12),
                                                          C(L_["glow"], 0.0)], [0.0, 0.32, 1.0]))
        if rays and L_["rays"] > 0:
            rp = blurp(16, L_["glow"], L_["rays"], PLUS)
            for _ in range(26):
                a = rng.uniform(0, 2 * math.pi) + 0.03 * t
                da = math.radians(rng.uniform(0.8, 2.6)) * (0.85 + 0.15 * math.sin(t * 0.9 + a * 3))
                Lr = rng.uniform(800, 1500)
                p = skia.Path()
                p.moveTo(mx, my)
                p.lineTo(mx + Lr * math.cos(a - da), my + Lr * math.sin(a - da))
                p.lineTo(mx + Lr * math.cos(a + da), my + Lr * math.sin(a + da))
                p.close()
                c.drawPath(p, rp)
    if L_["stars"]:
        srng = random.Random(7)
        for _ in range(70):
            x, y = srng.uniform(-40, W + 40), srng.uniform(60, 760)
            if src_xy and math.hypot(x - src_xy[0], y - src_xy[1]) < 480:
                continue
            r = srng.uniform(1.0, 2.6)
            tw = 0.55 + 0.45 * math.sin(t * srng.uniform(1.5, 4) + srng.uniform(0, 6))
            c.drawCircle(x, y, r * 3, blurp(4, L_["glow"], 0.35 * tw, PLUS))
            c.drawCircle(x, y, r, paint("#F2F8FB", alpha=0.9 * tw))
    if src_xy:
        mx, my = src_xy
        if L_["src"] == "moon":
            c.drawCircle(mx, my, src_r, radial(mx - 50, my - 60, src_r * 1.3, ["#FBFCF6", "#E3EEEA", "#C9DCDA"], [0, 0.6, 1]))
            for dx, dy, r in ((-60, -40, 38), (50, 30, 26), (-10, 90, 30), (80, -80, 18), (-100, 60, 16)):
                k = src_r / 215
                c.drawCircle(mx + dx * k, my + dy * k, r * k, paint("#9FB8B8", alpha=0.18))
        elif L_["src"] == "sun":
            c.drawCircle(mx, my, src_r * 1.25, blurp(src_r * 0.25, L_["glow"], 0.8))
            c.drawCircle(mx, my, src_r, radial(mx, my, src_r, ["#FFFDF4", L_["glow"]], [0.55, 1.0]))
    fog = L_["fog"]
    fa = (0.55, 0.45, 0.35)
    for li, (y, seed, sc) in enumerate(zip(layers_y, seeds, scales)):
        col = L_["layers"][li]
        c.save()
        c.translate(-(li + 1) * 6 * pt * drift, 0)                # pt: sahne içi zaman (küresel t ile kayıp gidiyordu)
        for dx in (-8, 8, 0):
            c.save()
            c.translate(dx, 0)
            D.skyline(c, y, seed, col, col, None, scale=sc, xmin=-400, xmax=W + 400)
            c.restore()
        c.restore()
        c.drawRect(skia.Rect(-300, y - 170, W + 300, y + 90),
                   linear(0, y - 170, 0, y + 90, [C(fog, 0.0), C(fog, fa[li]), C(fog, 0.0)], [0, 0.6, 1]))


def foreground(c, L_, t, y=1700, seed=24, scale=1.35, windows=True, drift=1.0, pt=0.0, buildings=True):
    c.save()
    c.translate(-30 * pt * drift, 0)
    for dx in ((-8, 8, 0) if buildings else ()):
        c.save()
        c.translate(dx, 0)
        D.skyline(c, y, seed, L_["fg"], L_["fg"], None, scale=scale, xmin=-400, xmax=W + 400)
        c.restore()
    c.drawRect(skia.Rect(-400, y, W + 400, H + 400), paint(L_["fg"]))
    if windows and L_["warm"] and buildings:
        rng = random.Random(seed)
        for _ in range(4):
            x, yy = rng.uniform(60, W - 60), rng.uniform(y - 170, y - 60)
            c.drawRect(skia.Rect(x, yy, x + 18, yy + 26), paint("#FFB65C"))
            c.drawCircle(x + 9, yy + 13, 60, blurp(30, "#FF9A3C", 0.45, PLUS))
    c.restore()


def dust(c, L_, t, center, n=90, spread=700, seed=3, up=9.0, side=14.0, pt=0.0):
    rng = random.Random(seed)
    mx, my = center
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0, spread)
        x = mx + d * math.cos(a) + side * pt * rng.uniform(0.5, 1.5)
        y = my + d * math.sin(a) * 1.4 - up * pt * rng.uniform(0.3, 1.2) + 6 * math.sin(t * 1.3 + d)
        r = rng.uniform(1.2, 3.2)
        c.drawCircle(x, y, r * 2.5, blurp(3, L_["dust"], 0.25, PLUS))


def low_fog(c, L_, y0=1380, y1=1760, a=0.22):
    fog = L_["fog"]
    c.drawRect(skia.Rect(-300, y0, W + 300, y1), linear(0, y0, 0, y1, [C(fog, 0.0), C(fog, a), C(fog, 0.0)]))


# ---------------------------------------------------------------- siluetler ve ışık nesneleri
def tower(c, x, y, h, L_, src=None, leak=1.0, alpha=1.0, antenna=False, color=None):
    """Kule silueti; ışık kaynağı yakınsa kafesten ışık sızar (radyal gradyan gölgelendirici)."""
    col = color or L_["fg"]
    tp = D.tower_path(x, y, h)
    c.drawPath(tp, paint(col, alpha=alpha))
    if src and leak > 0:
        c.save()
        c.clipPath(tp, doAntiAlias=True)
        lp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=max(1.6, h * 0.0028),
                        BlendMode=PLUS,
                        Shader=skia.GradientShader.MakeRadial(src, 460, [C(L_["glow"], 0.95 * leak * alpha).toColor(),
                                                                         C(L_["glow"], 0.35 * leak * alpha).toColor(),
                                                                         C(L_["glow"], 0.0).toColor()], [0, 0.55, 1]))
        k, step = -h, 0.022 * h
        while k < h:
            c.drawLine(x + k, y, x + k + h, y - h, lp)
            c.drawLine(x - k, y, x - k - h, y - h, lp)
            k += step
        c.restore()
    for f, extra in ((0.176, 1.18), (0.356, 1.22), (0.85, 1.6)):
        w = float(np.interp(f, D._F, D._Wd)) * h * extra
        c.drawRect(skia.Rect(x - w, y - f * h - h * 0.013, x + w, y - f * h + h * 0.003), paint(col, alpha=alpha))
    c.drawLine(x, y - h, x, y - h - 0.05 * h, paint(col, stroke=max(2.0, h * 0.006), alpha=alpha))
    if antenna:
        for dx in (-0.06, 0.06):
            c.drawLine(x, y - 1.05 * h, x + dx * h * 3, y - 0.2 * h, paint(col, stroke=2.0, alpha=0.8 * alpha))
    return (x, y - h)


def person(c, x, y, s, col, kind, t, seed):
    """Dönem siluetleri: silindir şapka / melon şapka / şemsiyeli kadın / bastonlu adam."""
    p = paint(col)
    bob = 1.5 * math.sin(t * 2.2 + seed)
    if kind == "lady":
        sk = skia.Path()
        sk.moveTo(x - 9 * s, y - 52 * s + bob)
        sk.lineTo(x + 9 * s, y - 52 * s + bob)
        sk.lineTo(x + 24 * s, y)
        sk.lineTo(x - 24 * s, y)
        sk.close()
        c.drawPath(sk, p)
        c.drawCircle(x, y - 62 * s + bob, 9 * s, p)
        c.drawLine(x + 6 * s, y - 50 * s, x + 26 * s, y - 92 * s + bob, paint(col, stroke=2.5 * s))
        um = skia.Path()
        um.addArc(skia.Rect(x + 2 * s, y - 112 * s + bob, x + 50 * s, y - 80 * s + bob), 180, 180)
        c.drawPath(um, p)
        return
    c.drawRoundRect(skia.Rect(x - 12 * s, y - 58 * s + bob, x + 12 * s, y - 20 * s + bob), 8 * s, 8 * s, p)
    c.drawRect(skia.Rect(x - 9 * s, y - 24 * s, x - 2 * s, y), p)
    c.drawRect(skia.Rect(x + 2 * s, y - 24 * s, x + 9 * s, y), p)
    c.drawCircle(x, y - 67 * s + bob, 9 * s, p)
    if kind == "top":
        c.drawRect(skia.Rect(x - 12 * s, y - 76 * s + bob, x + 12 * s, y - 73 * s + bob), p)
        c.drawRect(skia.Rect(x - 8 * s, y - 96 * s + bob, x + 8 * s, y - 74 * s + bob), p)
    else:
        bw = skia.Path()
        bw.addArc(skia.Rect(x - 10 * s, y - 84 * s + bob, x + 10 * s, y - 66 * s + bob), 180, 180)
        c.drawPath(bw, p)
        c.drawRect(skia.Rect(x - 13 * s, y - 76 * s + bob, x + 13 * s, y - 73 * s + bob), p)
    if kind == "cane":
        c.drawLine(x + 12 * s, y - 40 * s + bob, x + 20 * s, y, paint(col, stroke=2.5 * s))


def crowd(c, y, t, col, n=40, seed=9, x0=-40, x1=W + 40, scale=1.0):
    rng = random.Random(seed)
    kinds = ["top", "bowler", "lady", "cane", "bowler", "lady"]
    for i in range(n):
        person(c, rng.uniform(x0, x1), y + rng.uniform(-6, 10), rng.uniform(0.85, 1.15) * scale, col,
               rng.choice(kinds), t, i)


def bunting(c, x0, y0, x1, y1, t, col, sag=70, n=16):
    pts = []
    for i in range(n + 1):
        f = i / n
        pts.append((x0 + (x1 - x0) * f, y0 + (y1 - y0) * f + sag * 4 * f * (1 - f) + 6 * math.sin(t * 2 + f * 6)))
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        c.drawLine(ax, ay, bx, by, paint(col, stroke=2.5))
        tri = skia.Path()
        tri.moveTo(ax + 3, ay)
        tri.lineTo(bx - 3, by)
        tri.lineTo((ax + bx) / 2, (ay + by) / 2 + 36)
        tri.close()
        c.drawPath(tri, paint(col))


def lamp(c, x, y, h, col, warm="#FFB65C"):
    c.drawLine(x, y, x, y - h, paint(col, stroke=9))
    c.drawLine(x, y - h, x + 38, y - h - 8, paint(col, stroke=6))
    c.drawRect(skia.Rect(x + 24, y - h - 4, x + 54, y - h + 34), paint(col))
    c.drawRect(skia.Rect(x + 29, y - h + 2, x + 49, y - h + 28), paint(warm))
    c.drawCircle(x + 39, y - h + 15, 140, blurp(60, warm, 0.45, PLUS))


def glow_ring(c, x, y, r, col, a, w=4):
    c.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w * 4, BlendMode=PLUS,
                                     Color4f=C(col, 0.22 * a),
                                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)))
    c.drawCircle(x, y, r, paint(col, stroke=w, alpha=a))


def waves(c, x, y, t, col=AMBER, n=4, rmax=520, period=1.4, w=4):
    for k in range(n):
        ph = ((t / period) + k / n) % 1.0
        glow_ring(c, x, y, 20 + ph * rmax, col, (1 - ph) ** 1.3, w)


def morse(c, x0, y0, x1, y1, t, col=AMBER, speed=0.4, code="·−· ·− −·· ·· −−−"):
    syms = [ch for ch in code if ch in "·−"]
    Ln = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / Ln, (y1 - y0) / Ln
    for i, s in enumerate(syms):
        f = (t * speed - i * 0.07) % 1.0
        px, py = x0 + ux * f * Ln, y0 + uy * f * Ln
        a = math.sin(math.pi * f)
        c.drawCircle(px, py, 22, blurp(10, col, 0.6 * a, PLUS))
        if s == "·":
            c.drawCircle(px, py, 6, paint("#FFF4DA", alpha=a))
        else:
            c.drawLine(px - ux * 13, py - uy * 13, px + ux * 13, py + uy * 13, paint("#FFF4DA", stroke=9, alpha=a))


def globe(c, x, y, r, t, col="#9FD8FF", a=1.0):
    c.drawCircle(x, y, r * 1.2, blurp(30, col, 0.18 * a, PLUS))
    c.save()
    clip = skia.Path()
    clip.addCircle(x, y, r)
    c.clipPath(clip, doAntiAlias=True)
    for k in range(-3, 4):
        yy = y + k * r / 3.5
        hw = math.sqrt(max(0.0, r * r - (yy - y) ** 2))
        c.drawLine(x - hw, yy, x + hw, yy, paint(col, stroke=2, alpha=0.55 * a))
    for k in range(6):
        ph = (k / 6 + t * 0.05) % 1.0
        rx = abs(math.cos(ph * math.pi)) * r
        c.drawOval(skia.Rect(x - rx, y - r, x + rx, y + r), paint(col, stroke=2, alpha=0.55 * a))
    c.restore()
    glow_ring(c, x, y, r, col, a, 3)


def beam(c, x, y, ang, length, half_w, col, a):
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    p = skia.Path()
    p.moveTo(-6, 0)
    p.lineTo(-half_w, -length)
    p.lineTo(half_w, -length)
    p.lineTo(6, 0)
    p.close()
    sh = skia.GradientShader.MakeLinear([(0, 0), (0, -length)], [C(col, 0.30 * a).toColor(), C(col, 0.0).toColor()])
    c.drawPath(p, skia.Paint(AntiAlias=True, Shader=sh, BlendMode=PLUS,
                             MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)))
    c.restore()


def embers(c, t, n=60, seed=4, col="#FF9A4A"):
    rng = random.Random(seed)
    for _ in range(n):
        x0, sp = rng.uniform(-50, W + 50), rng.uniform(40, 120)
        y = (rng.uniform(0, H) - sp * t) % (H + 200) + 300
        x = x0 + 30 * math.sin(t * rng.uniform(0.5, 1.5) + x0)
        fl = 0.5 + 0.5 * math.sin(t * rng.uniform(4, 9) + x0)
        c.drawCircle(x, y, 7, blurp(4, col, 0.45 * fl, PLUS))
        c.drawCircle(x, y, 1.8, paint("#FFE2B0", alpha=0.9 * fl))


def anemometer(c, x, y, s, t, col):
    c.drawLine(x, y, x, y - 120 * s, paint(col, stroke=5 * s))
    for k in range(3):
        a = t * 7 + k * 2 * math.pi / 3
        ex, ey = x + math.cos(a) * 60 * s, y - 120 * s + math.sin(a) * 14 * s
        c.drawLine(x, y - 120 * s, ex, ey, paint(col, stroke=4 * s))
        c.drawCircle(ex, ey, 14 * s * (0.6 + 0.4 * abs(math.cos(a))), paint(col))


def wind(c, t, n=14, seed=4, col="#FFFFFF", a=0.5, y0=300, y1=1300):
    rng = random.Random(seed)
    for _ in range(n):
        y = rng.uniform(y0, y1)
        sp, Ln = rng.uniform(300, 500), rng.uniform(140, 300)
        x = (rng.uniform(0, W) + sp * t) % (W + 500) - 250
        p = skia.Path()
        p.moveTo(x, y)
        p.cubicTo(x + Ln * 0.3, y - 16, x + Ln * 0.6, y + 16, x + Ln, y)
        c.drawPath(p, paint(col, stroke=3.5, alpha=a))


def cloud(c, x, y, s, col, a=0.85):
    p = blurp(10 * s, col, a)
    for dx, dy, r in ((0, 0, 60), (55, -25, 70), (120, 0, 55), (60, 15, 60), (-50, 10, 45)):
        c.drawCircle(x + dx * s, y + dy * s, r * s, p)


# ---------------------------------------------------------------- sahneler: fn(c, u, dur, ctx) → kamera içi çizim;
# yazılar ctx["texts"] listesine eklenir, overlay ekran koordinatında çizer (kamera yazıyı büyütmesin, SAFE korunsun)
def _t(ctx, *a, **k):
    ctx["texts"].append((a, k))


def hook(c, u, dur, ctx):
    t, Lt = ctx["t"], LIGHTS["night"]
    cam(c, u, dur, push=0.10)
    src = (660, 720)
    stage(c, Lt, t, src, 215, pt=u)
    tower(c, 660, 1600, 1180, Lt, src)
    foreground(c, Lt, t, pt=u)
    dust(c, Lt, t, src, pt=u)
    low_fog(c, Lt)
    a = appear(u, 1.25, 0.3)
    _t(ctx, L(ctx, "EXPIRES", "SON TARİH"), SAFE.left(), 380, 40, "#DDEFF5", BOLD, alpha=0.9 * a, spacing=12)
    _t(ctx, "1909", SAFE.left() - 6, 560, 180 + 30 * (1 - a), "#F4FAFB", BLACK, alpha=a, glow="#BFE6F5")


def place(c, u, dur, ctx):
    t, Lt, lang = ctx["t"], LIGHTS["golden"], ctx["lang"]
    cam(c, u, dur, push=0.06, rise=-30)
    src = (870, 1000)
    stage(c, Lt, t, src, 120, pt=u)
    cloud(c, 160 + 12 * u, 760, 1.3, "#F7E7CC", 0.6)
    cloud(c, 760 + 8 * u, 330, 0.9, "#F7E7CC", 0.5)
    tower(c, 720, 1620, 1150, Lt, src, leak=0.7)
    bunting(c, -40, 1250, W + 40, 1235, t, Lt["fg"])
    foreground(c, Lt, t, y=1760, seed=25, scale=1.1, windows=False, pt=u)
    crowd(c, 1760, t, Lt["fg"], n=34, scale=1.25)
    dust(c, Lt, t, src, n=60, pt=u)
    a = appear(u, 0.4)
    _t(ctx, "1889", SAFE.left(), 380, 44, "#FFF6E6", BOLD, alpha=a, spacing=14)
    _t(ctx, tr_upper(ctx["place"]["city"], lang), SAFE.left() - 4, 520, 150, "#FFFFFF", BLACK, alpha=a, spacing=18)
    name = ctx["place"]["name"] if lang == "en" else ctx["place"].get("name_tr", ctx["place"]["name"])
    _t(ctx, name, SAFE.left(), 590, 44, AMBER, BOLD, alpha=appear(u, 0.9))


def permit(c, u, dur, ctx):
    t, Lt = ctx["t"], LIGHTS["dusk"]
    cam(c, u, dur, push=0.05)
    src = (540, 1240)
    stage(c, Lt, t, src, 210, pt=u)
    s4 = ctx["S"][4] - ctx["start"]                               # "1909'da yıkılması gerekiyordu"
    fade = 1.0 - 0.75 * D.ease((u - s4) / 1.4)
    tower(c, 540, 1620, 1150, Lt, src, alpha=fade)
    if u > s4:                                                    # kule tozlaşıp dağılır
        rng = random.Random(11)
        k = (u - s4)
        for _ in range(140):
            f = rng.random() * 0.95
            w = float(np.interp(f, D._F, D._Wd)) * 1150
            x = 540 + rng.uniform(-w, w) + k * rng.uniform(20, 90)
            y = 1620 - f * 1150 - k * rng.uniform(10, 60)
            c.drawCircle(x, y, rng.uniform(1.5, 4), paint(Lt["fg"], alpha=max(0.0, 1 - k / 2.5)))
    foreground(c, Lt, t, pt=u)
    dust(c, Lt, t, src, n=70, pt=u)
    a = appear(u, 0.3)
    _t(ctx, L(ctx, "PERMIT", "İZİN"), SAFE.left(), 380, 40, "#FFE9D2", BOLD, alpha=a, spacing=12)
    _t(ctx, L(ctx, "20 YEARS", "20 YIL"), SAFE.left() - 4, 540, 150, "#FFFFFF", BLACK, alpha=a, glow="#FFC07A")
    yr = int(round(1889 + 20 * D.ease((u - 0.8) / 2.2)))
    _t(ctx, f"1889 → {yr}", SAFE.left(), 630, 58, AMBER, BOLD, alpha=appear(u, 0.8))


def artists(c, u, dur, ctx):
    t, Lt = ctx["t"], LIGHTS["blue"]
    cam(c, u, dur, push=0.07)
    stage(c, Lt, t, None, pt=u)
    tower(c, 780, 1440, 760, Lt, color=Lt["layers"][1])          # uzakta, sisli
    low_fog(c, Lt, 1100, 1500, 0.35)
    foreground(c, Lt, t, y=1800, seed=26, scale=1.0, buildings=False, pt=u)
    lamp(c, 150, 1800, 520, Lt["fg"])
    for x, s, kind in ((330, 3.0, "top"), (560, 2.7, "lady"), (790, 3.2, "cane")):   # sanatçılar
        person(c, x, 1800, s, Lt["fg"], kind, t * 0.3, int(x))
    gx, gy = 345, 1800 - 3.0 * 58                                 # gazeteyi kaldıran el
    c.drawLine(gx + 30, gy + 30, gx + 70, gy - 70, paint(Lt["fg"], stroke=18))
    paper = skia.Rect(gx + 40, gy - 210, gx + 200, gy - 60)
    c.save()
    c.rotate(-6, gx + 120, gy - 135)
    c.drawRect(paper, paint("#F2E4C8", alpha=0.92))
    for i in range(7):
        c.drawLine(paper.left() + 14, paper.top() + 22 + i * 18, paper.right() - 14 - (i % 3) * 20,
                   paper.top() + 22 + i * 18, paint("#3A3346", stroke=5, alpha=0.5))
    c.drawRect(paper, blurp(18, "#FFE9C2", 0.35, PLUS))
    c.restore()
    s6 = ctx["S"][6] - ctx["start"]
    _t(ctx, "LE TEMPS · 1887", SAFE.left(), 380, 36, "#E6E2F5", BOLD, alpha=appear(u, 0.2), spacing=10)
    a = appear(u, s6 - 0.2)
    _t(ctx, "« INUTILE", SAFE.left(), 500, 84, "#FFFFFF", SERIF, alpha=a)
    _t(ctx, "ET MONSTRUEUSE »", SAFE.left(), 600, 84, "#FFFFFF", SERIF, alpha=a)
    _t(ctx, L(ctx, "useless and monstrous", "yararsız ve korkunç"), SAFE.left(), 670, 44, AMBER, BOLD,
       alpha=appear(u, s6 + 0.5))


def science(c, u, dur, ctx):
    t, Lt = ctx["t"], LIGHTS["day"]
    cam(c, u, dur, push=0.05, rise=60)
    src = (260, 560)
    c.drawRect(skia.Rect(-300, -300, W + 300, H + 300), linear(0, -100, 0, 1550, Lt["sky"], [0.0, 0.42, 0.78, 1.0]))
    c.drawCircle(src[0], src[1], 900, radial(src[0], src[1], 900, [C(Lt["glow"], 0.55), C(Lt["glow"], 0.0)]))
    c.drawCircle(src[0], src[1], 95, paint("#FFFDF2"))
    for i, (x, y, s) in enumerate(((100, 700, 1.6), (650, 520, 1.2), (900, 900, 1.8), (300, 1100, 1.4))):
        cloud(c, (x + 40 * t * (1 + i * 0.3)) % (W + 400) - 200, y, s, "#FFFFFF", 0.75)
    col = Lt["layers"][2]
    tower(c, 540, 4100, 3600, Lt, color=col)
    plat = 4100 - 0.85 * 3600
    anemometer(c, 680, plat - 20, 2.2, t, col)
    anemometer(c, 400, plat - 20, 1.6, t + 0.4, col)
    wind(c, t, a=0.55)
    D.birds(c, t, n=6, color=col, x0=200, y0=760, spread=260)


def radio(c, u, dur, ctx):
    t, Lt = ctx["t"], LIGHTS["blue"]
    cam(c, u, dur, push=0.06)
    stage(c, Lt, t, None, pt=u)
    D.pantheon(c, 800, 1530, 1.1, Lt["fg"])                        # kubbe: arka katmanla aynı renkteydi, kayboluyordu
    top = tower(c, 280, 1680, 1180, Lt)
    foreground(c, Lt, t, y=1760, seed=27, scale=1.0, pt=u)
    waves(c, top[0], top[1] - 40, t, AMBER, rmax=460)
    morse(c, top[0] + 20, top[1] - 30, 800, 1530 - 1.1 * 372, t, AMBER, speed=0.45)
    a = appear(u, 0.4)
    _t(ctx, "1898", 560, 520, 130, "#FFFFFF", BLACK, alpha=a, glow=AMBER)
    _t(ctx, "≈ 4 km", 566, 600, 54, AMBER, BOLD, alpha=a)


def military(c, u, dur, ctx):
    t, Lt = ctx["t"], LIGHTS["night"]
    cam(c, u, dur, push=0.04)
    stage(c, Lt, t, (200, 330), 56, rays=False, pt=u)
    top = tower(c, 540, 1700, 1150, Lt, antenna=True)
    waves(c, top[0], top[1] - 60, t, AMBER, n=5, rmax=1100, period=2.0, w=5)
    foreground(c, Lt, t, y=1780, seed=28, pt=u)
    a = appear(u, 1.0, 0.5)
    if a > 0:
        c.save()
        c.translate(720, 560)
        c.scale(0.6 + 0.4 * a, 0.6 + 0.4 * a)
        globe(c, 0, 0, 140, t, a=a)
        c.restore()
    _t(ctx, "6,000 km" if ctx["lang"] == "en" else "6.000 km", SAFE.left(), 900, 110, "#FFFFFF", BLACK, alpha=a,
       glow="#9FD8FF")


def renewal(c, u, dur, ctx):
    t, Lt = ctx["t"], LIGHTS["dawn"]
    cam(c, u, dur, push=0.06)
    rise = D.ease(u / max(dur, 0.1))
    src = (540, 1420 - 120 * rise)                                # güneş doğar
    stage(c, Lt, t, src, 240, pt=u)
    tower(c, 540, 1620, 1150, Lt, src)
    foreground(c, Lt, t, pt=u)
    dust(c, Lt, t, src, n=80, pt=u)
    a0 = appear(u, 0.2)
    _t(ctx, "1909", SAFE.left(), 380, 64, "#FFE8D8", BLACK, alpha=0.6 * a0)
    ctx["strike"] = (SAFE.left() - 6, 360, SAFE.left() + 160 * D.ease((u - 0.5) / 0.3), 360, a0) if u > 0.5 else None
    a1 = appear(u, 0.9)
    _t(ctx, L(ctx, "EXTENDED", "UZATILDI"), SAFE.left(), 460, 40, "#FFF0E0", BOLD, alpha=a1, spacing=12)
    _t(ctx, "1910", SAFE.left() - 6, 620, 170, "#FFFFFF", BLACK, alpha=a1, glow="#FFE2A8")
    s14 = ctx["S"][14] - ctx["start"]
    a2 = appear(u, s14, 0.3)
    _t(ctx, L(ctx, "+70 YEARS", "+70 YIL"), SAFE.left(), 760, 110 + 20 * (1 - a2), AMBER, BLACK, alpha=a2, glow=AMBER)


def war(c, u, dur, ctx):
    t, Lt = ctx["t"], LIGHTS["war"]
    cam(c, u, dur, push=0.06)
    stage(c, Lt, t, None, pt=u)
    c.drawRect(skia.Rect(-300, 1100, W + 300, 1600), linear(0, 1100, 0, 1600, [C("#FF7A2A", 0.0), C("#FF7A2A", 0.35)]))
    for i, (bx, base) in enumerate(((120, -20), (560, 15), (980, 30))):     # projektörler
        beam(c, bx, 1800, base + 18 * math.sin(t * 0.6 + i * 1.7), 1700, 150, "#FFE9C8", 1.0)
    top = tower(c, 540, 1700, 1150, Lt, antenna=True)
    for i, (sx, sy) in enumerate(((1100, 420), (1100, 900), (-20, 700))):
        morse(c, sx, sy, top[0], top[1] - 40, t + i * 0.3, "#FF5A3C", speed=0.5)
    foreground(c, Lt, t, y=1780, seed=29, windows=False, pt=u)
    embers(c, t)
    low_fog(c, Lt, 1300, 1760, 0.4)
    a = appear(u, 0.3)
    _t(ctx, "1914", SAFE.left() - 4, 520, 170, "#FFFFFF", BLACK, alpha=a, glow="#FF9A4A")
    _t(ctx, "MARNE", SAFE.left(), 600, 54, "#FFB27A", BOLD, alpha=a, spacing=14)


def today(c, u, dur, ctx):
    t, Lt = ctx["t"], LIGHTS["night"]
    cam(c, u, dur, push=-0.05)
    stage(c, Lt, t, (230, 400), 60, rays=False, pt=u)
    top = tower(c, 540, 1600, 1150, Lt)
    ang = t * 70                                                  # tepedeki fener: dönen ışık
    beam(c, top[0], top[1] - 30, ang % 360, 1100, 60, "#FFF2D0", 0.9)
    rng = random.Random(int(t * 12))                              # pırıltı: altın ışıklar
    for _ in range(60):
        f = rng.random() * 0.95
        w = float(np.interp(f, D._F, D._Wd)) * 1150
        x, y = 540 + rng.uniform(-w, w), 1600 - f * 1150
        c.drawCircle(x, y, 9, blurp(5, "#FFD58A", 0.6, PLUS))
        c.drawCircle(x, y, 2.4, paint("#FFF8E6"))
    foreground(c, Lt, t, pt=u)
    dust(c, Lt, t, (540, 900), n=60, pt=u)
    low_fog(c, Lt)


SCENES = {"hook": hook, "place_card": place, "permit": permit, "newspaper": artists, "science": science,
          "radio": radio, "military": military, "renewal": renewal, "war": war, "today": today}
WIN = None


def draw_texts(c, texts, strike=None, mul=1.0):
    for a, k in texts:
        if mul < 1.0:
            k = dict(k)
            k["alpha"] = k.get("alpha", 1.0) * mul
        text(c, *a, **k)
    if strike:
        x0, y, x1, _, al = strike
        c.drawLine(x0, y, x1, y, blurp(6, "#FF5A3C", 0.8 * al, PLUS))
        c.drawLine(x0, y, x1, y, paint("#FF5A3C", stroke=7, alpha=al))


def overlay(c, t, fi, ctx):
    style.grain(c, W, H, fi, alpha=0.05)
    style.vignette(c, W, H, 0.5)
    for ch in ctx["caps"]:
        if ch["s"] <= t < ch["e"]:
            caption(c, ch, t)
            break


def sfx(sc, s1):
    """Ses efektleri: kanca rakamı gümü, sahne geçişi hışırtısı (yumuşak), telsiz/savaşta Mors, uzatmada güm,
    sonda çan pırıltısı. Perde ve gazete şaplağı yok (klasik süs)."""
    seq_len = music.morse_seq()[1] + 0.3                          # Mors dizileri üst üste binmesin (~2,8 sn)
    out = [(sc[0]["start"] + 1.25, "thud", 34, 1.0)]
    for i, s in enumerate(sc[1:], 1):
        out.append((s["start"] - 0.1, "whoosh", 60, 1.0))
        if s["kind"] in ("radio", "war"):
            end = sc[i + 1]["start"] if i + 1 < len(sc) else s["start"] + 6
            k = 0
            while s["start"] + 0.5 + k * seq_len + seq_len < end:
                out.append((s["start"] + 0.5 + k * seq_len, "beepseq", 0, 1.0))
                k += 1
        if s["kind"] == "renewal":
            out.append((s["start"] + 0.9, "thud", 34, 1.0))
        if s["kind"] == "military":
            out.append((s["start"] + 1.0, "bell", 86, 1.0))
        if s["kind"] == "today":                                  # 4 çan birlikte çınlıyor: tek tek −6 dB
            out += [(s["start"] + 0.3 + 0.12 * q, "bell", m, 0.5) for q, m in enumerate((74, 78, 81, 86))]
    return out


def check_safe(boxes=None, margin=1.0):
    """Çizilen tüm yazı kutuları SAFE içinde mi? Döner: taşanlar listesi."""
    bad = []
    for x0, y0, x1, y1 in (boxes or _text_boxes):
        if x0 < SAFE.left() - 8 - margin or x1 > SAFE.right() + margin or y0 < SAFE.top() - margin or \
                y1 > SAFE.bottom() + margin:
            bad.append((round(x0), round(y0), round(x1), round(y1)))
    return bad
