"""Galton tahtası — "400 balls. Will they make a bell curve?"

Toplar tüpten üçgen çivi dizisine düşer; her çivide sağa ya da sola sekerek iner, alttaki bölmelerde
çan eğrisi oluşur. Sonda normal dağılım eğrisi çizilir (ödül). Her top düşerken **varacağı bölmenin
rengiyle** çizilir: renkler düşüş sırasında ayrışır, sonunda gökkuşağı bir çan eğrisi çıkar.

Kinematik: her çivide sol/sağ seçimi (p=0,5) + çividen çiviye parabolik sekme. pymunk ile denendi,
çan çıkmadı (CONTEXT.md §3): toplar hızlanıp çapraz kanallardan kaydı, dağılım düz/iki tepeli oldu,
güçlü sönümde bölmeler taştı. Gerçek tahtada çiviler sık olduğu için top hızlanamaz; kinematik bunu birebir verir.

  python3 formats/galton.py --out out/galton
"""
import argparse
import math
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import audio, canvas, produce  # noqa: E402
from lib.canvas import FPS, W  # noqa: E402

N_BALLS, POUR_T, CURVE_T, HOLD = 400, 13.0, 1.0, 2.3
ROWS, DX, DY = 12, 40, 34
BALL_R, PEG_R = 6.0, 5.5
CX, TUBE_Y0, PEG_Y0 = W / 2, 600, 720
BIN_TOP, FLOOR = 1150, 1490
HOP_T = 0.14          # çividen çiviye süre (± titreşim)
COLS_IN_BIN = 3
G = 2200.0


def peg_xy(j, k):
    return CX + (k - j / 2) * DX, PEG_Y0 + j * DY


def bin_center(m):
    return CX + (m - ROWS / 2) * DX


def plan(seed=5):
    """Her top için (zaman, x, y) anahtar noktaları; bölmede varış sırasına göre dizilir."""
    rng = random.Random(seed)
    balls = []
    for i in range(N_BALLS):
        t = POUR_T * i / N_BALLS + rng.uniform(0, 0.01)
        k = 0
        keys = [(t, CX + rng.uniform(-3, 3), TUBE_Y0)]
        x0, y0 = peg_xy(0, 0)
        y_top = y0 - (BALL_R + PEG_R)
        t += math.sqrt(2 * (y_top - TUBE_Y0) / G)
        keys.append((t, x0, y_top))
        hits = [(t, 0, 0)]
        for j in range(1, ROWS):
            k += 1 if rng.random() < 0.5 else 0
            x, y = peg_xy(j, k)
            t += HOP_T * rng.uniform(0.85, 1.15)
            keys.append((t, x, y - (BALL_R + PEG_R)))
            hits.append((t, j, k))
        k += 1 if rng.random() < 0.5 else 0
        balls.append({"keys": keys, "hits": hits, "bin": k, "t_exit": t})
    fill = [0] * (ROWS + 1)
    for i in sorted(range(N_BALLS), key=lambda i: balls[i]["t_exit"]):
        b = balls[i]
        q = fill[b["bin"]]
        fill[b["bin"]] += 1
        col, row = q % COLS_IN_BIN, q // COLS_IN_BIN
        bx = bin_center(b["bin"]) + (col - 1) * (2 * BALL_R + 0.8) + (BALL_R * 0.5 if row % 2 else 0)
        by = FLOOR - BALL_R - 1 - row * (2 * BALL_R * 0.9)
        y_exit = b["keys"][-1][2]
        t_land = b["t_exit"] + 0.06 + math.sqrt(2 * max(1.0, by - y_exit) / G)
        b["keys"].append((t_land, bx, by))
        b["land"] = t_land
    return balls, fill


def pos_at(b, t):
    keys = b["keys"]
    if t < keys[0][0]:
        return None
    if t >= keys[-1][0]:
        return keys[-1][1], keys[-1][2]
    for n, ((t0, x0, y0), (t1, x1, y1)) in enumerate(zip(keys, keys[1:])):
        if t0 <= t < t1:
            s = (t - t0) / (t1 - t0)
            if n == 0 or n == len(keys) - 2:              # tüpten düşüş / bölmeye düşüş: ivmeli
                return x0 + (x1 - x0) * s, y0 + (y1 - y0) * s * s
            hop = 40 * s * (1 - s)                          # çividen küçük sekme
            return x0 + (x1 - x0) * s, y0 + (y1 - y0) * s * s - hop
    return keys[-1][1], keys[-1][2]


def events(balls):
    ev = []
    for b in balls:
        for t, j, k in b["hits"]:
            x, _ = peg_xy(j, k)
            ev.append((t, "pluck", audio.scale_note(int((x - 280) / 520 * 12), base=67), 0.22, (x - CX) / 450, 0))
        ev.append((b["land"], "tick", 60, 0.25, (b["keys"][-1][1] - CX) / 450, b["bin"]))
    t_c = max(b["land"] for b in balls) + 0.4
    ev += [(t_c + 0.05 * q, "bell", m, 0.4, 0, 0) for q, m in enumerate((67, 71, 74, 79))]
    return ev, t_c


def render(balls, fill, t_curve, out_dir, hook=None):
    import skia
    from lib.canvas import paint, hsv
    from lib.hud import hud
    hook = hook or f"{N_BALLS} balls. Will they make a bell curve?"
    os.makedirs(out_dir, exist_ok=True)
    vid = os.path.join(out_dir, "video.mp4")
    rd = canvas.Renderer(vid, glow=0.5, glow_sigma=10)
    nb = ROWS + 1
    cols = [paint(hsv(0.85 * m / (nb - 1), 0.75, 1.0)) for m in range(nb)]
    peg_p = paint(skia.Color4f(0.85, 0.9, 1.0, 0.9))
    wall_p = paint(skia.Color4f(0.85, 0.9, 1.0, 0.55), stroke=4)
    # normal eğri: Binom(ROWS, 0.5) → σ = DX·√ROWS/2; tepe yüksekliği en dolu bölmeye göre
    xs = np.linspace(bin_center(0) - DX / 2, bin_center(nb - 1) + DX / 2, 200)
    sd = DX * math.sqrt(ROWS) / 2
    peak_h = max(fill) / COLS_IN_BIN * 2 * BALL_R * 0.9 + BALL_R
    ys = FLOOR - peak_h * np.exp(-0.5 * ((xs - CX) / sd) ** 2)
    total = t_curve + CURVE_T + HOLD
    edges = [bin_center(m) - DX / 2 for m in range(nb)] + [bin_center(nb - 1) + DX / 2]
    for fi in range(int(total * FPS)):
        t = fi / FPS

        def draw(c):
            c.drawLine(CX - 16, TUBE_Y0 - 120, CX - 16, TUBE_Y0 + 40, wall_p)
            c.drawLine(CX + 16, TUBE_Y0 - 120, CX + 16, TUBE_Y0 + 40, wall_p)
            for j in range(ROWS):
                for k in range(j + 1):
                    c.drawCircle(*peg_xy(j, k), PEG_R, peg_p)
            for x in edges:
                c.drawLine(x, BIN_TOP, x, FLOOR, wall_p)
            c.drawLine(edges[0], FLOOR + 2, edges[-1], FLOOR + 2, wall_p)
            for b in balls:
                p = pos_at(b, t)
                if p is not None:
                    c.drawCircle(p[0], p[1], BALL_R, cols[b["bin"]])
            if t >= t_curve:
                k = min(1.0, (t - t_curve) / CURVE_T)
                m = max(2, int(len(xs) * k))
                path = skia.Path()
                path.moveTo(float(xs[0]), float(ys[0]))
                for q in range(1, m):
                    path.lineTo(float(xs[q]), float(ys[q]))
                c.drawPath(path, paint(skia.Color4f(1, 1, 1, 0.95), stroke=6))

        def overlay(c):
            if t >= t_curve:
                hud(c, hook, "YES", None, pop=max(0, 1 - (t - t_curve) / 0.3), big_size=130)
            else:
                hud(c, hook, sum(1 for b in balls if b["keys"][0][0] <= t), "BALLS")

        rd.frame(draw, overlay)
    rd.close()
    return vid, total


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out/galton")
    a = ap.parse_args()
    clk = produce.Clock()
    balls, fill = plan()
    print("bölmeler", fill, flush=True)
    ev, t_curve = events(balls)
    vid, secs = render(balls, fill, t_curve, a.out)
    produce.finish(a.out, vid, ev, secs, cap=5)
    print("süre", clk)
