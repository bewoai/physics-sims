"""Format A — "Every bounce = +1 ball".

Beyaz ana top çemberin içinde zıplar; her çarpışmasında (duvar ya da top) arenaya yeni bir top eklenir.
Başta yavaş (saniyede ~1), arena doldukça ana top daha sık çarpar ve sayı hızlanır → doğal tırmanış.
Arena dolunca çember kırılır, toplar ekrandan dökülür (ödül anı).

  python3 formats/multiply.py --seed 3 --stats        # sadece simülasyon, tempo ölçümü
  python3 formats/multiply.py --seed 3 --out out/a    # render + ses + birleştirme
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

SUB = 4                     # kare başına fizik alt adımı
CX, CY, R = W / 2, 1010, 430
R_MAIN, R_BALL = 26, 26
MAIN, BALL, WALL = 1, 2, 3


class Sim:
    def __init__(self, seed, gravity=1400, min_speed=950, cooldown=0.035, max_balls=520, tail=2.2,
                 speedup=1.015, max_speed=2800):
        self.rng = random.Random(seed)
        self.min_speed, self.cooldown, self.max_balls, self.tail = min_speed, cooldown, max_balls, tail
        self.speedup, self.max_speed = speedup, max_speed
        s = self.space = pymunk.Space()
        s.gravity = (0, gravity)
        s.iterations = 25
        self.walls = []
        n = 140
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            seg = pymunk.Segment(s.static_body, (CX + (R + 6) * math.cos(a0), CY + (R + 6) * math.sin(a0)),
                                 (CX + (R + 6) * math.cos(a1), CY + (R + 6) * math.sin(a1)), 6)
            seg.elasticity, seg.friction, seg.collision_type = 1.0, 0.0, WALL
            self.walls.append(seg)
        s.add(*self.walls)

        self.main = self._ball(CX + 60, CY - 250, R_MAIN, MAIN, 1.0)
        a = self.rng.uniform(-0.6, 0.6)
        self.main.velocity = (900 * math.sin(a), 300)
        self.main.velocity_func = self._keep_speed
        self.balls = []            # (body, born_t, hue)
        self.t, self.last_spawn = 0.0, -1.0
        self.note = 0
        self.flashes = []          # (t, x, y, hue)
        self.events = []           # ses olayları: (t, kind, midi, gain, pan)
        self.counts = []           # kare başına top sayısı
        self.full_t = None
        self.pending = []
        s.on_collision(MAIN, WALL, begin=self._hit)
        s.on_collision(MAIN, BALL, begin=self._hit)
        s.on_collision(BALL, WALL, post_solve=self._clack)
        s.on_collision(BALL, BALL, post_solve=self._clack)

    def _ball(self, x, y, r, ctype, elast):
        b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, r))
        b.position = (x, y)
        sh = pymunk.Circle(b, r)
        sh.elasticity, sh.friction, sh.collision_type = elast, 0.2, ctype
        self.space.add(b, sh)
        return b

    def _keep_speed(self, body, gravity, damping, dt):
        pymunk.Body.update_velocity(body, gravity, damping, dt)
        v = body.velocity
        sp = v.length
        target = min(self.max_speed, self.min_speed * self.speedup ** len(self.balls))
        if 1e-3 < sp < target:
            body.velocity = v * (target / sp)

    def _hit(self, arb, space, data):
        if self.full_t is not None or self.t - self.last_spawn < self.cooldown:
            return
        self.last_spawn = self.t
        p = arb.contact_point_set.points[0].point_a if arb.contact_point_set.points else self.main.position
        self.pending.append((p.x, p.y))

    def _clack(self, arb, space, data):
        if not arb.is_first_contact:
            return
        imp = arb.total_impulse.length
        if imp > 260:
            p = arb.contact_point_set.points[0].point_a if arb.contact_point_set.points else (CX, CY)
            self.events.append((self.t, "tick", 60, min(0.35, imp / 2500), (p[0] - CX) / R, 0))

    def _free_spot(self, hx, hy):
        """Yeni top için boş yer: önce çarpma noktasının yakını, sonra arenanın üst yarısı."""
        for k in range(40):
            if k < 12:
                ang = self.rng.uniform(0, 2 * math.pi)
                d = self.rng.uniform(40, 160)
                x, y = hx + d * math.cos(ang), hy + d * math.sin(ang)
            else:
                ang = self.rng.uniform(math.pi * 1.05, math.pi * 1.95)
                d = self.rng.uniform(0, R - R_BALL - 14)
                x, y = CX + d * math.cos(ang), CY + d * math.sin(ang) * self.rng.uniform(0.2, 1)
            if math.hypot(x - CX, y - CY) > R - R_BALL - 10:
                continue
            q = self.space.point_query_nearest((x, y), R_BALL + 3, pymunk.ShapeFilter())
            if q is None:
                return x, y
        return None

    def step_frame(self):
        dt = 1 / FPS / SUB
        for _ in range(SUB):
            self.space.step(dt)
            self.t += dt
            for hx, hy in self.pending:
                spot = self._free_spot(hx, hy)
                if spot is None or len(self.balls) >= self.max_balls:
                    self.full_t = self.full_t or self.t
                    continue
                hue = (len(self.balls) * 0.0042) % 1.0
                b = self._ball(spot[0], spot[1], R_BALL, BALL, 0.55)
                mv = self.main.velocity
                b.velocity = (mv.x * 0.25 + self.rng.uniform(-80, 80), mv.y * 0.15)
                self.balls.append((b, self.t, hue))
                self.flashes.append((self.t, spot[0], spot[1], hue))
                pan = (hx - CX) / R
                self.events.append((self.t, "pluck", audio.scale_note(self._next_note(), base=62), 0.8, pan, 0))
                self.events.append((self.t, "pop", 74 + (len(self.balls) % 5) * 2, 0.35, (spot[0] - CX) / R, 0))
            self.pending.clear()
        # duvarın dışına kaçan (aşırı itilen) topları geri al — kırılmadan önce
        if self.full_t is None:
            for b, _, _ in self.balls:
                d = b.position - (CX, CY)
                if d.length > R - R_BALL + 2:
                    b.position = (CX, CY) + d * ((R - R_BALL - 2) / d.length)
                    b.velocity = b.velocity * 0.3
        self.counts.append(len(self.balls))

    def _next_note(self):
        # 0..9 arası yukarı-aşağı arpej, her turda bir basamak yukarı kayar
        k = self.note
        self.note += 1
        cyc, pos = divmod(k, 16)
        idx = pos if pos < 8 else 16 - pos
        return idx + (cyc % 3)

    def shatter(self):
        """Çemberi kır: duvar parçaları dışa savrulur, toplar dökülür."""
        self.space.remove(*self.walls)
        frags = []
        for i, seg in enumerate(self.walls[::2]):
            a = seg.a
            ang = math.atan2(a.y - CY, a.x - CX)
            b = pymunk.Body(0.5, 50)
            b.position = (a.x, a.y)
            sp = self.rng.uniform(250, 700)
            b.velocity = (sp * math.cos(ang), sp * math.sin(ang) - 300)
            b.angular_velocity = self.rng.uniform(-12, 12)
            b.angle = ang + math.pi / 2
            frags.append((b, i / len(self.walls) * 2))
            self.space.add(b)            # şekilsiz gövde: çarpışmaz, sadece savrulur
        self.frags = frags
        for b, _, _ in self.balls:
            b.velocity = b.velocity + ((b.position.x - CX) * 1.2, -120)
        self.main.velocity_func = pymunk.Body.update_velocity
        self.events.append((self.t, "shatter", 60, 1.0, 0, 3))
        self.events.append((self.t, "thud", 40, 0.9, 0, 0))
        self.events.append((self.t, "bell", 86, 0.5, 0, 0))


def simulate(seed, max_t=45.0, **kw):
    sim = Sim(seed, **kw)
    frames = []
    shattered_at = None
    while sim.t < max_t:
        sim.step_frame()
        if sim.full_t is not None and shattered_at is None and sim.t - sim.full_t > 1.2:
            sim.shatter()
            shattered_at = sim.t
        frames.append(snapshot(sim, shattered_at))
        if shattered_at is not None and sim.t - shattered_at > sim.tail:
            break
    return sim, frames, shattered_at


def snapshot(sim, shattered_at):
    m = sim.main
    return {
        "t": sim.t,
        "main": (m.position.x, m.position.y),
        "balls": [(b.position.x, b.position.y, h, sim.t - born) for b, born, h in sim.balls],
        "count": len(sim.balls),
        "frags": [(b.position.x, b.position.y, b.angle, h) for b, h in getattr(sim, "frags", [])],
        "shattered": shattered_at,
        "flashes": [f for f in sim.flashes if sim.t - f[0] < 0.35],
    }


def stats(sim, frames, shattered_at):
    def at(sec):
        i = min(len(sim.counts) - 1, int(sec * FPS))
        return sim.counts[i]
    marks = " ".join(f"{s}s:{at(s)}" for s in (2, 5, 8, 11, 14, 17, 20, 23, 26, 29))
    end = frames[-1]["t"]
    return f"dolu={sim.full_t and round(sim.full_t, 1)} kırılma={shattered_at and round(shattered_at, 1)} süre={end:.1f} | {marks}"


# ---------------------------------------------------------------- çizim
def render(frames, out_dir, hook="Every bounce = +1 ball"):
    import skia
    from lib.canvas import paint, hsv
    from lib.hud import hud, Pop
    os.makedirs(out_dir, exist_ok=True)
    vid = os.path.join(out_dir, "video.mp4")
    rd = canvas.Renderer(vid, glow=0.85, glow_sigma=12)
    pop = Pop()
    trail = []
    shatter_t = None
    for f in frames:
        t = f["t"]
        trail.append(f["main"])
        trail = trail[-14:]
        if f["shattered"] is not None:
            shatter_t = f["shattered"]

        def draw(c):
            # çember: kırılınca parçalar
            if shatter_t is None:
                ring_hue = 0.55 + 0.25 * math.sin(t * 0.35)
                c.drawCircle(CX, CY, R + 6, paint(hsv(ring_hue, 0.55, 1.0), stroke=9))
            else:
                for x, y, ang, h in f["frags"]:
                    dx, dy = 13 * math.cos(ang), 13 * math.sin(ang)
                    a = max(0.0, 1 - (t - shatter_t) / 2.5)
                    c.drawLine(x - dx, y - dy, x + dx, y + dy, paint(hsv(0.55 + 0.25 * h, 0.55, 1.0, a), stroke=9))
            # flaşlar
            for ft, fx, fy, fh in f["flashes"]:
                k = (t - ft) / 0.35
                c.drawCircle(fx, fy, R_BALL + 40 * k, paint(hsv(fh, 0.6, 1, 0.6 * (1 - k)), stroke=3))
            # toplar
            for x, y, h, age in f["balls"]:
                s = min(1.0, age / 0.1)
                c.drawCircle(x, y, R_BALL * (0.4 + 0.6 * s), paint(hsv(h, 0.78, 1.0)))
            # ana top + iz
            for i, (x, y) in enumerate(trail[:-1]):
                k = (i + 1) / len(trail)
                c.drawCircle(x, y, R_MAIN * (0.35 + 0.55 * k), paint(skia.Color4f(1, 1, 1, 0.25 * k)))
            x, y = f["main"]
            c.drawCircle(x, y, R_MAIN, paint(skia.Color4f(1, 1, 1, 1)))

        def overlay(c):
            n = f["count"] + 1          # ana top dahil
            hud(c, hook, n, "BALLS", pop=pop(n, t))

        rd.frame(draw, overlay)
    n = rd.close()
    return vid, n


def build_audio(sim, out_dir, seconds):
    mx = audio.Mix(seconds)
    for e in sim.events:
        mx.add(*e)
    return mx.render(os.path.join(out_dir, "mix.wav"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    sim, frames, sh = simulate(a.seed)
    print(stats(sim, frames, sh), flush=True)
    if a.out:
        vid, n = render(frames, a.out)
        wav = build_audio(sim, a.out, frames[-1]["t"])
        final = encode.mux(vid, wav, os.path.join(a.out, "final.mp4"))
        encode.contact_sheet(final, os.path.join(a.out, "sheet.jpg"))
        print("kare", n, final, encode.loudness(final))
