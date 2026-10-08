"""Sarkaç dalgası — "18 pendulums. Wait until they line up again."

Her sarkaç T saniyede (K + i) tam salınım yapar; aradaki desenler (yılan, ikili grup, kaos) kendiliğinden oluşur,
t = T'de hepsi yeniden hizalanır. Başlangıç ve bitiş aynı an → kusursuz döngü. Her sarkaç sağ uca her
vardığında kendi notasını çalar; hizalanmada hepsi aynı anda (akor).
Fizik motoru gerekmez: konum analitik, x_i(t) = A cos(2π (K+i) t / T).

  python3 formats/pendulum.py --out out/pendulum
"""
import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import audio, canvas, produce  # noqa: E402
from lib.canvas import FPS, W  # noqa: E402

N, K, T = 18, 20, 27.0
TAIL = 1.2
CX, Y0, Y1, AMP, BOB_R = W / 2, 640, 1440, 390, 19


def x_of(i, t):
    return CX + AMP * math.cos(2 * math.pi * (K + i) * t / T)


def events():
    ev = []
    for i in range(N):
        per = T / (K + i)
        k = 0
        while k * per <= T + TAIL:
            t = k * per
            midi = audio.scale_note(i, base=55)
            # hizalanma anlarında (t=0, t=T) daha güçlü
            g = 0.55 if (k == 0 or abs(t - T) < 1e-6) else 0.32
            ev.append((t, "pluck", midi, g, 0.75, i))
            k += 1
    for m in (67, 71, 74, 79):
        ev.append((T, "bell", m, 0.35, 0, 0))
    return ev


def render(out_dir, hook="Wait until they line up again"):
    import skia
    from lib.canvas import paint, hsv
    from lib.hud import hud, Pop
    os.makedirs(out_dir, exist_ok=True)
    vid = os.path.join(out_dir, "video.mp4")
    rd = canvas.Renderer(vid, glow=0.9, glow_sigma=12)
    pop = Pop()
    rows = [Y0 + (Y1 - Y0) * i / (N - 1) for i in range(N)]
    n_frames = int((T + TAIL) * FPS)
    track = paint(skia.Color4f(1, 1, 1, 0.07), stroke=2)
    for fi in range(n_frames):
        t = fi / FPS

        def draw(c):
            c.drawLine(CX, Y0 - 40, CX, Y1 + 40, paint(skia.Color4f(1, 1, 1, 0.10), stroke=2))
            for i, y in enumerate(rows):
                c.drawLine(CX - AMP, y, CX + AMP, y, track)
                col = hsv(i / N * 0.85, 0.75, 1.0)
                # iz: son 0,12 sn
                for k in range(6, 0, -1):
                    tx = x_of(i, t - k * 0.02)
                    c.drawCircle(tx, y, BOB_R * (1 - k * 0.1), paint(hsv(i / N * 0.85, 0.75, 1.0, 0.10 * (7 - k) / 6)))
                x = x_of(i, t)
                c.drawLine(CX, y, x, y, paint(hsv(i / N * 0.85, 0.6, 1.0, 0.35), stroke=3))
                c.drawCircle(x, y, BOB_R, paint(col))
            # hizalanma flaşı
            d = abs(t - T)
            if d < 0.4:
                c.drawRect(skia.Rect(CX + AMP - 30, Y0 - 50, CX + AMP + 30, Y1 + 50),
                           paint(skia.Color4f(1, 1, 1, 0.25 * (1 - d / 0.4))))

        def overlay(c):
            left = max(0, math.ceil(T - t - 1e-9))
            if t >= T:
                hud(c, hook, "ALIGNED", None, pop=max(0, 1 - (t - T) / 0.3), big_size=110)
            else:
                hud(c, hook, f"{left}s", "UNTIL THEY ALIGN", pop=pop(left, t))

        rd.frame(draw, overlay)
    rd.close()
    return vid, n_frames / FPS


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out/pendulum")
    a = ap.parse_args()
    clk = produce.Clock()
    vid, secs = render(a.out)
    produce.finish(a.out, vid, events(), secs, cap=6)
    print("süre", clk)
