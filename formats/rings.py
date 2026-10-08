"""Format B — "Can the ball escape N rings?"

Top iç içe dönen, boşluklu halkaların ortasında. Boşluktan çıktığı her halka parçalanır, her kırılmada
nota bir basamak yükselir, top biraz hızlanır. Son halka kırılınca top serbest kalır.
Kod avantajı: yüzlerce tohumu (seed) render etmeden simüle edip temposu en iyi olanı seçeriz
(toplam süre, en uzun "takılma" anı).

  python3 formats/rings.py --search 200            # tohum taraması
  python3 formats/rings.py --seed 17 --out out/b
"""
import argparse
import math
import os
import random
import sys

import pymunk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import audio, canvas, encode  # noqa: E402
from lib.canvas import FPS, W  # noqa: E402

SUB = 4
CX, CY = W / 2, 1010
N_RINGS = 20
R0, R_STEP = 70, 20          # 70 .. 450 px
BALL_R = 11
BALL, RING = 1, 2


def ring_params(seed):
    rng = random.Random(seed * 7919 + 1)
    rings = []
    for i in range(N_RINGS):
        r = R0 + i * R_STEP
        w = (1.5 + 1.2 * rng.random()) * (1 if i % 2 == 0 else -1)
        gap = 0.95 - 0.012 * i
        rings.append({"r": r, "w": w, "phase": rng.uniform(0, 2 * math.pi), "gap": gap,
                      "hue": 0.95 - 0.8 * i / (N_RINGS - 1)})
    return rings


class Sim:
    def __init__(self, seed, gravity=950, v0=650, v_gain=1.03, v_max=1500):
        self.rng = random.Random(seed)
        self.rings = ring_params(seed)
        self.v_floor, self.v_gain, self.v_max = v0, v_gain, v_max
        s = self.space = pymunk.Space()
        s.gravity = (0, gravity)
        s.iterations = 20
        b = self.ball = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BALL_R))
        b.position = (CX + self.rng.uniform(-10, 10), CY - 20)
        a = self.rng.uniform(0, 2 * math.pi)
        b.velocity = (v0 * math.cos(a), v0 * math.sin(a))
        sh = pymunk.Circle(b, BALL_R)
        sh.elasticity, sh.friction, sh.collision_type = 1.0, 0.0, BALL
        b.velocity_func = self._keep_speed
        s.add(b, sh)
        s.on_collision(BALL, RING, post_solve=self._bounce)
        self.t = 0.0
        self.cur = 0                    # en içteki sağlam halka
        self.ring_body = None
        self.broken = []                # (t, i)
        self.events = []
        self.last_bounce = -1
        self.bounce_n = 0
        self._spawn_ring(0)

    def _keep_speed(self, body, g, damping, dt):
        pymunk.Body.update_velocity(body, g, damping, dt)
        sp = body.velocity.length
        if 1e-3 < sp < self.v_floor:
            body.velocity = body.velocity * (self.v_floor / sp)

    def ring_angle(self, i, t):
        p = self.rings[i]
        return p["phase"] + p["w"] * t

    def _spawn_ring(self, i):
        if self.ring_body is not None:
            self.space.remove(self.ring_body, *self.ring_body.shapes)
            self.ring_body = None
        if i >= N_RINGS:
            return
        p = self.rings[i]
        body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        body.angle = self.ring_angle(i, self.t)
        body.angular_velocity = p["w"]
        body.position = (CX, CY)
        r, g = p["r"], p["gap"]
        n = max(24, int(2 * math.pi * r / 10))
        shapes = []
        for k in range(n):
            a0 = g / 2 + (2 * math.pi - g) * k / n
            a1 = g / 2 + (2 * math.pi - g) * (k + 1) / n
            seg = pymunk.Segment(body, (r * math.cos(a0), r * math.sin(a0)), (r * math.cos(a1), r * math.sin(a1)), 3)
            seg.elasticity, seg.friction, seg.collision_type = 1.0, 0.0, RING
            shapes.append(seg)
        self.space.add(body, *shapes)
        self.ring_body = body

    def _bounce(self, arb, space, data):
        if not arb.is_first_contact or self.t - self.last_bounce < 0.05:
            return
        self.last_bounce = self.t
        self.bounce_n += 1
        x = self.ball.position.x
        self.events.append((self.t, "pluck", audio.scale_note(self.bounce_n % 3, base=50), 0.30, (x - CX) / 480, 0))
        self.events.append((self.t, "tick", 60, 0.12, (x - CX) / 480, self.bounce_n))

    def step_frame(self):
        dt = 1 / FPS / SUB
        for _ in range(SUB):
            self.space.step(dt)
            self.t += dt
            if self.cur < N_RINGS:
                d = (self.ball.position - (CX, CY)).length
                # merkez halka çizgisini geçince kır: bir sonraki halkayla çakışma olmasın (aralık > yarıçap + kalınlık)
                if d > self.rings[self.cur]["r"] + 1:
                    self._break(self.cur)

    def _break(self, i):
        self.broken.append((self.t, i))
        x = self.ball.position.x
        pan = (x - CX) / 480
        self.events.append((self.t, "bell", audio.scale_note(i, base=64), 0.55, pan, 0))
        self.events.append((self.t, "shatter", 60, 0.35 + 0.02 * i, pan, i))
        self.cur = i + 1
        self.v_floor = min(self.v_max, self.v_floor * self.v_gain)
        if self.cur == N_RINGS:
            for k, m in enumerate((72, 76, 79, 84)):
                self.events.append((self.t + 0.02 * k, "bell", m, 0.5, 0, 0))
            self.events.append((self.t, "thud", 40, 0.9, 0, 0))
            self.ball.velocity_func = pymunk.Body.update_velocity
        self._spawn_ring(self.cur)


def simulate(seed, max_t=50.0, tail=1.8, **kw):
    sim = Sim(seed, **kw)
    frames = []
    end_t = None
    while sim.t < max_t:
        sim.step_frame()
        frames.append({"t": sim.t, "ball": (sim.ball.position.x, sim.ball.position.y), "cur": sim.cur})
        if sim.cur == N_RINGS and end_t is None:
            end_t = sim.t
        if end_t is not None and sim.t - end_t > tail:
            break
    return sim, frames, end_t


def pacing(sim, end_t):
    ts = [0.0] + [t for t, _ in sim.broken]
    gaps = [b - a for a, b in zip(ts, ts[1:])]
    return {"end": end_t, "max_gap": max(gaps) if gaps else None, "first": ts[1] if len(ts) > 1 else None}


def _score(seed, hi=34):
    sim, fr, end_t = simulate(seed, max_t=hi + 1)
    return seed, end_t, pacing(sim, end_t)


def search(n, lo=22, hi=34):
    from multiprocessing import Pool
    with Pool(4) as pool:
        res = pool.map(_score, range(n))
    good = [(p["max_gap"], s, e) for s, e, p in res if e and lo <= e <= hi and p["first"] < 1.5]
    good.sort()
    for g, s, e in good[:10]:
        print(f"seed={s} süre={e:.1f} en_uzun_takılma={g:.2f}s")


# ---------------------------------------------------------------- çizim
def render(sim, frames, out_dir, hook=None):
    import skia
    from lib.canvas import paint, hsv
    from lib.hud import hud, Pop
    pop = Pop()
    hook = hook or f"Can the ball escape {N_RINGS} rings?"
    os.makedirs(out_dir, exist_ok=True)
    vid = os.path.join(out_dir, "video.mp4")
    rd = canvas.Renderer(vid, glow=0.9, glow_sigma=12)
    rng = random.Random(5)
    # her kırılma için parça listesi: (açı ortası, yay uzunluğu, hız, dönüş)
    shards = {}
    for t0, i in sim.broken:
        p = sim.rings[i]
        n = 22
        lst = []
        for k in range(n):
            a = sim.ring_angle(i, t0) + p["gap"] / 2 + (2 * math.pi - p["gap"]) * (k + 0.5) / n
            lst.append((a, (2 * math.pi - p["gap"]) / n * 0.8, rng.uniform(150, 520), rng.uniform(-6, 6)))
        shards[i] = (t0, lst)
    trail = []
    end_t = sim.broken[-1][0] if len(sim.broken) == N_RINGS else None
    for f in frames:
        t = f["t"]
        trail.append(f["ball"])
        trail = trail[-12:]

        def draw(c):
            for i in range(f["cur"], N_RINGS):
                p = sim.rings[i]
                a0 = math.degrees(sim.ring_angle(i, t) + p["gap"] / 2)
                sweep = math.degrees(2 * math.pi - p["gap"])
                rect = skia.Rect(CX - p["r"], CY - p["r"], CX + p["r"], CY + p["r"])
                pt = paint(hsv(p["hue"], 0.75, 1.0, 0.95 if i == f["cur"] else 0.55), stroke=6 if i == f["cur"] else 4)
                path = skia.Path()
                path.addArc(rect, a0, sweep)
                c.drawPath(path, pt)
            for i, (t0, lst) in shards.items():
                dt = t - t0
                if dt < 0 or dt > 1.6:
                    continue
                p = sim.rings[i]
                alpha = max(0.0, 1 - dt / 1.6)
                for a, arc, sp, spin in lst:
                    rr = p["r"] + sp * dt
                    x = CX + rr * math.cos(a)
                    y = CY + rr * math.sin(a) + 500 * dt * dt
                    L = p["r"] * arc / 2
                    ang = a + math.pi / 2 + spin * dt
                    c.drawLine(x - L * math.cos(ang), y - L * math.sin(ang), x + L * math.cos(ang), y + L * math.sin(ang),
                               paint(hsv(p["hue"], 0.75, 1.0, alpha), stroke=5))
                if dt < 0.3:                         # kırılma halkası flaşı
                    c.drawCircle(CX, CY, p["r"] + 60 * dt, paint(hsv(p["hue"], 0.4, 1, 0.5 * (1 - dt / 0.3)), stroke=3))
            for i, (x, y) in enumerate(trail[:-1]):
                k = (i + 1) / len(trail)
                c.drawCircle(x, y, BALL_R * (0.3 + 0.6 * k), paint(skia.Color4f(1, 1, 1, 0.22 * k)))
            x, y = f["ball"]
            c.drawCircle(x, y, BALL_R, paint(skia.Color4f(1, 1, 1, 1)))

        def overlay(c):
            left = N_RINGS - f["cur"]
            if end_t is not None and t >= end_t:
                k = min(1.0, (t - end_t) / 0.25)
                hud(c, hook, "ESCAPED", None, pop=1 - k, big_size=110)
            else:
                hud(c, hook, left, "RINGS LEFT", pop=pop(left, t))

        rd.frame(draw, overlay)
    return vid, rd.close()


def build_audio(sim, out_dir, seconds):
    mx = audio.Mix(seconds)
    for e in sim.events:
        mx.add(*e)
    return mx.render(os.path.join(out_dir, "mix.wav"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--search", type=int)
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.search:
        search(a.search)
        sys.exit()
    sim, frames, end_t = simulate(a.seed)
    print(pacing(sim, end_t), flush=True)
    if a.out:
        vid, n = render(sim, frames, a.out)
        wav = build_audio(sim, a.out, frames[-1]["t"])
        final = encode.mux(vid, wav, os.path.join(a.out, "final.mp4"))
        encode.contact_sheet(final, os.path.join(a.out, "sheet.jpg"))
        print("kare", n, final, encode.loudness(final))
