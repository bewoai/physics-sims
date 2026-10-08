"""Büyüyen top — "Every bounce, the ball gets bigger".

Tek top çemberin içinde zıplar, her duvar sekmesinde yarıçapı büyür. Büyüdükçe hareket alanı daralır,
sekmeler sıklaşır → büyüme kendiliğinden hızlanır. Top çemberi tamamen doldurunca patlar (ödül).
Her sekme bir halka izi bırakır; iç içe renkli halkalar oluşur.

  python3 formats/grow.py --search 40      # tempo taraması
  python3 formats/grow.py --seed 4 --out out/grow
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
CX, CY, R = W / 2, 1010, 430
R0, GROWTH = 40, 1.035   # ilk sürüm 16 px: ilk 12 sn top %4→%11, çok yavaş açılış
BALL, WALL = 1, 2


class Sim:
    def __init__(self, seed, gravity=1300, v_floor=850):
        rng = random.Random(seed)
        s = self.space = pymunk.Space()
        s.gravity = (0, gravity)
        n = 160
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            seg = pymunk.Segment(s.static_body, (CX + (R + 5) * math.cos(a0), CY + (R + 5) * math.sin(a0)),
                                 (CX + (R + 5) * math.cos(a1), CY + (R + 5) * math.sin(a1)), 5)
            seg.elasticity, seg.friction, seg.collision_type = 1.0, 0.0, WALL
            s.add(seg)
        self.r = R0
        b = self.body = pymunk.Body(1, 100)
        b.position = (CX + rng.uniform(-80, 80), CY - 200)
        a = rng.uniform(-1, 1)
        b.velocity = (600 * math.sin(a), 200)
        self.shape = pymunk.Circle(b, R0)
        self.shape.elasticity, self.shape.friction, self.shape.collision_type = 1.0, 0.0, BALL
        s.add(b, self.shape)
        self.v_floor = v_floor
        b.velocity_func = self._keep
        s.on_collision(BALL, WALL, post_solve=self._hit)
        self.t, self.last, self.n = 0.0, -1.0, 0
        self.rings = []        # (t, x, y, r, hue)
        self.events = []
        self.full_t = None

    def _keep(self, body, g, damping, dt):
        pymunk.Body.update_velocity(body, g, damping, dt)
        sp = body.velocity.length
        if 1e-3 < sp < self.v_floor:
            body.velocity = body.velocity * (self.v_floor / sp)

    def _hit(self, arb, space, data):
        if not arb.is_first_contact or self.full_t is not None or self.t - self.last < 0.04:
            return
        self.last = self.t
        p = self.body.position
        hue = (self.n * 0.037) % 1.0
        self.rings.append((self.t, p.x, p.y, self.r, hue))
        k = self.n
        cyc, pos = divmod(k, 14)
        idx = pos if pos < 7 else 14 - pos
        pan = (p.x - CX) / R
        self.events.append((self.t, "pluck", audio.scale_note(idx + 2 * (cyc % 3), base=60), 0.75, pan, 0))
        self.events.append((self.t, "thud", 40, min(0.8, 0.15 + self.r / R), pan, k))
        self.n += 1
        self.r = min(R - 1, self.r * GROWTH)
        self.shape.unsafe_set_radius(self.r)
        if self.r >= R - 2:
            self.full_t = self.t

    def step_frame(self):
        dt = 1 / FPS / SUB
        for _ in range(SUB):
            self.space.step(dt)
            self.t += dt
            # büyüme anında duvara gömülmesin: içeri al
            d = self.body.position - (CX, CY)
            lim = R - self.r
            if d.length > lim:
                self.body.position = (CX, CY) + (d * (lim / d.length) if d.length > 1e-6 else d)
        if self.full_t is not None:
            self.body.velocity = (0, 0)
            self.body.position = self.body.position + ((CX, CY) - self.body.position) * 0.25


def simulate(seed, max_t=40.0, tail=1.8):
    sim = Sim(seed)
    frames = []
    while sim.t < max_t:
        sim.step_frame()
        frames.append((sim.t, sim.body.position.x, sim.body.position.y, sim.r, sim.n))
        if sim.full_t is not None and sim.t - sim.full_t > tail:
            break
    return sim, frames


def search(n):
    res = []
    for seed in range(n):
        sim, fr = simulate(seed)
        if sim.full_t:
            res.append((abs(sim.full_t - 24), seed, sim.full_t, sim.n))
    res.sort()
    for _, s, ft, nb in res[:8]:
        print(f"seed={s} dolma={ft:.1f}s sekme={nb}")


def render(sim, frames, out_dir, hook="Every bounce, the ball gets bigger"):
    import skia
    from lib.canvas import paint, hsv
    from lib.hud import hud, Pop
    os.makedirs(out_dir, exist_ok=True)
    vid = os.path.join(out_dir, "video.mp4")
    rd = canvas.Renderer(vid, glow=0.8, glow_sigma=12)
    pop = Pop()
    for t, x, y, r, n in frames:
        hue = (max(0, n - 1) * 0.037) % 1.0

        def draw(c):
            c.drawCircle(CX, CY, R + 5, paint(skia.Color4f(1, 1, 1, 0.9), stroke=7))
            for t0, rx, ry, rr, rh in sim.rings:
                age = t - t0
                if 0 <= age < 2.5:
                    c.drawCircle(rx, ry, rr, paint(hsv(rh, 0.7, 1.0, 0.55 * (1 - age / 2.5)), stroke=3))
            c.drawCircle(x, y, r, paint(hsv(hue, 0.75, 0.95)))
            c.drawCircle(x, y, r, paint(skia.Color4f(1, 1, 1, 0.85), stroke=3))
            if sim.full_t is not None and t >= sim.full_t:
                k = (t - sim.full_t) / 0.6
                if k < 1:
                    c.drawCircle(CX, CY, R + 30 + 200 * k, paint(skia.Color4f(1, 1, 1, 0.6 * (1 - k)), stroke=10))

        def overlay(c):
            pct = min(100, round(100 * r / R))
            hud(c, hook, f"{pct}%", "SIZE", pop=pop(pct, t))

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
    sim, frames = simulate(a.seed)
    print(f"dolma={sim.full_t} sekme={sim.n}", flush=True)
    if a.out:
        ev = sim.events + [(sim.full_t, "shatter", 60, 0.8, 0, 2), (sim.full_t, "bell", 72, 0.5, 0, 0),
                           (sim.full_t, "bell", 79, 0.4, 0, 0)]
        vid, secs = render(sim, frames, a.out)
        produce.finish(a.out, vid, ev, secs)
        print("süre", clk)
