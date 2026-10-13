"""Eyfel pilotu sahneleri (Yol 2, kodla çizim). Her sahne: fn(c, u, dur, ctx) — u: sahne içi saniye.
ctx: {"t": küresel zaman, "lang", "S": cümle başlangıç zamanları listesi, "start": sahne başlangıcı}.
Derinlik: katmanlar kamera ilerlemesine göre farklı hızda kayar (2,5D his; araştırma: düz 2D Shorts'ta zayıf)."""
import math

import skia

from story import draw as D
from story.style import CREAM, INK, MUSTARD, RUST, TEAL, TERRA, paint, text, SANS_K, SANS_XB

W, H = D.W, D.H


def _cam(c, u, dur, push=0.07, rise=0.0):
    k = D.ease(u / max(dur, 0.1))
    s = 1 + push * k
    c.translate(W / 2, H / 2)
    c.scale(s, s)
    c.translate(-W / 2, -H / 2 - rise * k)
    return k


def L(ctx, en, tr):
    return en if ctx["lang"] == "en" else tr


def hook(c, u, dur, ctx):
    t = ctx["t"]
    D.sky(c, "night")
    k = _cam(c, u, dur, push=0.10)
    D.stars(c, t)
    D.moon(c, 820, 420 + 30 * k, 46)
    c.save(); c.translate(0, 20 * k); D.skyline(c, 1500, 11, "#26324F", "#1C2640", None, scale=0.8); c.restore()
    D.tower(c, 540, 1520, 1050, lit=True, t=t, sparkle=0.25)
    c.save(); c.translate(0, -25 * k); D.skyline(c, 1660, 12, "#151C2E", "#0F1524", "#2A3552", lit=0.25, t=t); c.restore()
    D.stamp(c, 540, 860, [(L(ctx, "EXPIRES", "SON TARİH"), 70), ("1909", 120)], 1.25, u)


def place(c, u, dur, ctx):
    t = ctx["t"]
    D.sky(c, "day")
    k = _cam(c, u, dur, push=0.06, rise=-40)
    D.clouds(c, t, 4, "#F4EAD6", n=4)
    c.save(); c.translate(-30 * k, 0); D.skyline(c, 1480, 21, "#C9B48F", "#A88F6C", None, scale=0.7); c.restore()
    D.tower(c, 540, 1560, 1100)
    D.bunting(c, -20, 1250, 1100, 1240, t)
    c.save(); c.translate(-80 * k, 0); D.skyline(c, 1700, 22, "#9E7F5E", "#7C6146", "#D8C29C", scale=1.0)
    D.crowd(c, 1730, t, n=36); c.restore()
    D.place_card(c, 540, 600, L(ctx, "Eiffel Tower", "Eyfel Kulesi"), L(ctx, "Paris · France", "Paris · Fransa"),
                 "1889", 0.55, u)


def permit(c, u, dur, ctx):
    t = ctx["t"]
    D.sky(c, "dusk")
    k = _cam(c, u, dur, push=0.05)
    fade = 1.0 - 0.65 * D.ease((u - 3.2) / 1.2)          # "yıkılması gerekiyordu": kule solar
    D.skyline(c, 1580, 31, "#3A2B3A", "#2A1F2C", None)
    D.tower(c, 820, 1640, 1050, color="#2A1F2C", alpha=fade)
    D.skyline(c, 1720, 32, "#22182A", "#170F1D", None, scale=1.1)
    D.permit(c, 470, 900, 0.15, u, lang=ctx["lang"])


def news(c, u, dur, ctx):
    c.drawRect(skia.Rect(0, 0, W, H), paint("#3A2E2A"))
    for i in range(14):                                       # masa ahşap çizgileri
        c.drawLine(0, 140 * i + 30, W, 140 * i + 60, paint("#2E2420", stroke=10, alpha=0.6))
    k = _cam(c, u, dur, push=0.08)
    D.newspaper(c, 540, 880, 0.1, u, lang=ctx["lang"])


def science(c, u, dur, ctx):
    t = ctx["t"]
    D.sky(c, "day")
    k = _cam(c, u, dur, push=0.05, rise=60)
    D.clouds(c, t, 8, "#F7EFDD", n=6, speed=70)
    D.tower(c, 540, 4100, 3600)                               # yakın plan: tepe görünür
    top_y = 4100 - 3600
    plat_y = 4100 - 0.85 * 3600
    D.anemometer(c, 640, plat_y - 20, 1.3, t)
    D.anemometer(c, 430, plat_y - 20, 0.9, t + 0.4)
    D.wind_lines(c, t, n=12)


def radio(c, u, dur, ctx):
    t = ctx["t"]
    D.sky(c, "day")
    k = _cam(c, u, dur, push=0.06)
    D.skyline(c, 1520, 41, "#C9B48F", "#A88F6C", None, scale=0.6)
    D.pantheon(c, 830, 1540, 0.75, "#8C7457", accent=CREAM)
    tx, ty = 300, 1650 - 1150
    D.tower(c, 300, 1650, 1150)
    D.skyline(c, 1720, 42, "#9E7F5E", "#7C6146", "#D8C29C", scale=0.9)
    D.radio_waves(c, tx, ty - 50, t, color=TERRA, rmax=420)
    D.morse(c, tx + 20, ty - 40, 830, 1540 - 0.75 * 372, t, color=INK, speed=0.45)
    if u > 0.4:
        a = min(1.0, (u - 0.4) / 0.3)
        text(c, "1898", 830, 860, 96, color=INK, face=SANS_K, alpha=a)
        text(c, L(ctx, "≈ 4 km", "≈ 4 km"), 830, 925, 44, color=RUST, face=SANS_XB, alpha=a)


def military(c, u, dur, ctx):
    t = ctx["t"]
    D.sky(c, "dusk")
    k = _cam(c, u, dur, push=0.04)
    D.skyline(c, 1600, 51, "#3A2B3A", "#2A1F2C", None, scale=0.8)
    D.tower(c, 540, 1700, 1150, color="#2A1F2C", antenna=True)
    D.radio_waves(c, 540, 1700 - 1150 - 60, t, color=MUSTARD, n=5, rmax=1100, period=2.0, width=8)
    D.skyline(c, 1760, 52, "#22182A", "#170F1D", None)
    if u > 1.0:
        a = min(1.0, (u - 1.0) / 0.4)
        c.save(); c.translate(810, 560); c.scale(0.6 + 0.4 * a, 0.6 + 0.4 * a)
        D.globe(c, 0, 0, 150, t)
        c.restore()
        text(c, "6,000 km" if ctx["lang"] == "en" else "6.000 km", 810, 790, 64, color=CREAM, face=SANS_K, alpha=a)


def renewal(c, u, dur, ctx):
    t = ctx["t"]
    D.sky(c, "night")
    k = _cam(c, u, dur, push=0.06)
    D.stars(c, t)
    D.skyline(c, 1500, 11, "#26324F", "#1C2640", None, scale=0.8)
    D.tower(c, 540, 1520, 1050, lit=True, t=t, sparkle=0.2)
    D.skyline(c, 1660, 12, "#151C2E", "#0F1524", "#2A3552", lit=0.25, t=t)
    D.stamp(c, 540, 760, [(L(ctx, "EXPIRES", "SON TARİH"), 70), ("1909", 120)], -1.0, u)   # eski damga duruyor
    if u > 0.5:                                                   # üstü çizilir
        f = D.ease((u - 0.5) / 0.25)
        c.drawLine(300, 660, 300 + 480 * f, 860, paint(INK, stroke=16))
    D.stamp(c, 540, 1000, [(L(ctx, "EXTENDED", "UZATILDI"), 66), ("1910", 112)], 0.9, u, color=TEAL, angle=6)
    s14 = ctx["S"][14] - ctx["start"]
    if u > s14:
        a = min(1.0, (u - s14) / 0.25)
        text(c, L(ctx, "+70 YEARS", "+70 YIL"), 540, 1260, int(110 + 30 * (1 - a)), color=MUSTARD, face=SANS_K, alpha=a)


def war(c, u, dur, ctx):
    t = ctx["t"]
    D.sky(c, "war")
    k = _cam(c, u, dur, push=0.06)
    for i, ang in enumerate((-25, 18)):                          # projektör ışıkları
        a = ang + 8 * math.sin(t * 0.7 + i)
        c.save(); c.translate(200 + 680 * i, 1700); c.rotate(a)
        p = skia.Path(); p.moveTo(-10, 0); p.lineTo(-120, -1500); p.lineTo(120, -1500); p.lineTo(10, 0); p.close()
        c.drawPath(p, paint(CREAM, alpha=0.08)); c.restore()
    D.skyline(c, 1600, 61, "#2A1A22", "#1C1117", None, scale=0.8)
    D.tower(c, 540, 1700, 1150, color="#1C1117", antenna=True)
    top = (540, 1700 - 1150 - 50)
    for i, (sx, sy) in enumerate(((1100, 420), (1100, 900), (-20, 700))):
        D.morse(c, sx, sy, top[0], top[1], t + i * 0.3, color=MUSTARD, speed=0.5, alpha=0.9)
    D.skyline(c, 1760, 62, "#170F14", "#0E090C", None)
    if u > 0.3:
        a = min(1.0, (u - 0.3) / 0.3)
        text(c, "1914 · MARNE", 540, 1290, 72, color=CREAM, face=SANS_K, alpha=a, spacing=4)


def today(c, u, dur, ctx):
    t = ctx["t"]
    D.sky(c, "night")
    k = _cam(c, u, dur, push=-0.05)                              # son sahne: geri çekilir
    D.stars(c, t)
    D.moon(c, 230, 380, 40)
    D.skyline(c, 1500, 71, "#26324F", "#1C2640", None, scale=0.8)
    D.tower(c, 540, 1520, 1050, lit=True, t=t, sparkle=0.6 + 0.4 * math.sin(t * 2))
    D.skyline(c, 1660, 72, "#151C2E", "#0F1524", "#2A3552", lit=0.35, t=t)
    D.radio_waves(c, 540, 1520 - 1050 - 55, t, color=MUSTARD, n=3, rmax=300, period=2.4, width=4)


SCENES = {"hook": hook, "place_card": place, "permit": permit, "newspaper": news, "science": science,
          "radio": radio, "military": military, "renewal": renewal, "war": war, "today": today}
