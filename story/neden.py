""""Neden hep böyle?" serisi görsel modülü: Siluet Sinema dili + sevimli seri karakteri (story/karakter.py).

Kurallar: iç mekân, tek ışık kaynağı (lamba / pencere), karanlık siluet mobilya ve karakter, ışık tarafında kenar
parıltısı. Zemin çizgisi y = 1250: altyazı (y ≈ 1320–1400) zeminin koyu bölgesine düşer, karakterin yüzünü kapatmaz.
Üstte sabit soru başlığı (SAFE içinde). Yazılar yalnız SAFE içinde (siluet.text küçültür, check_safe denetler).
Süs yok (çerçeve, rozet, numara). Esprili anlar: kapının gözleri, dosyalanan düşünce, 3 m masa, yedek telefon.
"""
import math
import random

import numpy as np
import skia

from story import draw as D
from story import karakter as K
from story import maskot2 as M2
from story import music, style
from story.safezone import CX, SAFE
from story.siluet import (AMBER, BLACK, BOLD, PLUS, appear, blurp, caption, check_safe, draw_texts, font, text,  # noqa
                          _text_boxes)
from story.style import C, linear, paint, radial

W, H = D.W, D.H
FLOOR = 1250
INK = "#0A0D18"

ROOMS = {
    "living": dict(wall=["#1E1A2E", "#3A2C40", "#6B4A50"], floor=["#17111A", "#07060A"], light="#FFC27A", rim="#FFD9A0"),
    "kitchen": dict(wall=["#5E8C9A", "#A9C6C4", "#EAD8B4"], floor=["#3A3534", "#151214"], light="#FFF1D2", rim="#FFF6E2"),
    "bedroom": dict(wall=["#141933", "#2B2F58", "#8C5E78"], floor=["#100E1C", "#05050B"], light="#FFC9A0", rim="#FFD7B8"),
    "lab": dict(wall=["#0C1424", "#15233D", "#24395A"], floor=["#0A0F1C", "#04060C"], light="#9FD8FF", rim="#BFE6F5"),
}


def L(ctx, en, tr):
    return en if ctx["lang"] == "en" else tr


def _t(ctx, *a, **k):
    ctx["texts"].append((a, k))


def ease(x):
    return D.ease(x)


def zoom(c, z=1.25, cx=540):
    """Sahneyi zemin çizgisi etrafında büyütür (karakter telefonda küçük kalıyordu)."""
    c.translate(cx, FLOOR)
    c.scale(z, z)
    c.translate(-cx, -FLOOR)


def tick_mark(c, x, y, ok, s=1.0):
    """✓ / ✗ çizimi (yazı tipinde bu glifler yok, kutu çıkıyordu)."""
    col = "#7CFFA0" if ok else "#FF6B5C"
    c.drawCircle(x, y, 34 * s, blurp(14 * s, col, 0.4, PLUS))
    p = skia.Path()
    if ok:
        p.moveTo(x - 18 * s, y)
        p.lineTo(x - 4 * s, y + 15 * s)
        p.lineTo(x + 20 * s, y - 16 * s)
        c.drawPath(p, paint(col, stroke=9 * s))
    else:
        c.drawLine(x - 16 * s, y - 16 * s, x + 16 * s, y + 16 * s, paint(col, stroke=9 * s))
        c.drawLine(x + 16 * s, y - 16 * s, x - 16 * s, y + 16 * s, paint(col, stroke=9 * s))


# ---------------------------------------------------------------- mekân ve dekor
def room(c, kind, light_xy=None, light_r=700, x0=-400, x1=W + 400):
    R = ROOMS[kind]
    c.drawRect(skia.Rect(x0, -300, x1, FLOOR), linear(0, 0, 0, FLOOR, R["wall"], [0.0, 0.55, 1.0]))
    if light_xy:
        lx, ly = light_xy
        c.drawCircle(lx, ly, light_r, radial(lx, ly, light_r, [C(R["light"], 0.45), C(R["light"], 0.0)]))
    c.drawRect(skia.Rect(x0, FLOOR, x1, H + 300), linear(0, FLOOR, 0, H, R["floor"]))
    c.drawRect(skia.Rect(x0, FLOOR - 14, x1, FLOOR), paint(INK, alpha=0.85))         # süpürgelik
    if light_xy:                                                                   # zeminde ışık yansıması
        c.drawOval(skia.Rect(light_xy[0] - 380, FLOOR + 10, light_xy[0] + 380, FLOOR + 120),
                   blurp(40, R["light"], 0.12))


def window(c, x, y, w, h, sky, frame=INK, glow="#FFE2B0"):
    c.drawRect(skia.Rect(x - 40, y - 40, x + w + 40, y + h + 40), blurp(50, glow, 0.25, PLUS))
    c.drawRect(skia.Rect(x, y, x + w, y + h), linear(0, y, 0, y + h, sky))
    c.drawRect(skia.Rect(x, y, x + w, y + h), paint(frame, stroke=16))
    c.drawLine(x + w / 2, y, x + w / 2, y + h, paint(frame, stroke=10))
    c.drawLine(x, y + h / 2, x + w, y + h / 2, paint(frame, stroke=10))
    c.drawRect(skia.Rect(x - 30, y + h, x + w + 30, y + h + 18), paint(frame))


def doorway(c, x, w=250, h=600, inner=("#E9F2EE", "#B9D2CF"), col=INK):
    """Duvardaki kapı boşluğu: içi yan odanın ışığı, kasası siluet."""
    top = FLOOR - h
    c.drawRect(skia.Rect(x - w / 2, top, x + w / 2, FLOOR), linear(0, top, 0, FLOOR, list(inner)))
    c.drawRect(skia.Rect(x - w / 2 - 22, top - 22, x + w / 2 + 22, FLOOR), paint(col, stroke=28, cap=skia.Paint.kButt_Cap))


def door_leaf(c, x, w, h, open_k, col=INK, eyes=0.0, t=0.0, look=(0.0, 0.0), mood="smirk"):
    """Açık kapı kanadı (perspektifte daralır). eyes > 0: kapının gözleri açılır (seri esprisi)."""
    top = FLOOR - h
    ww = w * (1 - 0.72 * open_k)
    p = skia.Path()
    p.moveTo(x, top)
    p.lineTo(x + ww, top + 30 * open_k)
    p.lineTo(x + ww, FLOOR - 10 * open_k)
    p.lineTo(x, FLOOR)
    p.close()
    c.drawPath(p, paint(col))
    c.drawCircle(x + ww * 0.85, top + h * 0.55, 9, paint("#C9A26A"))
    if eyes > 0:
        ex, ey = x + ww * 0.5, top + h * 0.33
        blink = (t % 2.6) < 0.12
        for side in (-1, 1):
            K._eye(c, ex + side * 40, ey, 2.1 * eyes, "angry" if mood == "guilty" else "open", look, col, blink)
        mp = skia.Path()
        if mood == "smirk":
            mp.moveTo(ex - 40, ey + 84)
            mp.quadTo(ex + 8, ey + 112, ex + 50, ey + 74)
        else:
            mp.moveTo(ex - 34, ey + 96)
            mp.quadTo(ex, ey + 84, ex + 34, ey + 96)
        c.drawPath(mp, paint("#FFFFFF", stroke=7, alpha=eyes))


def sofa(c, x, s=1.0, col=INK):
    y = FLOOR
    c.drawRoundRect(skia.Rect(x - 190 * s, y - 230 * s, x + 190 * s, y - 120 * s), 40 * s, 40 * s, paint(col))
    c.drawRoundRect(skia.Rect(x - 230 * s, y - 150 * s, x + 230 * s, y - 40 * s), 30 * s, 30 * s, paint(col))
    for dx in (-200, 200):
        c.drawRoundRect(skia.Rect(x + dx * s - 30 * s, y - 180 * s, x + dx * s + 30 * s, y - 40 * s), 24 * s, 24 * s,
                        paint(col))
    for dx in (-180, 180):
        c.drawRect(skia.Rect(x + dx * s - 8 * s, y - 40 * s, x + dx * s + 8 * s, y), paint(col))


def floor_lamp(c, x, col=INK, warm="#FFB65C", h=520):
    c.drawLine(x, FLOOR, x, FLOOR - h, paint(col, stroke=10))
    c.drawOval(skia.Rect(x - 50, FLOOR - 16, x + 50, FLOOR + 4), paint(col))
    shade = skia.Path()
    shade.moveTo(x - 45, FLOOR - h - 20)
    shade.lineTo(x + 45, FLOOR - h - 20)
    shade.lineTo(x + 75, FLOOR - h + 70)
    shade.lineTo(x - 75, FLOOR - h + 70)
    shade.close()
    c.drawPath(shade, paint(col))
    c.drawOval(skia.Rect(x - 70, FLOOR - h + 60, x + 70, FLOOR - h + 84), paint(warm, alpha=0.9))
    c.drawCircle(x, FLOOR - h + 90, 260, blurp(90, warm, 0.35, PLUS))


def frame_pic(c, x, y, w, h, col=INK, inner="#C98B6A"):
    c.drawRect(skia.Rect(x, y, x + w, y + h), paint(col))
    c.drawRect(skia.Rect(x + 12, y + 12, x + w - 12, y + h - 12), paint(inner, alpha=0.5))


def table(c, x, w=420, h=300, col=INK, leg=16):
    top = FLOOR - h
    c.drawRoundRect(skia.Rect(x - w / 2, top - 24, x + w / 2, top), 6, 6, paint(col))
    for dx in (-w / 2 + 30, w / 2 - 30):
        c.drawRect(skia.Rect(x + dx - leg / 2, top, x + dx + leg / 2, FLOOR), paint(col))
    return top - 24


def toast(c, x, y, ang, s=1.0, butter_up=True, col="#3A2A1E", butter="#FFD45A", glow=0.0):
    """Ekmek dilimi (yan kesit + yüz): ang derece; tereyağı yüzü sarı şerit. butter_up: başlangıçta yağ yukarıda."""
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    w, h = 120 * s, 26 * s
    c.drawRoundRect(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), 10 * s, 10 * s, paint(col))
    c.drawRoundRect(skia.Rect(-w / 2 + 6 * s, -h / 2 + 5 * s, w / 2 - 6 * s, h / 2 - 5 * s), 8 * s, 8 * s,
                    paint("#C98B4E"))
    by = -h / 2 - 8 * s if butter_up else h / 2
    c.drawRoundRect(skia.Rect(-w / 2 + 8 * s, by, w / 2 - 8 * s, by + 9 * s), 4 * s, 4 * s, paint(butter))
    if glow > 0:
        c.drawRoundRect(skia.Rect(-w / 2, by - 10 * s, w / 2, by + 18 * s), 10 * s, 10 * s,
                        blurp(10 * s, butter, 0.8 * glow, PLUS))
    c.restore()


def splat(c, x, y, k, col="#FFD45A"):
    rng = random.Random(4)
    for _ in range(9):
        a = rng.uniform(math.pi, 2 * math.pi)
        d = (30 + rng.uniform(0, 50)) * k
        c.drawCircle(x + math.cos(a) * d, y + math.sin(a) * d * 0.5, rng.uniform(4, 9) * k, paint(col))


def bed(c, x, w=640, col=INK):
    y = FLOOR
    c.drawRoundRect(skia.Rect(x - w / 2, y - 210, x - w / 2 + 40, y), 16, 16, paint(col))      # başlık
    c.drawRect(skia.Rect(x - w / 2 - 10, y - 520, x - w / 2 + 40, y - 150), paint(col))
    c.drawRoundRect(skia.Rect(x - w / 2, y - 190, x + w / 2, y - 100), 20, 20, paint(col))      # şilte
    for dx in (-w / 2 + 20, w / 2 - 20):
        c.drawRect(skia.Rect(x + dx - 10, y - 100, x + dx + 10, y), paint(col))


def blanket(c, x, w, col="#1B1F36", rim="#FFD7B8", breathe=0.0):
    y = FLOOR - 190
    p = skia.Path()
    p.moveTo(x - w / 2 + 160, y - 40 - breathe)
    p.cubicTo(x - w / 2 + 300, y - 90 - breathe, x + w / 2 - 120, y - 70 - breathe * 0.5, x + w / 2 + 10, y - 20)
    p.lineTo(x + w / 2 + 10, y + 70)
    p.lineTo(x - w / 2 + 150, y + 70)
    p.close()
    c.save()
    c.translate(0, -3)
    c.drawPath(p, paint(rim, alpha=0.5))
    c.restore()
    c.drawPath(p, paint(col))


def phone(c, x, y, s, txt, glow=1.0, shake=0.0, face=None, t=0.0, screen="#9FD8FF"):
    c.save()
    c.translate(x + shake * math.sin(t * 90), y)
    c.rotate(shake * 4 * math.sin(t * 70))
    w, h = 90 * s, 170 * s
    c.drawRoundRect(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), 16 * s, 16 * s, paint(INK))
    c.drawRoundRect(skia.Rect(-w / 2 + 7 * s, -h / 2 + 12 * s, w / 2 - 7 * s, h / 2 - 12 * s), 9 * s, 9 * s,
                    paint(screen, alpha=0.25 + 0.6 * glow))
    c.drawRoundRect(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), 16 * s, 16 * s, blurp(18 * s, screen, 0.35 * glow, PLUS))
    if txt:
        f = font(BLACK, 30 * s)
        tw = f.measureText(txt)
        c.drawString(txt, -tw / 2, -10 * s, f, paint("#FFFFFF"))
    if face:                                       # telefonun yüzü (yedek esprisi)
        for side in (-1, 1):
            K._eye(c, side * 18 * s, 30 * s, 0.55 * s, "sleepy", (0, 0.6), "#284058", False)
        mp = skia.Path()
        mp.addArc(skia.Rect(-14 * s, 52 * s, 14 * s, 72 * s), 200, 140)
        c.drawPath(mp, paint("#FFFFFF", stroke=3 * s))
    c.restore()


def nightstand(c, x, col=INK):
    c.drawRect(skia.Rect(x - 80, FLOOR - 230, x + 80, FLOOR), paint(col))
    c.drawRect(skia.Rect(x - 95, FLOOR - 245, x + 95, FLOOR - 225), paint(col))
    return FLOOR - 245


def clapper(c, x, y, s, k, label, col=INK):
    """Film klaketi; k: 0 açık → 1 kapanmış."""
    c.save()
    c.translate(x, y)
    c.drawRoundRect(skia.Rect(-170 * s, -20 * s, 170 * s, 190 * s), 12 * s, 12 * s, paint(col))
    c.drawRoundRect(skia.Rect(-160 * s, -10 * s, 160 * s, 180 * s), 8 * s, 8 * s, paint("#F4F1EA", stroke=4 * s))
    f = font(BLACK, 62 * s)
    tw = f.measureText(label)
    c.drawString(label, -tw / 2, 110 * s, f, paint("#F4F1EA"))
    c.save()
    c.translate(-170 * s, -20 * s)
    c.rotate(-28 * (1 - k))
    c.drawRect(skia.Rect(0, -46 * s, 340 * s, 0), paint(col))
    for i in range(5):
        p = skia.Path()
        p.moveTo(20 * s + i * 66 * s, -46 * s)
        p.lineTo(52 * s + i * 66 * s, -46 * s)
        p.lineTo(32 * s + i * 66 * s, 0)
        p.lineTo(0 * s + i * 66 * s, 0)
        p.close()
        c.drawPath(p, paint("#F4F1EA"))
    c.restore()
    c.restore()


def cabinet(c, x, y, s, k, label, col=INK):
    """Dosya dolabı; k: çekmece açıklığı 0..1. Döner: çekmece ağzı merkezi."""
    c.drawRect(skia.Rect(x - 130 * s, y, x + 130 * s, y + 420 * s), paint(col))
    for i in range(3):
        yy = y + 20 * s + i * 135 * s
        dx = (90 * s * k) if i == 0 else 0
        c.drawRect(skia.Rect(x - 115 * s - dx, yy, x + 115 * s - dx, yy + 115 * s), paint("#232A40"))
        c.drawRoundRect(skia.Rect(x - 30 * s - dx, yy + 45 * s, x + 30 * s - dx, yy + 62 * s), 6, 6, paint("#C9A26A"))
    f = font(BOLD, 26 * s)
    tw = f.measureText(label)
    c.drawRect(skia.Rect(x - tw / 2 - 12 - 90 * s * k, y + 30 * s, x + tw / 2 + 12 - 90 * s * k, y + 64 * s),
               paint("#F4F1EA"))
    c.drawString(label, x - tw / 2 - 90 * s * k, y + 57 * s, f, paint(INK))
    return x - 90 * s * k, y + 20 * s


def keys_icon(c, x, y, s, col="#2B2F45"):
    c.drawCircle(x - 18 * s, y, 22 * s, paint(col, stroke=8 * s))
    c.drawLine(x + 2 * s, y, x + 52 * s, y, paint(col, stroke=9 * s))
    c.drawLine(x + 40 * s, y, x + 40 * s, y + 16 * s, paint(col, stroke=8 * s))
    c.drawLine(x + 52 * s, y, x + 52 * s, y + 12 * s, paint(col, stroke=8 * s))


def clock_icon(c, x, y, r, t, col="#2B2F45", speed=6.0):
    c.drawCircle(x, y, r, paint("#F4F1EA"))
    c.drawCircle(x, y, r, paint(col, stroke=r * 0.12))
    a1, a2 = t * speed, t * speed / 12
    c.drawLine(x, y, x + math.sin(a1) * r * 0.75, y - math.cos(a1) * r * 0.75, paint(col, stroke=r * 0.08))
    c.drawLine(x, y, x + math.sin(a2) * r * 0.5, y - math.cos(a2) * r * 0.5, paint(col, stroke=r * 0.12))
    for side in (-1, 1):                          # çalar saat çanları
        c.drawCircle(x + side * r * 0.7, y - r * 0.95, r * 0.3, paint(col))


def trophy(c, x, y, s, col=INK, glow="#FFD58A"):
    c.drawCircle(x, y - 120 * s, 170 * s, blurp(60 * s, glow, 0.45, PLUS))
    cup = skia.Path()
    cup.moveTo(x - 80 * s, y - 230 * s)
    cup.lineTo(x + 80 * s, y - 230 * s)
    cup.cubicTo(x + 80 * s, y - 120 * s, x + 30 * s, y - 90 * s, x, y - 90 * s)
    cup.cubicTo(x - 30 * s, y - 90 * s, x - 80 * s, y - 120 * s, x - 80 * s, y - 230 * s)
    c.drawPath(cup, paint(col))
    for side in (-1, 1):
        c.drawArc(skia.Rect(x + side * 80 * s - 30 * s, y - 220 * s, x + side * 80 * s + 30 * s, y - 150 * s),
                  -90 if side > 0 else 90, 180, False, paint(col, stroke=12 * s))
    c.drawRect(skia.Rect(x - 12 * s, y - 95 * s, x + 12 * s, y - 40 * s), paint(col))
    c.drawRect(skia.Rect(x - 60 * s, y - 40 * s, x + 60 * s, y), paint(col))


def bench(c, x, col=INK):
    c.drawRoundRect(skia.Rect(x - 260, FLOOR - 170, x + 260, FLOOR - 140), 10, 10, paint(col))
    for dx in (-220, 220):
        c.drawRect(skia.Rect(x + dx - 12, FLOOR - 140, x + dx + 12, FLOOR), paint(col))
    c.drawRect(skia.Rect(x - 260, FLOOR - 300, x + 260, FLOOR - 270), paint(col))
    for dx in (-220, 220):
        c.drawRect(skia.Rect(x + dx - 10, FLOOR - 300, x + dx + 10, FLOOR - 170), paint(col))


def ladder(c, x, y_top, col=INK, w=110):
    c.drawLine(x - w / 2, FLOOR, x - w / 2 + 20, y_top, paint(col, stroke=14))
    c.drawLine(x + w / 2, FLOOR, x + w / 2 - 20, y_top, paint(col, stroke=14))
    n = int((FLOOR - y_top) / 70)
    for i in range(1, n + 1):
        yy = FLOOR - i * 70
        f = (FLOOR - yy) / (FLOOR - y_top)
        c.drawLine(x - w / 2 + 20 * f, yy, x + w / 2 - 20 * f, yy, paint(col, stroke=10))


def rim(kind):
    return ROOMS[kind]["rim"]


def cat(c, x, y, s, t, **st):
    """Seri maskotu Mango (tekir kedi, story/maskot2.py). Zemin gölgesi + otomatik göz kırpma.
    Döner: {"head": (hx, hy, hr)} ekran koordinatı (balon / işaret yerleşimi için)."""
    jump = st.pop("jump", 0.0)
    if "blink" not in st:
        ph = (t + 0.37 * x / 100) % 3.3
        st["blink"] = math.sin(ph / 0.14 * math.pi) if ph < 0.14 else 0.0
    tilt = st.get("tilt", 0.0)
    if abs(tilt) < 30:
        c.drawOval(skia.Rect(x - 120 * s, y - 14 * s, x + 120 * s, y + 14 * s), paint("#000000", alpha=0.28))
    M2.mango(c, x, y - jump, s, t, st)
    r = math.radians(tilt)
    ox, oy = 0.0, -270 * s
    hx, hy = x + ox * math.cos(r) - oy * math.sin(r), y - jump + ox * math.sin(r) + oy * math.cos(r)
    return {"head": (hx, hy, 150 * s)}


def note(c, x, y, s=1.0, col="#FFFFFF", a=1.0):
    """♪ çizimi (yazı tipinde glif yok)."""
    c.drawOval(skia.Rect(x - 16 * s, y - 10 * s, x + 12 * s, y + 12 * s), paint(col, alpha=a))
    c.drawLine(x + 10 * s, y, x + 10 * s, y - 56 * s, paint(col, stroke=5 * s, alpha=a))
    c.drawLine(x + 10 * s, y - 56 * s, x + 30 * s, y - 40 * s, paint(col, stroke=5 * s, alpha=a))


# ---------------------------------------------------------------- BÖLÜM 1: kapı
def k_hook(c, u, dur, ctx):
    t = ctx["t"]
    zoom(c, 1.25)
    walk_t = min(u, 2.1)
    cx = 260 + 330 * walk_t                                       # karakterin dünya x'i
    pan = -min(420.0, max(0.0, cx - 540))
    c.translate(pan, 0)
    room(c, "living", (180, 640), 800, x0=-300, x1=780)
    c.save()
    c.clipRect(skia.Rect(780, -300, 2200, H + 300))
    room(c, "kitchen", (1300, 500), 900, x0=780, x1=2200)
    c.restore()
    floor_lamp(c, 120)
    frame_pic(c, 330, 560, 170, 130)
    doorway(c, 780, inner=("#FFF4DE", "#EAD8B4"))
    window(c, 1180, 520, 220, 280, ["#BFE0EC", "#F6E8C8"])
    table(c, 1380, w=300, h=280)
    walking = u < 2.1
    pose = {"walk": u * 7.5 if walking else None, "mood": "idle", "look": (0.8, 0.0)}
    if not walking:
        k = u - 2.1
        e = ease(k / 0.3)
        pose.update({"mood": "shock" if k < 0.5 else "confused", "derp": 0.0 if k < 0.5 else 0.85 * ease((k - 0.5) / 0.3),
                     "tilt": -10 * ease((k - 0.5) / 0.3), "look": (math.sin(k * 5) * (1 - e * 0.5), -0.2),
                     "arm_r": 150 if k > 0.6 else 25})
    h = cat(c, cx, FLOOR, 0.9, t, **pose)
    hx, hy, hr = h["head"]
    passed = cx > 800
    if not passed:                                                # düşünce balonu: anahtarlar
        bx, by = cx + 150, hy - 240
        K.bubble(c, bx, by, 0.9, tail_to=(hx + 40, hy - hr))
        keys_icon(c, bx - 20, by, 1.2)
    elif u < 1.9:                                                 # kapıdan geçince balon patlar
        k = (u - (800 - 260) / 330) / 0.25
        K.bubble(c, cx + 150, hy - 240, 0.9 * (1 + 0.5 * k), a=max(0.0, 1 - k))
    if not walking:
        K.mark(c, hx + 70, hy - hr - 40, 1.0, "?", bob=6 * math.sin(t * 6), a=appear(u, 2.2, 0.2))


def k_culprit(c, u, dur, ctx):
    t = ctx["t"]
    zoom(c, 1.2)
    s2 = ctx["S"][2] - ctx["start"]
    room(c, "kitchen", (900, 520), 900)
    doorway(c, 560, w=330, h=720, inner=("#FFE7C2", "#E6B98A"))
    door_leaf(c, 560 + 165, 330, 720, 0.55, eyes=appear(u, s2 - 0.1, 0.3), t=t,
              look=(-0.8, 0.1) if u < s2 + 0.8 else (-0.3, -0.6))
    h = cat(c, 200, FLOOR, 0.85, t, mood="annoyed" if u > s2 + 0.3 else "idle", look=(1, 0))
    if u > s2 + 0.2:                                              # kapının ağzından anahtar ucu
        a = appear(u, s2 + 0.2)
        keys_icon(c, 710, FLOOR - 720 * 0.36, 0.9 * a, "#E8E2D6")
    _t(ctx, L(ctx, "CULPRIT: THE DOOR", "SUÇLU: KAPI"), SAFE.left(), 520, 56, "#FFFFFF", BLACK,
       alpha=appear(u, s2), glow="#FF8A5C", spacing=2)


def _lane(c, y0, h, u, door, label, ok, ctx, t):
    c.drawRect(skia.Rect(0, y0, W, y0 + h), linear(0, y0, 0, y0 + h, ["#22324F", "#3B5576"]))
    c.drawRect(skia.Rect(0, y0 + h - 40, W, y0 + h), paint(INK))
    cyc = (u % 4.0) / 4.0
    cx = 140 + 760 * cyc
    if door:
        c.drawRect(skia.Rect(520, y0 + 40, 600, y0 + h - 40), paint("#E9F2EE", alpha=0.85))
        c.drawRect(skia.Rect(505, y0 + 25, 615, y0 + h - 40), paint(INK, stroke=16, cap=skia.Paint.kButt_Cap))
    s = 0.58
    hd = cat(c, cx, y0 + h - 40, 0.5, t, walk=u * 8, look=(0.8, 0),
             mood="confused" if (door and cx > 560) else "idle", derp=0.8 if (door and cx > 560) else 0.0)
    hx, hy, hr = hd["head"]
    lost = door and cx > 560
    if not lost:
        K.bubble(c, hx + 90, hy - 110, 0.42, tail_to=(hx + 30, hy - hr))
        keys_icon(c, hx + 82, hy - 110, 0.55)
    else:
        K.mark(c, hx + 70, hy - hr - 10, 0.6, "?")
    yl = y0 + 70
    _t(ctx, label, SAFE.left() + 10, yl, 40, "#FFFFFF", BOLD, spacing=3)
    tick_mark(c, SAFE.right() - 40, yl - 14, ok)


def k_study(c, u, dur, ctx):
    t = ctx["t"]
    room(c, "lab", None)
    _lane(c, 470, 360, u, False, L(ctx, "ONE ROOM", "TEK ODA"), True, ctx, t)
    _lane(c, 880, 360, u + 0.6, True, L(ctx, "THROUGH A DOOR", "KAPIDAN GEÇİNCE"), False, ctx, t)
    _t(ctx, "Notre Dame · 2011", SAFE.left(), 1300 - 60, 34, "#BFE6F5", BOLD, alpha=appear(u, 0.3), spacing=4)


def k_scene(c, u, dur, ctx):
    t = ctx["t"]
    zoom(c, 1.2)
    s5 = ctx["S"][5] - ctx["start"]
    room(c, "lab", (540, 700), 800)
    k = ease((u - 0.25) / 0.2)
    clapper(c, 330, 690, 1.0, k, L(ctx, "SCENE 2", "SAHNE 2") if u > 0.45 else L(ctx, "SCENE 1", "SAHNE 1"))
    dk = ease((u - s5 + 0.2) / 0.4) * (1 - ease((u - s5 - 1.6) / 0.4))
    mx, my = cabinet(c, 780, 760, 1.0, dk, L(ctx, "OLD SCENE", "ESKİ SAHNE"))
    hd = cat(c, 300, FLOOR, 0.85, t, mood="shock" if u > s5 else "idle",
             look=(1, -0.3) if u > s5 else (0.3, -0.8))
    fly = ease((u - s5) / 0.9)                                    # düşünce çekmeceye uçar
    if u < s5 + 1.0:
        hx, hy, hr = hd["head"]
        bx = hx + 200 + (mx - hx - 200) * fly
        by = hy - 230 + (my + 40 - hy + 230) * fly - math.sin(fly * math.pi) * 160
        sc = 0.8 * (1 - 0.6 * fly)
        K.bubble(c, bx, by, sc)
        keys_icon(c, bx - 16 * sc, by, 1.1 * sc)


def k_punch(c, u, dur, ctx):
    t = ctx["t"]
    zoom(c, 1.2)
    room(c, "kitchen", (900, 520), 900)
    doorway(c, 560, w=330, h=720, inner=("#FFE7C2", "#E6B98A"))
    look = (0.8, -0.7) if (u % 1.6) < 0.8 else (-0.2, -0.9)        # kapı ıslık çalar gibi yukarı bakar
    door_leaf(c, 560 + 165, 330, 720, 0.55, eyes=1.0, t=t, look=look, mood="guilty")
    cat(c, 200, FLOOR, 0.85, t, mood="annoyed", arm_r=95 + 6 * math.sin(t * 12), look=(1, 0),
        jump=10 * abs(math.sin(t * 6)))
    if u > 0.6:                                                   # kapı ıslık çalıyor
        a = appear(u, 0.6)
        note(c, 850, 620 + 10 * math.sin(t * 4), 1.0, a=a)
        note(c, 900, 560 + 10 * math.sin(t * 4 + 1), 0.8, a=a)


# ---------------------------------------------------------------- BÖLÜM 2: ekmek
def _fall(k, h0, rot_total, x0, slide=40):
    """Masadan düşen dilim: k 0..1, düşüş yüksekliği h0, toplam dönüş (derece)."""
    y = h0 * k * k
    return x0 + slide * k, y, rot_total * k


def e_hook(c, u, dur, ctx):
    t = ctx["t"]
    zoom(c, 1.25)
    room(c, "kitchen", (820, 520), 900)
    window(c, 640, 470, 260, 320, ["#FFE6B4", "#F6C98A"])
    top = table(c, 470, w=520, h=300)
    k_hit = 0.9
    fall_k = min(1.0, max(0.0, (u - k_hit) / 0.65))
    landed = u > k_hit + 0.65
    if u < k_hit:
        toast(c, 650, top - 18, 0, 1.0)
    elif not landed:
        dx, dy, rot = _fall(fall_k, FLOOR - top, 180, 700)
        toast(c, dx, top - 18 + dy, rot, 1.0)
    else:
        toast(c, 760, FLOOR - 14, 180, 1.0)
        splat(c, 760, FLOOR - 2, min(1.0, (u - k_hit - 0.65) / 0.15))
    arm = 60 + 50 * ease((u - k_hit + 0.25) / 0.25)               # dirsek çarpar
    cat(c, 290, FLOOR, 0.85, t, arm_r=arm, mood="shock" if landed else "idle",
        look=(0.9, 0.7) if u > k_hit else (0.5, 0), squash=0.92 if landed and u < k_hit + 0.9 else 1.0)


def e_physics(c, u, dur, ctx):
    t = ctx["t"]
    zoom(c, 1.1)
    s2 = ctx["S"][2] - ctx["start"]
    room(c, "lab", (540, 760), 700)
    top = table(c, 360, w=420, h=300, col="#0E1426")
    k = (u * 0.35) % 1.0                                          # ağır çekim tekrar
    dx, dy, rot = _fall(k, FLOOR - top, 180, 560)
    p = skia.Path()
    p.addArc(skia.Rect(520, top - 40, 760, FLOOR + 40), -80, 170)
    pe = paint("#9FD8FF", stroke=4, alpha=0.7)
    pe.setPathEffect(skia.DashPathEffect.Make([14, 10], 0))
    c.drawPath(p, pe)
    toast(c, dx, top - 18 + dy, rot, 1.3, glow=0.6)
    _t(ctx, f"{int(rot)}°", 760, 800, 70, "#FFFFFF", BLACK, glow="#9FD8FF")
    _t(ctx, L(ctx, "PHYSICS", "FİZİK"), SAFE.left(), 560, 120, "#FFFFFF", BLACK, alpha=appear(u, s2 - 0.1),
       glow="#9FD8FF", spacing=4)


def e_turn(c, u, dur, ctx):
    t = ctx["t"]
    zoom(c, 1.1)
    S, st = ctx["S"], ctx["start"]
    s4, s5, s6 = S[4] - st, S[5] - st, S[6] - st
    room(c, "lab", (540, 760), 700)
    top = table(c, 300, w=380, h=300, col="#0E1426")
    hgt = FLOOR - top
    c.drawLine(140, top, 140, FLOOR, paint("#BFE6F5", stroke=3))  # 75 cm ölçüsü
    for yy in (top, FLOOR):
        c.drawLine(120, yy, 160, yy, paint("#BFE6F5", stroke=3))
    _t(ctx, "75 cm", SAFE.left() + 4, 470, 44, "#BFE6F5", BOLD)
    n = 6
    reveal = min(n, int(max(0.0, u - 0.3) / 0.35) + 1)
    for i in range(reveal):                                       # hayalet kareler: yarım tur
        k = i / (n - 1)
        dx, dy, rot = _fall(k, hgt, 180, 520, slide=260)
        toast(c, dx, top - 18 + dy, rot, 1.1, glow=1.0 if (u > s5 and i == 0) or (u > s6 and i == n - 1) else 0.0)
    _t(ctx, L(ctx, "≈ ½ TURN", "≈ ½ TUR"), 560, 560, 90, AMBER, BLACK, alpha=appear(u, s4), glow=AMBER)
    if u > s5:
        _t(ctx, L(ctx, "BUTTER ↑", "YAĞ ↑"), 560, 660, 54, "#FFFFFF", BOLD, alpha=appear(u, s5))
    if u > s6:
        _t(ctx, L(ctx, "BUTTER ↓", "YAĞ ↓"), 560, 730, 54, "#FF8A5C", BOLD, alpha=appear(u, s6))


def e_matthews(c, u, dur, ctx):
    t = ctx["t"]
    zoom(c, 1.2)
    room(c, "living", (540, 640), 800)
    trophy(c, 700, 1060, 1.3)
    clap = abs(math.sin(t * 9))
    cat(c, 300, FLOOR, 0.85, t, mood="happy", arm_l=60 + 70 * clap, arm_r=60 + 70 * clap,
        jump=8 * clap)
    _t(ctx, "Robert Matthews · 1995", SAFE.left(), 500, 48, "#FFFFFF", BLACK, alpha=appear(u, 0.2))
    _t(ctx, "Ig Nobel", SAFE.left(), 570, 44, AMBER, BOLD, alpha=appear(u, 0.5), spacing=4)


def e_punch(c, u, dur, ctx):
    t = ctx["t"]
    zoom(c, 0.55)                                                 # 3 m masanın tamamı kadraja girsin
    room(c, "kitchen", (820, 300), 1100, x0=-600, x1=W + 600)
    c.drawRect(skia.Rect(-600, -1200, W + 600, 0), linear(0, -1200, 0, 0, ["#4E7C8A", "#5E8C9A"]))
    top = FLOOR - 1080                                            # 3 m masa (ölçek: 75 cm = 300 px → 3 m ≈ 1200)
    c.drawRect(skia.Rect(380, top - 24, 900, top), paint(INK))
    for dx in (410, 870):
        c.drawRect(skia.Rect(dx - 9, top, dx + 9, FLOOR), paint(INK))
    ladder(c, 300, top - 40)
    cat(c, 300, top - 40, 0.95, t, mood="happy" if u > 2.0 else "idle", look=(0.8, 0.6),
        jump=12 * abs(math.sin(t * 7)) if u > 2.0 else 0.0)
    fk = min(1.0, max(0.0, (u - 0.4) / 1.4))
    if fk < 1.0:
        dx, dy, rot = _fall(fk, FLOOR - top, 360, 700, slide=120)
        toast(c, dx, top - 18 + dy, rot, 1.0)
    else:
        toast(c, 820, FLOOR - 14, 0, 1.0, glow=1.0)
    c.drawLine(980, top, 980, FLOOR, paint("#FFFFFF", stroke=3, alpha=0.8))
    _t(ctx, "3 m", 700, 1180, 110, "#FFFFFF", BLACK, glow=AMBER, alpha=appear(u, 0.3))


# ---------------------------------------------------------------- BÖLÜM 3: alarm
def _bedroom(c, t, dawn=0.5):
    room(c, "bedroom", (860, 620), 820)
    window(c, 720, 470, 240, 320, ["#3A3A6E", "#D98A7A" if dawn > 0.3 else "#3A3A6E", "#FFD6A0"])
    bed(c, 420, w=620)
    ny = nightstand(c, 860)
    return ny


def a_hook(c, u, dur, ctx):
    t = ctx["t"]
    zoom(c, 1.2)
    ny = _bedroom(c, t)
    awake = u > 1.1
    ring = u > 2.3
    hx, hy = 250, FLOOR - 240                                     # yastıktaki kafa (kedi yan yatıyor)
    cat(c, hx + 270 * 0.72, hy, 0.72, t, tilt=-88, mood=("annoyed" if ring else "shock") if awake else "sleepy",
        blink=0.0 if awake else 1.0, look=(0.3, -1) if awake else (0, 0))
    blanket(c, 420, 620, breathe=0 if awake else 6 * math.sin(t * 2.2))
    txt = "07:00" if ring else "06:58"
    phone(c, 860, ny - 90, 1.0, txt, glow=1.0 if ring else 0.35, shake=4.0 if ring else 0.0, t=t)
    if not awake:
        for i in range(3):
            ph = (t * 0.6 + i / 3) % 1.0
            K.mark(c, hx + 140 + ph * 90, hy - 160 - ph * 200, 0.4 + 0.3 * ph, "Z", a=math.sin(ph * math.pi))


def a_inside(c, u, dur, ctx):
    t = ctx["t"]
    room(c, "bedroom", (540, 700), 800)
    s_ = 2.2                                                      # yakın plan Mango: alnında röntgen penceresi
    cat(c, 540, 860 + 270 * s_, s_, t, mood="sleepy", blink=1.0)
    hx, hy = 540, 860 - 150
    c.drawCircle(hx, hy, 150, paint("#0E1428"))
    c.drawCircle(hx, hy, 150, paint("#BFE6F5", stroke=8, alpha=0.8))
    clock_icon(c, hx, hy + 8, 92, t, speed=3.0)
    c.drawCircle(hx, hy, 175, blurp(40, "#9FD8FF", 0.25 + 0.15 * math.sin(t * 6), PLUS))


def a_study(c, u, dur, ctx):
    t = ctx["t"]
    s3 = ctx["S"][3] - ctx["start"]
    room(c, "lab", None)
    x0, y0, w, h = 150, 600, 760, 560                             # grafik: saat → hormon
    c.drawLine(x0, y0 + h, x0 + w, y0 + h, paint("#BFE6F5", stroke=4))
    c.drawLine(x0, y0, x0, y0 + h, paint("#BFE6F5", stroke=4))
    wake_x = x0 + w * 0.85
    c.drawLine(wake_x, y0, wake_x, y0 + h, paint(AMBER, stroke=3, alpha=0.8))
    clock_icon(c, wake_x, y0 - 40, 40, t * 0.2, speed=0.0)
    prog = ease((u - s3 + 0.3) / 2.2)
    pts = []
    for i in range(101):
        f = i / 100
        if f > prog:
            break
        x = x0 + f * w
        rise = 1 / (1 + math.exp(-(f - 0.55) * 14))               # bir saat önceden yükselir
        pts.append((x, y0 + h - 60 - rise * (h - 140) + 6 * math.sin(f * 40)))
    if len(pts) > 1:
        p = skia.Path()
        p.moveTo(*pts[0])
        for q in pts[1:]:
            p.lineTo(*q)
        c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=16, BlendMode=PLUS,
                                 Color4f=C("#9FD8FF", 0.3), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8)))
        c.drawPath(p, paint("#E8F6FF", stroke=6))
    one_h = x0 + w * 0.5
    if prog > 0.5:
        c.drawLine(one_h, y0 + h - 20, wake_x, y0 + h - 20, paint(AMBER, stroke=4))
    _t(ctx, "Lübeck · 1999", SAFE.left(), 470, 40, "#BFE6F5", BOLD, alpha=appear(u, 0.2), spacing=3)
    _t(ctx, L(ctx, "WAKE-UP", "UYANMA"), 690, 560, 40, AMBER, BOLD, alpha=appear(u, 0.4))
    _t(ctx, L(ctx, "−1 hour", "−1 saat"), 470, 1100, 44, AMBER, BOLD, alpha=appear(u, s3 + 1.2))
    _t(ctx, L(ctx, "hormone ↑", "hormon ↑"), SAFE.left() + 20, 720, 44, "#FFFFFF", BOLD, alpha=appear(u, s3 + 1.6))


def a_brain(c, u, dur, ctx):
    t = ctx["t"]
    zoom(c, 1.2)
    _bedroom(c, t, dawn=0.0)
    cat(c, 250 + 270 * 0.72, FLOOR - 240, 0.72, t, tilt=-88, mood="sleepy", blink=1.0)
    blanket(c, 420, 620, breathe=6 * math.sin(t * 2.2))
    bx, by = 580, 740
    K.bubble(c, bx, by, 1.1, tail_to=(330, 1000))
    clock_icon(c, bx, by + 4, 70, t, speed=8.0)


def a_punch(c, u, dur, ctx):
    t = ctx["t"]
    zoom(c, 1.2)
    s6 = ctx["S"][6] - ctx["start"]
    room(c, "living", (540, 640), 800)
    if u < s6 - 0.1:                                              # asıl alarm sensin: kafada çanlar
        ring = math.sin(t * 40) * 6
        hd = cat(c, 540, FLOOR, 1.15, t, mood="happy", jump=10 * abs(math.sin(t * 8)))
        hx, hy, hr = hd["head"]
        for side in (-1, 1):                                      # kulak uçlarında çalar saat çanları
            bx, by = hx + side * 150 * 1.15 + ring * side, hy - 205 * 1.15
            c.drawCircle(bx, by, 60, blurp(18, AMBER, 0.6, PLUS))
            c.drawArc(skia.Rect(bx - 48, by - 48, bx + 48, by + 48), 180, 180, True, paint("#E8B04B"))
            c.drawCircle(bx, by + 2, 11, paint("#8C5A1E"))
        _t(ctx, "RRRİNG!" if ctx["lang"] == "tr" else "RRRING!", SAFE.left(), 520, 90, AMBER, BLACK, glow=AMBER)
    else:                                                         # telefon yedek kulübesinde
        bench(c, 540)
        phone(c, 540, FLOOR - 330, 2.2, None, glow=0.4, face=True, t=t)
        _t(ctx, L(ctx, "BACKUP", "YEDEK"), CX, 560, 110, "#FFFFFF", BLACK, align="center", glow="#9FD8FF",
           alpha=appear(u, s6), spacing=6)


SCENES = {"k_hook": k_hook, "k_culprit": k_culprit, "k_study": k_study, "k_scene": k_scene, "k_punch": k_punch,
          "e_hook": e_hook, "e_physics": e_physics, "e_turn": e_turn, "e_matthews": e_matthews, "e_punch": e_punch,
          "a_hook": a_hook, "a_inside": a_inside, "a_study": a_study, "a_brain": a_brain, "a_punch": a_punch}
WIN = None


def overlay(c, t, fi, ctx):
    style.grain(c, W, H, fi, alpha=0.04)
    style.vignette(c, W, H, 0.35)
    title = ctx["ep"][ctx["lang"]].get("title_top")               # sabit soru başlığı: kaydırırken bağlam
    if title:
        c.drawRect(skia.Rect(0, 230, W, 520), linear(0, 230, 0, 520, [C("#000000", 0.0), C("#000000", 0.42),
                                                                       C("#000000", 0.0)], [0.0, 0.45, 1.0]))
        f = font(BLACK, 54)
        words, lines, cur = title.split(), [], ""
        for w_ in words:
            trial = (cur + " " + w_).strip()
            if f.measureText(trial) > SAFE.width() - 20 and cur:
                lines.append(cur)
                cur = w_
            else:
                cur = trial
        lines.append(cur)
        for i, ln in enumerate(lines):
            text(c, ln, CX, 350 + i * 64, 54, "#FFFFFF", BLACK, align="center")
    for ch in ctx["caps"]:
        if ch["s"] <= t < ch["e"]:
            caption(c, ch, t)
            break


def sfx(sc, s1):
    """Efektler (seviye music.SFX_DB'den): balon patlaması, klaket, ekmek düşüşü, alarm, geçiş hışırtısı."""
    out = []
    kinds = {s["kind"]: s for s in sc}
    for s in sc[1:]:
        out.append((s["start"] - 0.1, "whoosh", 60, 1.0))
    if "k_hook" in kinds:
        out.append((kinds["k_hook"]["start"] + (800 - 260) / 330 + 0.05, "pop", 76, 1.0))
    if "k_scene" in kinds:
        out.append((kinds["k_scene"]["start"] + 0.45, "tick", 70, 1.0))
        out.append((kinds["k_scene"]["start"] + 0.45, "thud", 40, 0.6))
    if "e_hook" in kinds:
        out.append((kinds["e_hook"]["start"] + 0.9 + 0.65, "thud", 46, 1.0))
    if "e_punch" in kinds:
        out.append((kinds["e_punch"]["start"] + 1.8, "bell", 84, 1.0))
    if "a_hook" in kinds:
        st = kinds["a_hook"]["start"]
        out += [(st + 2.3 + 0.18 * q, "bell", 88 if q % 2 == 0 else 84, 0.8) for q in range(6)]
    if "a_punch" in kinds:
        st = kinds["a_punch"]["start"]
        out += [(st + 0.2 + 0.15 * q, "bell", 86 if q % 2 == 0 else 81, 0.6) for q in range(5)]
    return out
