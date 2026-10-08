"""Son kalan top — "Which number survives?"

Çember arenada numaralı 12 top. Duvarın bir parçası dönen kırmızı lazer; ona değen top elenir. Lazer yayı
zamanla uzar → elemeler hızlanır. İzleyici bir numara seçip tutar (yorumlarda "7!" tipi etkileşim).

  python3 formats/survivor.py --search 48
  python3 formats/survivor.py --seed 3 --out out/survivor
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
N, BALL_R = 12, 34
OMEGA, W0, W1, T_GROW = 0.75, 0.16, 0.75, 26.0      # ilk deneme 1,1 / 0,45 / 1,7: 7–13 sn'de bitti
BALL, WALL = 1, 2


def laser(t):
    w = W0 + (W1 - W0) * min(1.0, t / T_GROW)
    return (OMEGA * t) % (2 * math.pi), w


def in_arc(ang, t):
    c, w = laser(t)
    d = (ang - c + math.pi) % (2 * math.pi) - math.pi
    return abs(d) < w / 2


class Sim:
    def __init__(self, seed, gravity=900, v_floor=520):
        rng = random.Random(seed)
        s = self.space = pymunk.Space()
        s.gravity = (0, gravity)
        s.iterations = 20
        n = 180
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            seg = pymunk.Segment(s.static_body, (CX + (R + 6) * math.cos(a0), CY + (R + 6) * math.sin(a0)),
                                 (CX + (R + 6) * math.cos(a1), CY + (R + 6) * math.sin(a1)), 6)
            seg.elasticity, seg.friction, seg.collision_type = 1.0, 0.2, WALL
            s.add(seg)
        self.balls = {}
        k = 0
        while len(self.balls) < N:
            x, y = CX + rng.uniform(-300, 300), CY + rng.uniform(-300, 300)
            if math.hypot(x - CX, y - CY) > R - BALL_R - 10:
                continue
            if any(math.hypot(x - b.position.x, y - b.position.y) < 2 * BALL_R + 6 for b in self.balls.values()):
                continue
            b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BALL_R))
            b.position = (x, y)
            b.velocity = (rng.uniform(-500, 500), rng.uniform(-500, 200))
            sh = pymunk.Circle(b, BALL_R)
            sh.elasticity, sh.friction, sh.collision_type = 0.95, 0.2, BALL
            sh.num = k + 1
            b.velocity_func = self._keep
            s.add(b, sh)
            self.balls[k + 1] = b
            k += 1
        self.v_floor = v_floor
        self.t = 0.0
        self.dead = {}            # numara → (zaman, x, y)
        self.events = []
        self.kill = []
        s.on_collision(BALL, WALL, begin=self._wall)
        s.on_collision(BALL, BALL, post_solve=self._clack)

    def _keep(self, body, g, damping, dt):
        pymunk.Body.update_velocity(body, g, damping, dt)
        sp = body.velocity.length
        if 1e-3 < sp < self.v_floor:
            body.velocity = body.velocity * (self.v_floor / sp)

    def _wall(self, arb, space, data):
        sh = arb.shapes[0] if arb.shapes[0].collision_type == BALL else arb.shapes[1]
        p = sh.body.position
        ang = math.atan2(p.y - CY, p.x - CX)
        if in_arc(ang, self.t) and len(self.balls) - len(self.kill) > 1:
            self.kill.append(sh)
        else:
            self.events.append((self.t, "pluck", audio.scale_note((sh.num - 1) % 15, base=57), 0.3, (p.x - CX) / R, 0))

    def _clack(self, arb, space, data):
        if arb.is_first_contact and arb.total_impulse.length > 200:
            p = arb.contact_point_set.points[0].point_a
            self.events.append((self.t, "tick", 60, 0.25, (p.x - CX) / R, len(self.events)))

    def step_frame(self):
        dt = 1 / FPS / SUB
        for _ in range(SUB):
            self.space.step(dt)
            self.t += dt
            for sh in self.kill:
                if sh.num in self.balls:
                    b = self.balls.pop(sh.num)
                    self.dead[sh.num] = (self.t, b.position.x, b.position.y)
                    self.space.remove(b, sh)
                    pan = (b.position.x - CX) / R
                    self.events.append((self.t, "shatter", 60, 0.6, pan, sh.num))
                    self.events.append((self.t, "bell", 52 - len(self.dead) % 5, 0.4, pan, 0))
            self.kill.clear()


def simulate(seed, max_t=40.0, tail=2.2):
    sim = Sim(seed)
    frames = []
    end_t = None
    while sim.t < max_t:
        sim.step_frame()
        frames.append((sim.t, {k: (b.position.x, b.position.y) for k, b in sim.balls.items()}))
        if len(sim.balls) == 1 and end_t is None:
            end_t = sim.t
        if end_t is not None and sim.t - end_t > tail:
            break
    return sim, frames, end_t


def _score(seed):
    sim, fr, e = simulate(seed, max_t=34)
    ts = sorted(t for t, _, _ in sim.dead.values())
    gaps = [b - a for a, b in zip([0.0] + ts, ts)]
    return seed, e, max(gaps) if gaps else 99, ts[0] if ts else None


def search(n, lo=20, hi=30):
    from multiprocessing import Pool
    with Pool(4) as p:
        res = p.map(_score, range(n))
    good = sorted((g, s, e, f) for s, e, g, f in res if e and lo <= e <= hi and f and f > 1.5)
    for g, s, e, f in good[:8]:
        print(f"seed={s} süre={e:.1f} en_uzun_ara={g:.1f} ilk_eleme={f:.1f}")
    if not good:
        print("uygun yok", sorted(res, key=lambda r: r[2])[:6])


def render(sim, frames, end_t, out_dir, hook="Which number survives?"):
    import skia
    from lib.canvas import paint, hsv, text
    from lib.hud import hud, Pop
    os.makedirs(out_dir, exist_ok=True)
    vid = os.path.join(out_dir, "video.mp4")
    rd = canvas.Renderer(vid, glow=0.7, glow_sigma=12)
    pop = Pop()
    cols = {k: paint(hsv((k - 1) / N * 0.9, 0.7, 0.95)) for k in range(1, N + 1)}
    winner = next(iter(frames[-1][1])) if end_t else None
    rect = skia.Rect(CX - R - 6, CY - R - 6, CX + R + 6, CY + R + 6)
    for t, balls in frames:
        c_ang, w = laser(t)

        def draw(c):
            c.drawCircle(CX, CY, R + 6, paint(skia.Color4f(1, 1, 1, 0.85), stroke=8))
            path = skia.Path()
            path.addArc(rect, math.degrees(c_ang - w / 2), math.degrees(w))
            c.drawPath(path, paint(skia.Color4f(1, 0.12, 0.15, 1), stroke=16))
            for k, (t0, x, y) in sim.dead.items():
                q = (t - t0) / 0.5
                if 0 <= q < 1:
                    c.drawCircle(x, y, BALL_R + 70 * q, paint(hsv((k - 1) / N * 0.9, 0.6, 1, 1 - q), stroke=6))
            for k, (x, y) in balls.items():
                c.drawCircle(x, y, BALL_R, cols[k])

        def overlay(c):
            for k, (x, y) in balls.items():
                text(c, str(k), x, y + 12, size=34, weight=900, shadow=False)
            left = len(balls)
            if end_t is not None and t >= end_t:
                hud(c, hook, f"#{winner} WINS", None, pop=max(0, 1 - (t - end_t) / 0.3), big_size=110)
            else:
                hud(c, hook, left, "LEFT", pop=pop(left, t))

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
    print(f"bitiş={end_t} kazanan={list(sim.balls)}", flush=True)
    if a.out:
        ev = sim.events + [(end_t + 0.04 * q, "bell", m, 0.45, 0, 0) for q, m in enumerate((60, 64, 67, 72, 76))]
        vid, secs = render(sim, frames, end_t, a.out)
        produce.finish(a.out, vid, ev, secs, cap=5)
        print("süre", clk)
