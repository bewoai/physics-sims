"""Lazer ip sanatı — "1 laser inside a heart-shaped mirror".

Kalp eğrisi ayna; ışın her çarpmada yansır ve geçtiği yol kalıcı, yarı saydam bir çizgi bırakır.
Kalp bilardosu kaotik olduğu için ışın zamanla kalbin içini doldurur. Sekme hızı üstel artar:
başta ışının yolculuğu görülür, sonda saniyede yüzlerce sekme → parlayan kalp (ödül).

  python3 formats/laser.py --out out/laser
"""
import argparse
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import audio, canvas, produce  # noqa: E402
from lib.canvas import FPS, W  # noqa: E402

CX, CY, S = W / 2, 1060, 26.5
N_BOUNCE, T_END, TAU, HOLD = 3000, 24.0, 4.0, 2.6
A_COEF = N_BOUNCE / (math.exp(T_END / TAU) - 1)


def heart(n=720):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x = 16 * np.sin(t) ** 3
    y = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
    return np.stack([CX + S * x, CY - S * y], 1)


def trace(poly, p, d, n):
    a = poly
    b = np.roll(poly, -1, 0)
    e = b - a
    pts = [p.copy()]
    seg_prev = -1
    for _ in range(n):
        # ışın p + s d ile kenar a + u e kesişimi
        den = d[0] * e[:, 1] - d[1] * e[:, 0]
        ap = a - p
        with np.errstate(divide="ignore", invalid="ignore"):
            s = (ap[:, 0] * e[:, 1] - ap[:, 1] * e[:, 0]) / den
            u = (ap[:, 0] * d[1] - ap[:, 1] * d[0]) / den
        ok = (np.abs(den) > 1e-12) & (s > 1e-6) & (u >= 0) & (u <= 1)
        ok[seg_prev] = False
        idx = np.where(ok)[0]
        k = idx[np.argmin(s[idx])]
        p = p + s[k] * d
        nrm = np.array([e[k, 1], -e[k, 0]])
        nrm /= np.linalg.norm(nrm)
        d = d - 2 * np.dot(d, nrm) * nrm
        d /= np.linalg.norm(d)
        pts.append(p.copy())
        seg_prev = k
    return np.array(pts)


def b_of(t):
    return A_COEF * (math.exp(min(t, T_END) / TAU) - 1)


def events(pts):
    ev = []
    for k in range(1, len(pts)):
        # k. sekmenin zamanı: b(t) = k → t = τ ln(k/A + 1)
        t = TAU * math.log(k / A_COEF + 1)
        x, y = pts[k]
        ang = (math.atan2(y - CY, x - CX) + math.pi) / (2 * math.pi)
        g = 0.5 if k < 60 else max(0.12, 0.5 * (60 / k) ** 0.35)
        ev.append((t, "pluck", audio.scale_note(int(ang * 15), base=62), g, (x - CX) / 450, 0))
    for m in (62, 66, 69, 74, 78):
        ev.append((T_END + 0.05, "bell", m, 0.4, 0, 0))
    return ev


def render(pts, out_dir, hook="1 laser inside a heart-shaped mirror"):
    import skia
    from lib.canvas import H, paint, hsv
    from lib.hud import hud, Pop
    os.makedirs(out_dir, exist_ok=True)
    vid = os.path.join(out_dir, "video.mp4")
    rd = canvas.Renderer(vid, glow=0.8, glow_sigma=10)
    pop = Pop()
    acc = skia.Surface(W, H)
    acc.getCanvas().clear(skia.Color4f(0, 0, 0, 0))
    poly = heart()
    path = skia.Path()
    path.moveTo(*poly[0])
    for q in poly[1:]:
        path.lineTo(*q)
    path.close()
    drawn = 0
    n_frames = int((T_END + HOLD) * FPS)
    for fi in range(n_frames):
        t = fi / FPS
        b = b_of(t)
        done = min(int(b), N_BOUNCE)
        ac = acc.getCanvas()
        while drawn < done:
            k = drawn
            hue = 0.92 + 0.25 * k / N_BOUNCE
            alpha = 0.55 if k < 40 else max(0.05, 0.55 * (40 / k) ** 0.6)
            ac.drawLine(*pts[k], *pts[k + 1], paint(hsv(hue, 0.7, 1.0, alpha), stroke=2.2, blend=skia.BlendMode.kPlus))
            drawn += 1
        img = acc.makeImageSnapshot()
        frac = b - done if done < N_BOUNCE else 0.0

        def draw(c):
            c.drawImage(img, 0, 0)
            pulse = 0.0 if t < T_END else 0.5 * math.exp(-(t - T_END) / 0.8)
            c.drawPath(path, paint(skia.Color4f(1, 0.75, 0.85, 0.8 + pulse), stroke=5))
            if done < N_BOUNCE:
                p0, p1 = pts[done], pts[done + 1]
                head = p0 + (p1 - p0) * frac
                c.drawLine(*p0, *head, paint(skia.Color4f(1, 0.35, 0.55, 1.0), stroke=4))
                c.drawCircle(*head, 9, paint(skia.Color4f(1, 1, 1, 1)))

        def overlay(c):
            hud(c, hook, done, "BOUNCES", pop=pop(done, t) if done < 50 else 0)

        rd.frame(draw, overlay)
    rd.close()
    return vid, n_frames / FPS


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out/laser")
    a = ap.parse_args()
    clk = produce.Clock()
    poly = heart()
    ang = math.radians(71.3)
    pts = trace(poly, np.array([CX + 40, CY + 120.0]), np.array([math.cos(ang), -math.sin(ang)]), N_BOUNCE + 1)
    inside = np.mean((np.abs(pts[:, 0] - CX) < 16 * S + 2))
    print("ışın noktaları", pts.shape, "kalp içinde", inside, flush=True)
    vid, secs = render(pts, a.out)
    produce.finish(a.out, vid, events(pts), secs, cap=5)
    print("süre", clk)
