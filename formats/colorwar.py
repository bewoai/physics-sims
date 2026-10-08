"""Renk savaşı — "4 colors. Only 1 survives."

24×24 kare ızgara 4 renge bölünmüş, her rengin bir topu var. Top kendi renginde serbest gezer, başka renkte
bir kareye çarpınca onu kendi rengine çevirir ve seker (Pong Wars kuralı). Saf Pong Wars çok dengeli
(36 sn'de payler %22–29 arasında kaldı, hiç eleme yok). Ek kurallar: **büyük bölge = hızlı top** ve bölge payı
büyüdükçe **renk yeni top kazanır** → kartopu, renkler tek tek elenir. Üstte canlı bölge çubuğu.

Fizik motoru gerekmez; ızgara çarpışması doğrudan hesaplanır.

  python3 formats/colorwar.py --search 40
  python3 formats/colorwar.py --seed 3 --out out/colorwar
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

G, CELL = 24, 36
X0, Y0 = (W - G * CELL) / 2, 600
BALL_R, SUB = 11, 8
V0 = 1250
ELIM_CELLS = 16                    # bunun altına düşen renk elenir (yoksa 10-15 karelik cepte sonsuza dek yaşıyor)
START_BALLS, STEP = 2, 0.02       # bölge payı %25'i her %2 aştığında renk +1 top kazanır (kartopu)
HUES = [0.0, 0.13, 0.36, 0.6]          # kırmızı, sarı, yeşil, mavi
NAMES = ["RED", "YELLOW", "GREEN", "BLUE"]
NOTES = [60, 64, 67, 71]
DIRS = [(math.cos(a), math.sin(a)) for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)]


class Sim:
    def __init__(self, seed):
        rng = random.Random(seed)
        self.grid = np.zeros((G, G), np.int8)
        h = G // 2
        self.grid[:h, :h], self.grid[:h, h:], self.grid[h:, :h], self.grid[h:, h:] = 0, 1, 2, 3
        self.rng = rng
        self.balls = []
        for c, (qi, qj) in enumerate([(0, 0), (0, 1), (1, 0), (1, 1)]):
            for _ in range(START_BALLS):
                x = X0 + (qj * h + h / 2) * CELL + rng.uniform(-90, 90)
                y = Y0 + (qi * h + h / 2) * CELL + rng.uniform(-90, 90)
                self._add(c, x, y)
        self.t = 0.0
        self.events = []
        self.dead = {}        # renk → elenme zamanı
        self.flips = 0

    def _add(self, c, x, y):
        a = self.rng.uniform(0, 2 * math.pi)
        if abs(math.cos(a)) < 0.25 or abs(math.sin(a)) < 0.25:
            a += 0.6
        self.balls.append({"c": c, "x": x, "y": y, "vx": math.cos(a), "vy": math.sin(a), "alive": True})

    def counts(self):
        return np.bincount(self.grid.ravel(), minlength=4)

    def step_frame(self):
        dt = 1 / FPS / SUB
        cnt = self.counts()
        for _ in range(SUB):
            for b in self.balls:
                if not b["alive"]:
                    continue
                share = cnt[b["c"]] / (G * G)
                sp = V0 * (0.6 + 1.6 * share)                # büyük bölge = hızlı top
                b["x"] += b["vx"] * sp * dt
                b["y"] += b["vy"] * sp * dt
                fx = fy = False
                for dx, dy in DIRS:
                    px, py = b["x"] + dx * BALL_R, b["y"] + dy * BALL_R
                    j, i = int((px - X0) // CELL), int((py - Y0) // CELL)
                    if 0 <= i < G and 0 <= j < G and self.grid[i, j] != b["c"]:
                        old = self.grid[i, j]
                        self.grid[i, j] = b["c"]
                        cnt[old] -= 1
                        cnt[b["c"]] += 1
                        self.flips += 1
                        self.events.append((self.t, "pluck", NOTES[b["c"]] + 12 * (self.flips % 2), 0.22,
                                            (px - W / 2) / 450, 0))
                        if abs(dx) > abs(dy):
                            fx = True
                        else:
                            fy = True
                if fx:
                    b["vx"] = -b["vx"]
                if fy:
                    b["vy"] = -b["vy"]
                if b["x"] - BALL_R < X0:
                    b["vx"] = abs(b["vx"])
                if b["x"] + BALL_R > X0 + G * CELL:
                    b["vx"] = -abs(b["vx"])
                if b["y"] - BALL_R < Y0:
                    b["vy"] = abs(b["vy"])
                if b["y"] + BALL_R > Y0 + G * CELL:
                    b["vy"] = -abs(b["vy"])
            self.t += dt
            for col in range(4):
                if col in self.dead or cnt[col] >= ELIM_CELLS or len(self.dead) >= 3:
                    continue
                self.dead[col] = self.t
                lead = int(np.argmax([cnt[k] if k not in self.dead else -1 for k in range(4)]))
                m = self.grid == col
                cnt[lead] += int(m.sum())
                cnt[col] = 0
                self.grid[m] = lead
                for b in self.balls:
                    if b["c"] == col and b["alive"]:
                        b["alive"] = False
                        b["dt"] = self.t
                self.events.append((self.t, "shatter", 60, 0.7, 0, col))
                self.events.append((self.t, "bell", NOTES[col] - 12, 0.5, 0, 0))
        # kartopu: pay arttıkça yeni top
        for col in range(4):
            if col in self.dead:
                continue
            mine = [b for b in self.balls if b["c"] == col and b["alive"]]
            target = START_BALLS + int(max(0.0, cnt[col] / (G * G) - 0.25) / STEP)
            if mine and len(mine) < target:
                src = mine[len(self.balls) % len(mine)]
                self._add(col, src["x"], src["y"])
                self.events.append((self.t, "pop", NOTES[col] + 12, 0.4, (src["x"] - W / 2) / 450, 0))

    def alive(self):
        return sorted({b["c"] for b in self.balls if b["alive"]})


def simulate(seed, max_t=40.0, tail=2.2):
    sim = Sim(seed)
    frames = []
    end_t = None
    while sim.t < max_t:
        sim.step_frame()
        frames.append((sim.t, sim.grid.copy(), [(b["x"], b["y"], b["c"], b["alive"], b.get("dt")) for b in sim.balls]))
        if len(sim.alive()) == 1 and end_t is None:
            end_t = sim.t
        if end_t is not None and sim.t - end_t > tail:
            break
    return sim, frames, end_t


def _score(seed):
    sim, fr, end_t = simulate(seed, max_t=36)
    ts = sorted(sim.dead.values())
    return seed, end_t, ts


def search(n, lo=20, hi=33):
    from multiprocessing import Pool
    with Pool(4) as p:
        res = p.map(_score, range(n))
    good = []
    for s, e, ts in res:
        if e and lo <= e <= hi:
            # elenmeler yayılmış olsun: ilk elenme 8 sn'den önce değil, aralar dengeli
            good.append((abs(ts[0] - e / 3) + abs(ts[1] - 2 * e / 3), s, e, ts))
    good.sort()
    for g, s, e, ts in good[:8]:
        print(f"seed={s} süre={e:.1f} elenmeler={[round(x, 1) for x in ts]}")
    if not good:
        print("uygun yok:", [(s, e and round(e, 1), len(ts)) for s, e, ts in res][:12])


def render(sim, frames, end_t, out_dir, hook="4 colors. Only 1 survives."):
    import skia
    from lib.canvas import paint, hsv, text
    from lib.hud import HOOK_Y
    os.makedirs(out_dir, exist_ok=True)
    vid = os.path.join(out_dir, "video.mp4")
    rd = canvas.Renderer(vid, glow=0.35, glow_sigma=10)
    cell_p = [paint(hsv(h, 0.72, 0.62)) for h in HUES]
    ball_p = [paint(hsv(h, 0.55, 1.0)) for h in HUES]
    bar_p = [paint(hsv(h, 0.75, 0.95)) for h in HUES]
    edge = paint(skia.Color4f(1, 1, 1, 0.95), stroke=4)
    winner = sim.alive()[0] if end_t else None
    for t, grid, balls in frames:
        cnt = np.bincount(grid.ravel(), minlength=4)

        def draw(c):
            for i in range(G):
                for j in range(G):
                    c.drawRect(skia.Rect(X0 + j * CELL, Y0 + i * CELL, X0 + (j + 1) * CELL - 1, Y0 + (i + 1) * CELL - 1),
                               cell_p[grid[i, j]])
            for x, y, col, alive, tdead in balls:
                if alive:
                    c.drawCircle(x, y, BALL_R + 3, paint(skia.Color4f(1, 1, 1, 1)))
                    c.drawCircle(x, y, BALL_R, ball_p[col])
                else:
                    k = (t - tdead) / 0.6
                    if k < 1:
                        c.drawCircle(x, y, BALL_R + 80 * k, paint(hsv(HUES[col], 0.5, 1, 1 - k), stroke=5))

        def overlay(c):
            text(c, hook, W / 2, HOOK_Y, size=60, weight=800, max_w=W - 140)
            bx0, bx1, by0, by1 = X0, X0 + G * CELL, 400, 450
            x = bx0
            for col in range(4):
                w = (bx1 - bx0) * cnt[col] / (G * G)
                if w > 0:
                    c.drawRect(skia.Rect(x, by0, x + w, by1), bar_p[col])
                    if w > 90:
                        text(c, f"{round(100 * cnt[col] / (G * G))}%", x + w / 2, by1 - 10, size=34, weight=800,
                             shadow=False)
                x += w
            c.drawRect(skia.Rect(bx0, by0, bx1, by1), paint(skia.Color4f(1, 1, 1, 0.8), stroke=3))
            if winner is not None and t >= end_t:
                k = min(1.0, (t - end_t) / 0.3)
                text(c, f"{NAMES[winner]} WINS", W / 2, 540, size=int(84 + 20 * (1 - k)), weight=900,
                     color=skia.Color4f(1, 1, 1, k))
            else:
                text(c, f"{len({b[2] for b in balls if b[3]})} COLORS LEFT", W / 2, 540, size=50, weight=900)

        rd.frame(draw, overlay)
    rd.close()
    return vid, frames[-1][0]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--search", type=int)
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.search:
        search(a.search)
        sys.exit()
    clk = produce.Clock()
    sim, frames, end_t = simulate(a.seed)
    print(f"bitiş={end_t} elenmeler={sim.dead} çevirme={sim.flips}", flush=True)
    if a.out:
        w = sim.alive()[0]
        ev = sim.events + [(end_t + 0.04 * q, "bell", NOTES[w] + d, 0.45, 0, 0) for q, d in enumerate((0, 4, 7, 12))]
        vid, secs = render(sim, frames, end_t, a.out)
        produce.finish(a.out, vid, ev, secs, cap=4)
        print("süre", clk)
