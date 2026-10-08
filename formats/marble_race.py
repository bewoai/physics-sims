"""Misket yarışı — "Which color wins?"

8 renkli misket uzun bir parkurdan iner: zikzak rampalar, çivi alanı, dönen pervaneler, tampon, huni.
Kamera lideri takip eder; solda canlı sıralama haritası (her misketin parkurdaki ilerlemesi). İzleyici bir
renk tutar; liderlik değişimleri gerilimi taşır. Tohum taraması: liderlik değişimi çok, finiş yakın olanlar.

  python3 formats/marble_race.py --search 40
  python3 formats/marble_race.py --seed 3 --out out/marble_race
"""
import argparse
import math
import os
import random
import sys

import pymunk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import audio, canvas, produce  # noqa: E402
from lib.canvas import FPS, H, W  # noqa: E402

SUB = 4
XL, XR = 90, 990
BALL_R = 19
NAMES = ["RED", "ORANGE", "YELLOW", "GREEN", "CYAN", "BLUE", "PURPLE", "PINK"]
HUES = [0.0, 0.07, 0.15, 0.33, 0.5, 0.62, 0.76, 0.88]
BALL, STATIC, BUMP = 1, 2, 3
VIEW_Y = 980          # liderin ekrandaki y'si
START_Y = 560


def build_course(space, rng):
    """Statik parkur. Döner: (çizim listesi, pervaneler, finiş y)."""
    sb = space.static_body
    draw = []      # ("seg", a, b, r) | ("circle", c, r, kind)
    spinners = []

    def seg(a, b, r=6, e=0.4, f=0.3):
        s = pymunk.Segment(sb, a, b, r)
        s.elasticity, s.friction, s.collision_type = e, f, STATIC
        space.add(s)
        draw.append(("seg", a, b, r))

    def peg(c, r=9, e=0.5, kind="peg"):
        s = pymunk.Circle(sb, r, c)
        s.elasticity, s.friction = e, 0.2
        s.collision_type = BUMP if kind == "bump" else STATIC
        space.add(s)
        draw.append(("circle", c, r, kind))

    y = START_Y + 80
    # başlangıç: hafif eğimli rampa
    seg((XL, y - 40), (XR - 140, y + 60))
    y += 230
    # A: zikzak rampalar (ilk sürüm 4 rampa / 110 px eğim: lider 27–33 sn'de bitirdi)
    for k in range(3):
        if k % 2 == 0:
            seg((XR, y), (XL + 150, y + 170))
        else:
            seg((XL, y), (XR - 150, y + 170))
        y += 290
    # B: çivi alanı
    for row in range(8):
        off = 0 if row % 2 == 0 else 55
        x = XL + 60 + off
        while x < XR - 40:
            peg((x, y), 10 if rng.random() > 0.15 else 16)
            x += 110
        y += 80
    y += 60
    # C: pervaneler + saptırıcılar
    for k, (sx, w) in enumerate([(330, 2.6), (750, -2.4), (540, 2.9)]):
        body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        body.position = (sx, y)
        body.angular_velocity = w
        arms = []
        for a in (0, math.pi / 2):
            L = 175
            sh = pymunk.Segment(body, (-L * math.cos(a), -L * math.sin(a)), (L * math.cos(a), L * math.sin(a)), 9)
            sh.elasticity, sh.friction, sh.collision_type = 0.6, 0.3, STATIC
            arms.append(sh)
        space.add(body, *arms)
        spinners.append((body, 175))
        if k < 2:
            seg((XL, y - 140), (XL + 120, y - 60))
            seg((XR, y - 140), (XR - 120, y - 60))
        y += 330
    # D: huni → tek sıra, sonra rampalar
    seg((XL, y), (W / 2 - 70, y + 260))
    seg((XR, y), (W / 2 + 70, y + 260))
    y += 380
    for k in range(2):
        if k % 2 == 0:
            seg((XL, y), (XR - 170, y + 160))
        else:
            seg((XR, y), (XL + 170, y + 160))
        y += 280
    # E: tampon alanı (sekme katsayısı > 1 → fırlatır)
    for row in range(3):
        for k in range(4):
            x = XL + 130 + k * 230 + (115 if row % 2 else 0)
            if x < XR - 60:
                peg((x, y), 30, e=1.25, kind="bump")
        y += 170
    y += 80
    finish = y
    # finiş sonrası toplama havuzu
    seg((XL, finish + 260), (XR, finish + 260), 8)
    return draw, spinners, finish


class Sim:
    def __init__(self, seed):
        rng = random.Random(seed)
        s = self.space = pymunk.Space()
        s.gravity = (0, 1700)
        s.iterations = 20
        sb = s.static_body
        for x in (XL - 6, XR + 6):
            w = pymunk.Segment(sb, (x, 0), (x, 20000), 6)
            w.elasticity, w.friction, w.collision_type = 0.5, 0.2, STATIC
            s.add(w)
        self.draw, self.spinners, self.finish = build_course(s, rng)
        self.balls = []
        order = list(range(8))
        rng.shuffle(order)
        for slot, k in enumerate(order):
            b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BALL_R))
            b.position = (XL + 80 + slot * 95 + rng.uniform(-6, 6), START_Y - rng.uniform(0, 30))
            b.velocity = (rng.uniform(-40, 40), 0)
            sh = pymunk.Circle(b, BALL_R)
            sh.elasticity, sh.friction, sh.collision_type = 0.45, 0.25, BALL
            sh.k = k
            s.add(b, sh)
            self.balls.append((b, k))
        self.t = 0.0
        self.finished = {}       # k → zaman
        self.events = []
        self.last = {}
        s.on_collision(BALL, STATIC, post_solve=self._hit)
        s.on_collision(BALL, BUMP, post_solve=self._bump)

    def _hit(self, arb, space, data):
        if not arb.is_first_contact:
            return
        sh = arb.shapes[0] if arb.shapes[0].collision_type == BALL else arb.shapes[1]
        if arb.total_impulse.length < 120 or self.t - self.last.get(sh.k, -1) < 0.08:
            return
        self.last[sh.k] = self.t
        self.events.append((self.t, "pluck", audio.scale_note(sh.k + 3, base=55), min(0.4, arb.total_impulse.length / 1500),
                            (sh.body.position.x - W / 2) / 450, 0))

    def _bump(self, arb, space, data):
        if arb.is_first_contact:
            sh = arb.shapes[0] if arb.shapes[0].collision_type == BALL else arb.shapes[1]
            self.events.append((self.t, "pop", 70 + sh.k, 0.5, (sh.body.position.x - W / 2) / 450, 0))

    def step_frame(self):
        dt = 1 / FPS / SUB
        for _ in range(SUB):
            self.space.step(dt)
            self.t += dt
            for b, k in self.balls:
                if k not in self.finished and b.position.y > self.finish:
                    self.finished[k] = self.t
                    place = len(self.finished)
                    self.events.append((self.t, "bell", [76, 72, 69, 64, 62, 60, 57, 55][place - 1], 0.5 if place == 1 else 0.3,
                                        (b.position.x - W / 2) / 450, 0))
                    if place == 1:
                        self.events += [(self.t + 0.05 * q, "bell", m, 0.4, 0, 0) for q, m in enumerate((64, 68, 71, 76))]


def simulate(seed, max_t=50.0, tail=2.4):
    sim = Sim(seed)
    frames = []
    first = None
    leaders = []
    while sim.t < max_t:
        sim.step_frame()
        pos = {k: (b.position.x, b.position.y, b.angle) for b, k in sim.balls}
        lead = max(pos, key=lambda k: pos[k][1]) if not sim.finished else min(sim.finished, key=sim.finished.get)
        leaders.append(lead)
        frames.append((sim.t, pos, [(sp.angle, sp.position) for sp, _ in sim.spinners], lead, dict(sim.finished)))
        if sim.finished and first is None:
            first = sim.t
        if first is not None and sim.t - first > tail:
            break
    changes = sum(1 for a, b in zip(leaders, leaders[1:]) if a != b)
    return sim, frames, first, changes


def _score(seed):
    sim, fr, first, ch = simulate(seed, max_t=40)
    fin = sorted(sim.finished.values())
    gap = fin[1] - fin[0] if len(fin) > 1 else 9
    return seed, first, ch, gap


def search(n, lo=17, hi=26):
    from multiprocessing import Pool
    with Pool(4) as p:
        res = p.map(_score, range(n))
    good = sorted(((-ch, gap, s, f) for s, f, ch, gap in res if f and lo <= f <= hi), key=lambda r: (r[0], r[1]))
    for ch, gap, s, f in good[:10]:
        print(f"seed={s} finiş={f:.1f} liderlik_değişimi={-ch} ikinciyle_fark={gap:.2f}s")
    if not good:
        print("uygun yok", res[:8])


def render(sim, frames, first, out_dir, hook="Which color wins?"):
    import skia
    from lib.canvas import paint, hsv, text
    from lib.hud import HOOK_Y
    os.makedirs(out_dir, exist_ok=True)
    vid = os.path.join(out_dir, "video.mp4")
    rd = canvas.Renderer(vid, glow=0.55, glow_sigma=10)
    cols = [hsv(h, 0.75, 1.0) for h in HUES]
    ball_p = [paint(c) for c in cols]
    track = paint(skia.Color4f(0.85, 0.9, 1.0, 0.85))
    bump_p = paint(skia.Color4f(1, 1, 1, 0.9), stroke=7)       # içi boş halka: dolu pembe tampon PINK misketle karışıyordu
    spin_p = paint(skia.Color4f(1, 0.85, 0.3, 0.95), stroke=18)
    cam = START_Y - VIEW_Y + 200
    total = sim.finish + 120 - START_Y
    for t, pos, spins, lead, fin in frames:
        # kamera: liderin y'si (finişten sonra sabit), yumuşak takip
        target = min(pos[lead][1], sim.finish + 120) - VIEW_Y
        cam += (target - cam) * 0.12
        oy = -cam

        def draw(c):
            c.save()
            c.translate(0, oy)
            side = paint(skia.Color4f(0.85, 0.9, 1.0, 0.6), stroke=10)
            c.drawLine(XL - 6, cam, XL - 6, cam + H, side)
            c.drawLine(XR + 6, cam, XR + 6, cam + H, side)
            for d in sim.draw:
                if d[0] == "seg":
                    _, a, b, r = d
                    if max(a[1], b[1]) > cam - 50 and min(a[1], b[1]) < cam + H + 50:
                        c.drawLine(*a, *b, paint(skia.Color4f(0.85, 0.9, 1.0, 0.9), stroke=2 * r))
                else:
                    _, cc, r, kind = d
                    if cam - 50 < cc[1] < cam + H + 50:
                        c.drawCircle(*cc, r - 3.5 if kind == "bump" else r, bump_p if kind == "bump" else track)
            for ang, p in spins:
                if cam - 300 < p[1] < cam + H + 300:
                    for a in (ang, ang + math.pi / 2):
                        L = 175
                        c.drawLine(p[0] - L * math.cos(a), p[1] - L * math.sin(a), p[0] + L * math.cos(a), p[1] + L * math.sin(a), spin_p)
            # finiş çizgisi (dama)
            fy = sim.finish
            for q in range(18):
                for r2 in range(2):
                    col = skia.Color4f(1, 1, 1, 1) if (q + r2) % 2 == 0 else skia.Color4f(0.1, 0.1, 0.1, 1)
                    c.drawRect(skia.Rect(XL + q * 50, fy + r2 * 16, XL + (q + 1) * 50, fy + (r2 + 1) * 16), paint(col))
            for k, (x, y, a) in pos.items():
                c.drawCircle(x, y, BALL_R, ball_p[k])
                c.drawLine(x, y, x + BALL_R * 0.7 * math.cos(a), y + BALL_R * 0.7 * math.sin(a),
                           paint(skia.Color4f(1, 1, 1, 0.8), stroke=4))
            c.restore()

        def overlay(c):
            c.drawRect(skia.Rect(0, 0, W, 560), paint(skia.Color4f(0.035, 0.035, 0.05, 0.92)))
            text(c, hook, W / 2, HOOK_Y, size=60, weight=800)
            if fin:
                win = min(fin, key=fin.get)
                k = min(1.0, (t - fin[win]) / 0.3)
                text(c, f"{NAMES[win]} WINS", W / 2, 470, size=int(96 + 20 * (1 - k)), weight=900, color=cols[win], shadow=False)
            else:
                text(c, f"{NAMES[lead]} LEADS", W / 2, 460, size=72, weight=900, color=cols[lead], shadow=False)
            # sıralama haritası (sol kenar)
            mx, my0, my1 = 40, 640, 1420
            c.drawLine(mx, my0, mx, my1, paint(skia.Color4f(1, 1, 1, 0.3), stroke=4))
            c.drawLine(mx - 14, my1, mx + 14, my1, paint(skia.Color4f(1, 1, 1, 0.8), stroke=4))
            for k, (x, y, a) in pos.items():
                prog = min(1.0, max(0.0, (y - START_Y) / total))
                c.drawCircle(mx, my0 + (my1 - my0) * prog, 11, ball_p[k])

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
    sim, frames, first, ch = simulate(a.seed)
    print(f"finiş={first} liderlik_değişimi={ch} sıralama={sorted(sim.finished, key=sim.finished.get)}", flush=True)
    if a.out:
        vid, secs = render(sim, frames, first, a.out)
        produce.finish(a.out, vid, sim.events, secs, cap=5)
        print("süre", clk)
