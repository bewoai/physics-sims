"""Dönen yedigen — "20 balls. 1 tiny exit."

Dönen bir yedigenin içinde 20 top (30 topta son 2-5 top 36 sn'de çıkamadı); bir kenarında küçük bir açıklık var. Çıkan top yerçekimiyle düşüp gider,
sayaç geri sayar. İlk kaçışlar hızlı, son toplar zorlanır → "son top" gerilimi. Her top kendi notasını
çalar (duvara her çarptığında), böylece her video kendi melodisini üretir.

  python3 formats/heptagon.py --search 60
  python3 formats/heptagon.py --seed 5 --out out/heptagon
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
CX, CY, R = W / 2, 1010, 410
N, BALL_R, GAP = 20, 18, 150
OMEGA = 1.35          # 0,85 rad/s ve 92 px açıklıkta 36 sn'de 30 topun en fazla 25'i çıktı
BALL, WALL = 1, 2


def poly_pts():
    return [(R * math.cos(2 * math.pi * k / 7 - math.pi / 2), R * math.sin(2 * math.pi * k / 7 - math.pi / 2))
            for k in range(7)]


def wall_segments():
    """Yerel koordinatta kenarlar; 0. kenarın ortasında GAP genişliğinde açıklık."""
    p = poly_pts()
    segs = []
    for k in range(7):
        a, b = p[k], p[(k + 1) % 7]
        if k == 0:
            L = math.dist(a, b)
            f = (L - GAP) / 2 / L
            m1 = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            m2 = (b[0] + (a[0] - b[0]) * f, b[1] + (a[1] - b[1]) * f)
            segs += [(a, m1), (m2, b)]
        else:
            segs.append((a, b))
    return segs


APOTHEM = R * math.cos(math.pi / 7)
NORMALS = [(math.cos(2 * math.pi * k / 7 - math.pi / 2 + math.pi / 7), math.sin(2 * math.pi * k / 7 - math.pi / 2 + math.pi / 7))
           for k in range(7)]


def outside_by(x, y, ang):
    """Yedigenin dışına taşma miktarı (yerel koordinatta, en büyük kenar normali izdüşümü - apotem).
    Merkeze uzaklık yetmiyor: üstten çıkan top dış kenarın üstünde (≈393 px) sekmeye devam edip sayılmıyordu."""
    dx, dy = x - CX, y - CY
    ca, sa = math.cos(-ang), math.sin(-ang)
    lx, ly = dx * ca - dy * sa, dx * sa + dy * ca
    return max(lx * nx + ly * ny for nx, ny in NORMALS) - APOTHEM


class Sim:
    def __init__(self, seed, gravity=950, v_floor=650):
        rng = random.Random(seed)
        s = self.space = pymunk.Space()
        s.gravity = (0, gravity)
        s.iterations = 20
        body = self.hept = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        body.position = (CX, CY)
        body.angle = rng.uniform(0, 2 * math.pi)
        body.angular_velocity = OMEGA
        shapes = []
        for a, b in wall_segments():
            sg = pymunk.Segment(body, a, b, 6)
            sg.elasticity, sg.friction, sg.collision_type = 0.95, 0.4, WALL
            shapes.append(sg)
        s.add(body, *shapes)
        self.balls = []
        k = 0
        while len(self.balls) < N:
            x, y = CX + rng.uniform(-250, 250), CY + rng.uniform(-250, 250)
            if math.hypot(x - CX, y - CY) > R * 0.8 - BALL_R:
                continue
            if any(math.hypot(x - b.position.x, y - b.position.y) < 2 * BALL_R + 4 for b, _ in self.balls):
                continue
            b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BALL_R))
            b.position = (x, y)
            b.velocity = (rng.uniform(-400, 400), rng.uniform(-400, 400))
            sh = pymunk.Circle(b, BALL_R)
            sh.elasticity, sh.friction, sh.collision_type = 0.95, 0.3, BALL
            b.velocity_func = self._keep
            s.add(b, sh)
            self.balls.append((b, k))
            k += 1
        self.v_floor = v_floor
        self.t = 0.0
        self.out = {}          # top no → kaçış zamanı
        self.events = []
        self.last_hit = {}
        s.on_collision(BALL, WALL, post_solve=self._hit)

    def _keep(self, body, g, damping, dt):
        pymunk.Body.update_velocity(body, g, damping, dt)
        sp = body.velocity.length
        if 1e-3 < sp < self.v_floor and outside_by(body.position.x, body.position.y, self.hept.angle) < 0:
            body.velocity = body.velocity * (self.v_floor / sp)

    def _hit(self, arb, space, data):
        if not arb.is_first_contact:
            return
        sh = arb.shapes[0] if arb.shapes[0].collision_type == BALL else arb.shapes[1]
        idx = next(k for b, k in self.balls if b is sh.body)
        if self.t - self.last_hit.get(idx, -1) < 0.12 or idx in self.out:
            return
        self.last_hit[idx] = self.t
        x = sh.body.position.x
        self.events.append((self.t, "pluck", audio.scale_note(idx % 15, base=55), 0.30, (x - CX) / R, 0))

    def step_frame(self):
        dt = 1 / FPS / SUB
        for _ in range(SUB):
            self.space.step(dt)
            self.t += dt
            for b, k in self.balls:
                if k not in self.out and outside_by(b.position.x, b.position.y, self.hept.angle) > BALL_R + 4:
                    self.out[k] = self.t
                    n_out = len(self.out)
                    pan = (b.position.x - CX) / R
                    self.events.append((self.t, "bell", audio.scale_note(n_out - 1, base=64), 0.45, pan, 0))
                    self.events.append((self.t, "whoosh", 60, 0.2, pan, n_out))


def simulate(seed, max_t=45.0, tail=1.8):
    sim = Sim(seed)
    frames = []
    end_t = None
    while sim.t < max_t:
        sim.step_frame()
        frames.append((sim.t, sim.hept.angle, [(b.position.x, b.position.y, k) for b, k in sim.balls], len(sim.out)))
        if len(sim.out) == N and end_t is None:
            end_t = sim.t
        if end_t is not None and sim.t - end_t > tail:
            break
    return sim, frames, end_t


def _score(seed):
    sim, fr, end_t = simulate(seed, max_t=36)
    ts = sorted(sim.out.values())
    gaps = [b - a for a, b in zip([0.0] + ts, ts)]
    return seed, end_t, max(gaps) if gaps else 99, len(sim.out)


def search(n, lo=20, hi=34):
    from multiprocessing import Pool
    with Pool(4) as p:
        res = p.map(_score, range(n))
    good = sorted((g, s, e) for s, e, g, _ in res if e and lo <= e <= hi)
    for g, s, e in good[:8]:
        print(f"seed={s} süre={e:.1f} en_uzun_bekleme={g:.1f}s")
    if not good:
        print("uygun yok; en iyi:", sorted(res, key=lambda r: -r[3])[:5])


def render(sim, frames, end_t, out_dir, hook=None):
    import skia
    hook = hook or f"{N} balls. 1 tiny exit."
    from lib.canvas import paint, hsv
    from lib.hud import hud, Pop
    os.makedirs(out_dir, exist_ok=True)
    vid = os.path.join(out_dir, "video.mp4")
    rd = canvas.Renderer(vid, glow=0.8, glow_sigma=12)
    pop = Pop()
    segs = wall_segments()
    cols = [paint(hsv(k / N * 0.9, 0.75, 1.0)) for k in range(N)]
    for t, ang, balls, n_out in frames:
        ca, sa = math.cos(ang), math.sin(ang)

        def draw(c):
            for (ax, ay), (bx, by) in segs:
                x0, y0 = CX + ax * ca - ay * sa, CY + ax * sa + ay * ca
                x1, y1 = CX + bx * ca - by * sa, CY + bx * sa + by * ca
                c.drawLine(x0, y0, x1, y1, paint(skia.Color4f(1, 1, 1, 0.92), stroke=9))
            for x, y, k in balls:
                if y < 2100:
                    c.drawCircle(x, y, BALL_R, cols[k])

        def overlay(c):
            left = N - n_out
            if end_t is not None and t >= end_t:
                hud(c, hook, "ALL OUT", None, pop=max(0, 1 - (t - end_t) / 0.3), big_size=110)
            else:
                hud(c, hook, left, "BALLS INSIDE", pop=pop(left, t))

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
    print(f"bitiş={end_t} çıkan={len(sim.out)}", flush=True)
    if a.out:
        ev = sim.events + [(end_t + 0.03 * q, "bell", m, 0.4, 0, 0) for q, m in enumerate((64, 68, 71, 76))]
        vid, secs = render(sim, frames, end_t, a.out)
        produce.finish(a.out, vid, ev, secs, cap=5)
        print("süre", clk)
