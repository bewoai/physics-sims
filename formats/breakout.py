"""Tuğla kırma zinciri — "Every brick = +1 ball".

Tek top tuğla duvarına çıkar; kırdığı her tuğla için alttaki fırlatıcıdan yeni bir top çıkar. Başta tek top, sonra üstel
patlama; son birkaç tuğla "son tuğla" gerilimi yaratır. Toplar birbirinin içinden geçer (klasik breakout),
yerçekimi yok, hız sabit.

  python3 formats/breakout.py --search 24
  python3 formats/breakout.py --seed 2 --out out/breakout
"""
import argparse
import math
import os
import random
import sys

import pymunk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import audio, canvas, produce  # noqa: E402
from lib.canvas import FPS, W  # noqa: E402

SUB = 4
AX0, AX1, AY0, AY1 = 90, 990, 600, 1480
COLS, ROWS, BW, BH, GAPB = 15, 14, 56, 22, 4
BY0 = 640
BALL_R, SPEED, MAX_BALLS = 8, 740, 400
HP_SLOPE = 1.25
BALL, BRICK, WALL = 1, 2, 3


def brick_rect(i, j):
    x0 = (W - COLS * (BW + GAPB) + GAPB) / 2 + j * (BW + GAPB)
    y0 = BY0 + i * (BH + GAPB)
    return x0, y0, x0 + BW, y0 + BH


class Sim:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        s = self.space = pymunk.Space()
        s.iterations = 10
        sb = s.static_body
        walls = [pymunk.Segment(sb, a, b, 6) for a, b in [((AX0, AY0), (AX1, AY0)), ((AX1, AY0), (AX1, AY1)),
                                                          ((AX1, AY1), (AX0, AY1)), ((AX0, AY1), (AX0, AY0))]]
        for w in walls:
            w.elasticity, w.friction, w.collision_type = 1.0, 0.0, WALL
        s.add(*walls)
        self.bricks = {}
        self.hp = {}
        for i in range(ROWS):
            for j in range(COLS):
                x0, y0, x1, y1 = brick_rect(i, j)
                sh = pymunk.Poly(sb, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
                sh.elasticity, sh.friction, sh.collision_type = 1.0, 0.0, BRICK
                sh.ij = (i, j)
                s.add(sh)
                self.bricks[(i, j)] = sh
                # can: alt sıralar 1, üst sıralar 10'a kadar (canlar olmadan tüm duvar ~7 sn'de çöktü)
                self.hp[(i, j)] = 1 + int(self.rng.random() * (1 + (ROWS - 1 - i) * HP_SLOPE))
        self.balls = []
        self.t = 0.0
        self.events = []
        self.broken = []          # (t, i, j)
        self.pending = []
        self.launches = []
        self.hits = []
        a = self.rng.uniform(-0.5, 0.5)
        self._ball(W / 2, AY1 - 60, math.sin(a), -math.cos(a))
        s.on_collision(BALL, BRICK, begin=self._hit)
        s.on_collision(BALL, WALL, begin=self._wall)

    def _ball(self, x, y, dx, dy):
        b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BALL_R))
        b.position = (x, y)
        b.velocity = (dx * SPEED, dy * SPEED)
        sh = pymunk.Circle(b, BALL_R)
        sh.elasticity, sh.friction, sh.collision_type = 1.0, 0.0, BALL
        sh.filter = pymunk.ShapeFilter(group=1)          # toplar birbirinin içinden geçer
        self.space.add(b, sh)
        self.balls.append((b, self.t))

    def _hit(self, arb, space, data):
        brick = arb.shapes[1] if arb.shapes[1].collision_type == BRICK else arb.shapes[0]
        if brick.ij in self.bricks and brick.ij not in [p[0] for p in self.pending]:
            self.pending.append((brick.ij, brick))

    def _wall(self, arb, space, data):
        b = arb.shapes[0].body if arb.shapes[0].collision_type == BALL else arb.shapes[1].body
        if len(self.balls) < 40:
            self.events.append((self.t, "tick", 60, 0.18, (b.position.x - W / 2) / 450, len(self.events)))

    def step_frame(self):
        dt = 1 / FPS / SUB
        for _ in range(SUB):
            self.space.step(dt)
            self.t += dt
            for ij, sh in self.pending:
                if ij not in self.bricks:
                    continue
                self.hp[ij] -= 1
                if self.hp[ij] > 0:
                    x0, y0, x1, y1 = brick_rect(*ij)
                    self.hits.append((self.t, *ij))
                    self.events.append((self.t, "tick", 60, 0.22, ((x0 + x1) / 2 - W / 2) / 450, len(self.hits)))
                    continue
                self.space.remove(sh)
                del self.bricks[ij]
                self.broken.append((self.t, *ij))
                x0, y0, x1, y1 = brick_rect(*ij)
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                pan = (cx - W / 2) / 450
                self.events.append((self.t, "pluck", audio.scale_note(ROWS - 1 - ij[0] + (ij[1] % 3), base=60), 0.35, pan, 0))
                if len(self.balls) < MAX_BALLS:
                    # yeni top alttaki fırlatıcıdan çıkar: tuğlanın içinde doğunca komşusunu anında kırıyor,
                    # tüm duvar 1,4 sn'de zincirleme çöküyordu
                    a = self.rng.uniform(-0.9, 0.9)
                    self._ball(W / 2, AY1 - 40, math.sin(a), -math.cos(a))
                    self.launches.append(self.t)
            self.pending.clear()
            for b, _ in self.balls:                    # sabit hız (yerçekimsiz breakout)
                v = b.velocity
                if v.length > 1e-3:
                    if abs(v.y) < 0.15 * v.length:      # yatay sıkışmayı önle
                        v = pymunk.Vec2d(v.x, math.copysign(0.2 * v.length, v.y or 1))
                    b.velocity = v * (SPEED / v.length)


def simulate(seed, max_t=40.0, tail=1.8):
    sim = Sim(seed)
    frames = []
    end_t = None
    while sim.t < max_t:
        sim.step_frame()
        frames.append((sim.t, [(b.position.x, b.position.y, born) for b, born in sim.balls],
                       {ij: sim.hp[ij] for ij in sim.bricks}))
        if not sim.bricks and end_t is None:
            end_t = sim.t
        if end_t is not None and sim.t - end_t > tail:
            break
    return sim, frames, end_t


def _score(seed):
    sim, fr, end_t = simulate(seed, max_t=36)
    ts = [t for t, _, _ in sim.broken]
    gaps = [b - a for a, b in zip(ts, ts[1:])]
    return seed, end_t, max(gaps) if gaps else 99, len(sim.bricks), (ts[9] if len(ts) > 9 else None)


def search(n, lo=18, hi=32):
    from multiprocessing import Pool
    with Pool(4) as p:
        res = p.map(_score, range(n))
    for r in sorted(res, key=lambda r: (r[1] is None, r[2]))[:10]:
        s, e, g, left, t10 = r
        print(f"seed={s} süre={e and round(e, 1)} en_uzun_ara={g:.1f} kalan={left} 10.tuğla={t10 and round(t10, 1)}")


def render(sim, frames, end_t, out_dir, hook="Every brick = +1 ball"):
    import skia
    from lib.canvas import paint, hsv, text
    from lib.hud import hud, Pop
    os.makedirs(out_dir, exist_ok=True)
    vid = os.path.join(out_dir, "video.mp4")
    rd = canvas.Renderer(vid, glow=0.6, glow_sigma=10)
    pop = Pop()
    brick_p = {(i, j): paint(hsv(0.92 - 0.75 * i / (ROWS - 1), 0.7, 1.0)) for i in range(ROWS) for j in range(COLS)}
    wall_p = paint(skia.Color4f(1, 1, 1, 0.85), stroke=8)
    ball_p = paint(skia.Color4f(1, 1, 1, 1))
    brk = {}
    for t0, i, j in sim.broken:
        brk[(i, j)] = t0
    for t, balls, bricks in frames:
        def draw(c):
            c.drawRect(skia.Rect(AX0, AY0, AX1, AY1), wall_p)
            for ij, hp in bricks.items():
                c.drawRect(skia.Rect(*brick_rect(*ij)), brick_p[ij])
            for ij, t0 in brk.items():                  # kırılma flaşı
                k = (t - t0) / 0.25
                if 0 <= k < 1:
                    x0, y0, x1, y1 = brick_rect(*ij)
                    g = 10 * k
                    c.drawRect(skia.Rect(x0 - g, y0 - g, x1 + g, y1 + g), paint(skia.Color4f(1, 1, 1, 0.7 * (1 - k)), stroke=3))
            for x, y, born in balls:
                s = min(1.0, (t - born) / 0.12)
                c.drawCircle(x, y, BALL_R * (0.3 + 0.7 * s), ball_p)

        def overlay(c):
            for ij, hp in bricks.items():
                if hp > 1:
                    x0, y0, x1, y1 = brick_rect(*ij)
                    text(c, str(hp), (x0 + x1) / 2, y1 - 4, size=19, weight=800, shadow=False)
            left = len(bricks)
            if end_t is not None and t >= end_t:
                hud(c, hook, "CLEARED", None, pop=max(0, 1 - (t - end_t) / 0.3), big_size=110)
            else:
                hud(c, hook, left, "BRICKS LEFT", pop=pop(left, t) if left < 30 else 0)

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
    print(f"bitiş={end_t} top={len(sim.balls)}", flush=True)
    if a.out:
        ev = sim.events + [(end_t + 0.04 * q, "bell", m, 0.45, 0, 0) for q, m in enumerate((60, 64, 67, 72, 76))]
        vid, secs = render(sim, frames, end_t, a.out)
        produce.finish(a.out, vid, ev, secs, cap=5)
        print("süre", clk)
