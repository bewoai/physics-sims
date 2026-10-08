"""Domino büyütme — "Domino #1: 1 cm. Domino #22: 5.5 m."

Her domino bir öncekinin 1,35 katı (gerçekte devrilme zinciri ~1,5 kata kadar çalışır). İlki 1 cm, 18.'si
1,65 m. Kamera düşen dominoyu izler ve sürekli uzaklaşır; ses küçükten büyüğe tıkırtıdan derin gümlemeye iner.
Gerçek ölçek: birim mm, g = 9810 mm/s² (yavaş çekim katsayısı SLOWMO ile).

  python3 formats/domino.py --stats
  python3 formats/domino.py --out out/domino
"""
import argparse
import math
import os
import sys

import pymunk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import canvas, produce  # noqa: E402
from lib.canvas import FPS, W  # noqa: E402

N, H0, K = 22, 10.0, 1.35          # adet, ilk yükseklik (mm), büyüme → sonuncusu 5,5 m
THICK, GAP = 0.2, 0.55             # kalınlık/yükseklik, aralık/yükseklik
SLOWMO = 0.3                       # yerçekimi çarpanı: 0,55 ile 18 domino 8 sn sürdü
SUB = 12
DOM, GROUND = 1, 2
GROUND_Y_SCREEN = 1460


def layout():
    xs, x = [], 0.0
    for i in range(N):
        h = H0 * K ** i
        xs.append((x, h))
        x += h * THICK + h * GAP
    return xs


class Sim:
    def __init__(self):
        s = self.space = pymunk.Space()
        s.gravity = (0, 9810 * SLOWMO)            # y aşağı pozitif
        s.iterations = 30
        s.collision_slop = 0.02
        g = pymunk.Segment(s.static_body, (-500, 1), (20000, 1), 1)      # üst yüzey y=0
        g.friction, g.collision_type = 0.9, GROUND
        s.add(g)
        self.doms = []
        for i, (x, h) in enumerate(layout()):
            w = h * THICK
            m = w * h * 0.001
            b = pymunk.Body(m, pymunk.moment_for_box(m, (w, h)))
            b.position = (x + w / 2, -h / 2)
            sh = pymunk.Poly.create_box(b, (w, h))
            sh.friction, sh.elasticity, sh.collision_type = 0.5, 0.05, DOM
            sh.idx = i
            s.add(b, sh)
            self.doms.append((b, w, h))
        # ilk dominoya küçük itiş
        # ilk dominoya tepesinden yatay darbe (kütle merkezine verilen dönüş alt köşeyi zemine gömüp sönüyordu)
        b0, w0, h0 = self.doms[0]
        b0.apply_impulse_at_local_point((b0.mass * 45, 0), (0, -h0 / 2))
        self.t = 0.0
        self.hit = {}            # i → i'nin i+1'e ilk çarpma zamanı
        self.landed = {}         # i → yere yattığı zaman
        s.on_collision(DOM, DOM, begin=self._dd)

    def _dd(self, arb, space, data):
        a, b = arb.shapes
        i, j = sorted((a.idx, b.idx))
        if j == i + 1 and i not in self.hit:
            self.hit[i] = self.t

    def step_frame(self):
        dt = 1 / FPS / SUB
        for _ in range(SUB):
            self.space.step(dt)
            self.t += dt
        for i, (b, w, h) in enumerate(self.doms):
            if i not in self.landed and abs(b.angle) > math.radians(70):
                self.landed[i] = self.t

    def active(self):
        """Şu an devrilmekte olan en büyük domino."""
        k = 0
        for i, (b, w, h) in enumerate(self.doms):
            if abs(b.angle) > math.radians(3):
                k = i
        return k


def simulate(max_t=40.0, tail=2.4):
    sim = Sim()
    frames = []
    end_t = None
    while sim.t < max_t:
        sim.step_frame()
        frames.append((sim.t, [(b.position.x, b.position.y, b.angle) for b, _, _ in sim.doms], sim.active()))
        if N - 1 in sim.landed and end_t is None:
            end_t = sim.t
        if end_t is not None and sim.t - end_t > tail:
            break
        if sim.t > 3 and sim.active() == 0:
            break
    return sim, frames, end_t


def size_label(h_mm):
    if h_mm < 1000:
        return f"{h_mm / 10:.0f} cm" if h_mm >= 100 else f"{h_mm / 10:.1f} cm"
    return f"{h_mm / 1000:.2f} m"


def events(sim, end_t):
    ev = []
    for i, t in sim.hit.items():
        midi = 84 - 2.6 * i
        g = 0.35 + 0.03 * i
        ev.append((t, "thud", midi, g, 0, i))
        ev.append((t, "tick", 60, max(0.05, 0.4 - 0.03 * i), 0, i))
    for i, t in sim.landed.items():
        if i >= 8:
            ev.append((t, "thud", 46 - 0.8 * (i - 8), 0.4 + 0.04 * (i - 8), 0, i))
    if end_t:
        ev += [(end_t, "thud", 28, 1.0, 0, 0), (end_t, "shatter", 50, 0.3, 0, 1)]
        ev += [(end_t + 0.05 * q, "bell", m, 0.35, 0, 0) for q, m in enumerate((55, 62, 67, 74))]
    return ev


def render(sim, frames, end_t, out_dir, hook="Domino #1: 1 cm. Domino #22: 5.5 m."):
    import skia
    from lib.canvas import paint, hsv
    from lib.hud import hud, Pop
    os.makedirs(out_dir, exist_ok=True)
    vid = os.path.join(out_dir, "video.mp4")
    rd = canvas.Renderer(vid, glow=0.35, glow_sigma=10)
    pop = Pop()
    lay = layout()
    fills = [paint(hsv(0.0 + 0.85 * i / (N - 1), 0.7, 0.95)) for i in range(N)]
    edge = paint(skia.Color4f(1, 1, 1, 0.9), stroke=2.5)
    ground = paint(skia.Color4f(0.85, 0.9, 1.0, 0.7), stroke=6)
    # kamera: odak x ve görüş genişliği (mm), yumuşak
    fx, vw = lay[0][0], lay[0][1] * 6
    for t, doms, act in frames:
        nxt = min(N - 1, act + 1)
        tx = (lay[act][0] + lay[nxt][0] + lay[nxt][1] * THICK) / 2
        tw = max(lay[nxt][1] * 2.3, (lay[nxt][0] - lay[max(0, act - 2)][0]) * 1.15)   # 3,2 ile dominolar ekranın altında küçük kaldı
        fx += (tx - fx) * 0.08
        vw += (tw - vw) * 0.06
        s = W / vw

        def to_screen(x, y):
            return W / 2 + (x - fx) * s, GROUND_Y_SCREEN + y * s

        def draw(c):
            c.drawLine(0, GROUND_Y_SCREEN, W, GROUND_Y_SCREEN, ground)
            for i, (x, y, a) in enumerate(doms):
                w, h = lay[i][1] * THICK * s, lay[i][1] * s
                if w < 0.6:
                    continue
                sx, sy = to_screen(x, y)
                if sx < -h or sx > W + h:
                    continue
                c.save()
                c.translate(sx, sy)
                c.rotate(math.degrees(a))
                r = skia.Rect(-w / 2, -h / 2, w / 2, h / 2)
                c.drawRect(r, fills[i])
                if w > 4:
                    c.drawRect(r, edge)
                c.restore()

        def overlay(c):
            h = lay[act][1]
            if end_t is not None and t >= end_t:
                hud(c, hook, size_label(lay[-1][1]), f"DOMINO #{N}", pop=max(0, 1 - (t - end_t) / 0.3))
            else:
                hud(c, hook, size_label(h), f"DOMINO #{act + 1}", pop=pop(act, t))

        rd.frame(draw, overlay)
    rd.close()
    return vid, frames[-1][0]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    clk = produce.Clock()
    sim, frames, end_t = simulate()
    print(f"bitiş={end_t} çarpmalar={ {k: round(v, 2) for k, v in sorted(sim.hit.items())} } devrilen={len(sim.landed)}",
          flush=True)
    if a.out and end_t:
        vid, secs = render(sim, frames, end_t, a.out)
        produce.finish(a.out, vid, events(sim, end_t), secs, cap=6, reverb=0.25)
        print("süre", clk)
