"""Format C — "1 Ball vs 5000 Balls" (kademeli parametre).

Referansın kademe yapısı, bizim içeriğimizle: aynı cam bardağa her kademede daha çok top dökülür
(1 → 10 → 100 → 1000 → 5000). Toplar döküm sırasına göre renk değiştirir, bardakta gökkuşağı katmanları
oluşur. Kademeler giderek uzar; son kademede bardak taşar (ödül).

  python3 formats/pour.py --stats
  python3 formats/pour.py --out out/c
"""
import argparse
import math
import os
import random
import sys

import numpy as np
import pymunk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import audio, canvas, encode  # noqa: E402
from lib.canvas import FPS, W  # noqa: E402

SUB = 3
BALL_R = 6.5
CUP_W, CUP_H, CUP_BOTTOM = 470, 560, 1440        # iç genişlik, yükseklik, taban y
CUP_X0, CUP_X1 = W / 2 - CUP_W / 2, W / 2 + CUP_W / 2
CUP_TOP = CUP_BOTTOM - CUP_H
WALL_T = 9
FLOOR_Y = 1500
# (top sayısı, döküm süresi, kademe süresi)
STAGES = [(1, 0.1, 2.6), (10, 0.9, 3.2), (100, 1.8, 4.2), (1000, 3.2, 6.0), (5000, 6.5, 10.0)]
WALL, BALL = 1, 2


def radius(n):
    # tek top ve 10 top, küçük boyutta bardakta kaybolur; bu kademelerde top büyük
    return {1: 18.0, 10: 12.0}.get(n, BALL_R)


def stage_sim(n, pour_t, dur, seed):
    rng = random.Random(seed)
    r = radius(n)
    s = pymunk.Space()
    s.gravity = (0, 1500)
    s.iterations = 12
    s.use_spatial_hash(BALL_R * 2.2, 12000)
    sb = s.static_body
    segs = [
        pymunk.Segment(sb, (CUP_X0 - WALL_T, CUP_TOP), (CUP_X0 - WALL_T, CUP_BOTTOM + WALL_T), WALL_T),
        pymunk.Segment(sb, (CUP_X1 + WALL_T, CUP_TOP), (CUP_X1 + WALL_T, CUP_BOTTOM + WALL_T), WALL_T),
        pymunk.Segment(sb, (CUP_X0 - WALL_T, CUP_BOTTOM + WALL_T), (CUP_X1 + WALL_T, CUP_BOTTOM + WALL_T), WALL_T),
        pymunk.Segment(sb, (-400, FLOOR_Y + 40), (W + 400, FLOOR_Y + 40), 40),
    ]
    for g in segs:
        g.elasticity, g.friction, g.collision_type = 0.35, 0.6, WALL
    s.add(*segs)

    events = []
    bodies = []
    t = [0.0]

    def begin(arb, space, data):
        a, b = arb.bodies
        rv = (a.velocity - b.velocity).length
        if rv > 260:
            x = a.position.x if a.body_type == pymunk.Body.DYNAMIC else b.position.x
            g = min(0.5, rv / 2600)
            if n <= 10:
                events.append((t[0], "pluck", audio.scale_note(rng.randrange(6), base=76), g * 0.8, (x - W / 2) / 500, 0))
            events.append((t[0], "tick", 60, g, (x - W / 2) / 500, rng.randrange(8)))

    s.on_collision(BALL, WALL, begin=begin)
    s.on_collision(BALL, BALL, begin=begin)

    spawned = 0
    frames = []
    dt = 1 / FPS / SUB
    emit_w = 60 if n <= 10 else (160 if n <= 100 else CUP_W - 40)
    while t[0] < dur:
        # döküm: süre boyunca eşit hızla, bardağın üstündeki bantta
        target = n if pour_t <= 0.1 else min(n, int(n * t[0] / pour_t) + 1)
        while spawned < target:
            b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, r))
            # bardağa yakın ve hızlı: ilk sürümde düşüş ~1 sn sürüyor, her kademe başında sessiz boşluk oluyordu
            b.position = (W / 2 + rng.uniform(-emit_w / 2, emit_w / 2), CUP_TOP - 170 + rng.uniform(-60, 60))
            b.velocity = (rng.uniform(-30, 30), rng.uniform(700, 900))
            sh = pymunk.Circle(b, r)
            sh.elasticity, sh.friction, sh.collision_type = (0.55 if n == 1 else 0.3), 0.45, BALL
            s.add(b, sh)
            bodies.append(b)
            spawned += 1
        for _ in range(SUB):
            s.step(dt)
            t[0] += dt
        pos = np.array([(b.position.x, b.position.y) for b in bodies], np.float32) if bodies else np.zeros((0, 2), np.float32)
        frames.append(pos)
        # ekrandan çıkan topları sabitle (hesap yükü)
        for b in bodies:
            if b.body_type == pymunk.Body.DYNAMIC and (b.position.x < -60 or b.position.x > W + 60):
                b.velocity = (0, 0)
    return frames, events


def simulate(stats_only=False):
    out = []
    for k, (n, pour_t, dur) in enumerate(STAGES):
        fr, ev = stage_sim(n, pour_t, dur, seed=11 + k)
        last = fr[-1]
        inside = int(np.sum((last[:, 0] > CUP_X0) & (last[:, 0] < CUP_X1) & (last[:, 1] < CUP_BOTTOM) & (last[:, 1] > CUP_TOP)))
        top = float(last[:, 1].min()) if len(last) else 0
        print(f"{n:>5} top: bardakta={inside} en_üst_y={top:.0f} (ağız y={CUP_TOP}) olay={len(ev)}", flush=True)
        out.append((n, fr, ev))
    return out


def label(n):
    return f"{n} Ball" if n == 1 else f"{n} Balls"


def render(stages, out_dir, hook="1 Ball VS 5000 Balls"):
    import skia
    from lib.canvas import paint, text, hsv
    os.makedirs(out_dir, exist_ok=True)
    vid = os.path.join(out_dir, "video.mp4")
    rd = canvas.Renderer(vid, glow=0.35, glow_sigma=10)
    T = 0.0
    glass_fill = paint(skia.Color4f(0.75, 0.85, 1.0, 0.06))
    glass_edge = paint(skia.Color4f(0.85, 0.92, 1.0, 0.75), stroke=WALL_T * 1.6)
    glass_hi = paint(skia.Color4f(1, 1, 1, 0.22), stroke=5)
    floor = paint(skia.Color4f(0.10, 0.10, 0.13, 1))
    cup = skia.Path()
    cup.moveTo(CUP_X0 - WALL_T, CUP_TOP)
    cup.lineTo(CUP_X0 - WALL_T, CUP_BOTTOM + WALL_T)
    cup.lineTo(CUP_X1 + WALL_T, CUP_BOTTOM + WALL_T)
    cup.lineTo(CUP_X1 + WALL_T, CUP_TOP)
    for k, (n, frames, _) in enumerate(stages):
        cols = [hsv((i / max(1, n - 1)) * 0.85 + 0.0, 0.72, 1.0) if n > 1 else hsv(0.55, 0.6, 1.0) for i in range(n)]
        pts = [paint(c) for c in cols]
        rb = radius(n)
        for fi, pos in enumerate(frames):
            t = fi / FPS
            gt = T + t

            def draw(c):
                c.drawRect(skia.Rect(0, FLOOR_Y, W, 1920), floor)
                c.drawRect(skia.Rect(CUP_X0, CUP_TOP, CUP_X1, CUP_BOTTOM), glass_fill)
                for i in range(len(pos)):
                    c.drawCircle(float(pos[i, 0]), float(pos[i, 1]), rb, pts[i])
                c.drawPath(cup, glass_edge)
                c.drawLine(CUP_X0 + 14, CUP_TOP + 30, CUP_X0 + 14, CUP_BOTTOM - 40, glass_hi)

            def overlay(c):
                if k == 0:
                    a = 1.0 if t < 2.0 else max(0.0, 1 - (t - 2.0) / 0.4)
                    text(c, hook, W / 2, 330, size=74, weight=900, color=skia.Color4f(1, 1, 1, a))
                    if a < 1:
                        text(c, label(n), W / 2, 330, size=86, weight=900, color=skia.Color4f(1, 1, 1, 1 - a))
                else:
                    pop = max(0.0, 1 - t / 0.25)
                    text(c, label(n), W / 2, 330, size=int(86 + 24 * pop), weight=900)

            rd.frame(draw, overlay)
        T += len(frames) / FPS
    return vid, rd.close()


def build_audio(stages, out_dir):
    total = sum(len(fr) for _, fr, _ in stages) / FPS
    mx = audio.Mix(total)
    T = 0.0
    for k, (n, fr, ev) in enumerate(stages):
        if k > 0:
            mx.add(T, "whoosh", 60, 0.25, 0, k)
        for t, kind, midi, g, pan, seed in ev:
            mx.add(T + t, kind, midi, g, pan, seed)
        T += len(fr) / FPS
    return mx.render(os.path.join(out_dir, "mix.wav"), cap=6, grow=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    stages = simulate()
    if a.out:
        vid, n = render(stages, a.out)
        wav = build_audio(stages, a.out)
        final = encode.mux(vid, wav, os.path.join(a.out, "final.mp4"))
        encode.contact_sheet(final, os.path.join(a.out, "sheet.jpg"))
        print("kare", n, final, encode.loudness(final))
