"""Günlük otomasyon için format adaptörleri.

Her format için:
  choose(rng)            → o günün varyasyonu: modül ayarları, kanca, açıklama değişkenleri
  check(mod, p, seed)    → sadece simülasyon; tempo uygunsa puan (küçük = iyi), değilse None
  make(mod, p, seed, out)→ render + ses; dönen sözlük: final yolu ve tamamlanma bilgisi

Aday tohumdan hem varyasyon hem simülasyon türetilir: aynı tohum = aynı video (tekrar üretilebilir).
Kabul aralıkları CONTEXT.md §3'teki ölçümlerden: ilk olay < 2 sn, uzun boşluk yok, bitiş ~20–28 sn.
"""
import importlib
import math
import os
import random

import numpy as np

from lib import canvas, encode, produce


def _load(name):
    return importlib.import_module(f"formats.{name}")


# ---------------------------------------------------------------- 01 multiply
def multiply_choose(rng):
    return {"hue": rng.random(),
            "hook": rng.choice(["Every bounce = +1 ball", "Each bounce adds a ball", "1 bounce = 1 new ball"])}


def multiply_check(m, p, seed):
    sim, frames, sh = m.simulate(seed)
    if sim.full_t and sh and 19 <= sim.full_t <= 27:
        return abs(sim.full_t - 24)
    return None


def multiply_make(m, p, seed, out):
    sim, frames, sh = m.simulate(seed)
    vid, _ = m.render(frames, out, hook=p["hook"])
    wav = m.build_audio(sim, out, frames[-1]["t"])
    final = encode.mux(vid, wav, os.path.join(out, "final.mp4"))
    encode.contact_sheet(final, os.path.join(out, "sheet.jpg"))
    return {"final": final, "complete": sh is not None, "info": {"balls": sim.counts[-1] + 1}}


# ---------------------------------------------------------------- 02 rings
def rings_choose(rng):
    n = rng.choice([14, 16, 18, 20])
    return {"hue": rng.random(), "N_RINGS": n, "R_STEP": min(26, 380 / (n - 1)),
            "hook": f"Can the ball escape {n} rings?", "n": n}


def rings_apply(m, p):
    m.N_RINGS, m.R_STEP = p["N_RINGS"], p["R_STEP"]


def rings_check(m, p, seed):
    sim, frames, end_t = m.simulate(seed)
    pc = m.pacing(sim, end_t)
    if end_t and 20 <= end_t <= 32 and pc["first"] < 1.5 and pc["max_gap"] < 4.5:
        return pc["max_gap"]
    return None


def rings_make(m, p, seed, out):
    sim, frames, end_t = m.simulate(seed)
    vid, _ = m.render(sim, frames, out, hook=p["hook"])
    wav = m.build_audio(sim, out, frames[-1]["t"])
    final = encode.mux(vid, wav, os.path.join(out, "final.mp4"))
    encode.contact_sheet(final, os.path.join(out, "sheet.jpg"))
    return {"final": final, "complete": end_t is not None, "info": {"end": end_t}}


# ---------------------------------------------------------------- 03 pendulum
def pendulum_choose(rng):
    n = rng.randint(15, 20)
    return {"hue": rng.random(), "N": n, "K": rng.randint(16, 22), "T": float(rng.randint(24, 29)), "n": n,
            "hook": rng.choice(["Wait until they line up again", f"{n} pendulums. Wait for them to line up.",
                                "Watch them line up again"])}


def pendulum_apply(m, p):
    m.N, m.K, m.T = p["N"], p["K"], p["T"]


def pendulum_make(m, p, seed, out):
    vid, secs = m.render(out, hook=p["hook"])
    final = produce.finish(out, vid, m.events(), secs, cap=6)
    return {"final": final, "complete": True, "info": {}}


# ---------------------------------------------------------------- 04 laser
def laser_choose(rng):
    return {"hue": rng.uniform(-0.12, 0.12), "ang": rng.uniform(25, 155), "dx": rng.uniform(-60, 60),
            "hook": rng.choice(["1 laser inside a heart-shaped mirror", "A laser trapped in a heart-shaped mirror"])}


def _laser_pts(m, p):
    poly = m.heart()
    a = math.radians(p["ang"])
    return m.trace(poly, np.array([m.CX + p["dx"], m.CY + 120.0]), np.array([math.cos(a), -math.sin(a)]),
                   m.N_BOUNCE + 1)


def laser_check(m, p, seed):
    pts = _laser_pts(m, p)
    poly = m.heart()
    ok = (pts[:, 0].min() >= poly[:, 0].min() - 1 and pts[:, 0].max() <= poly[:, 0].max() + 1
          and pts[:, 1].min() >= poly[:, 1].min() - 1 and pts[:, 1].max() <= poly[:, 1].max() + 1)
    return 0.0 if ok else None


def laser_make(m, p, seed, out):
    pts = _laser_pts(m, p)
    vid, secs = m.render(pts, out, hook=p["hook"])
    final = produce.finish(out, vid, m.events(pts), secs, cap=5)
    return {"final": final, "complete": True, "info": {}}


# ---------------------------------------------------------------- 05 grow
def grow_choose(rng):
    g, r0 = rng.choice([(1.03, 36), (1.035, 40), (1.04, 44)])
    return {"hue": rng.random(), "GROWTH": g, "R0": r0,
            "hook": rng.choice(["Every bounce, the ball gets bigger", "It grows every time it bounces"])}


def grow_apply(m, p):
    m.GROWTH, m.R0 = p["GROWTH"], p["R0"]


def grow_check(m, p, seed):
    sim, frames = m.simulate(seed)
    if sim.full_t and 18 <= sim.full_t <= 25:
        return abs(sim.full_t - 21.5)
    return None


def grow_make(m, p, seed, out):
    sim, frames = m.simulate(seed)
    ev = sim.events + [(sim.full_t, "shatter", 60, 0.8, 0, 2), (sim.full_t, "bell", 72, 0.5, 0, 0),
                       (sim.full_t, "bell", 79, 0.4, 0, 0)]
    vid, secs = m.render(sim, frames, out, hook=p["hook"])
    final = produce.finish(out, vid, ev, secs)
    return {"final": final, "complete": sim.full_t is not None, "info": {"bounces": sim.n}}


# ---------------------------------------------------------------- 06 galton
def galton_choose(rng):
    n = rng.choice([300, 350, 400, 450])
    return {"hue": rng.uniform(-0.1, 0.1), "N_BALLS": n, "ROWS": rng.choice([10, 11, 12]), "n": n,
            "hook": f"{n} balls. Will they make a bell curve?"}


def galton_apply(m, p):
    m.N_BALLS, m.ROWS = p["N_BALLS"], p["ROWS"]


def galton_check(m, p, seed):
    balls, fill = m.plan(seed)
    stack = max(fill) / m.COLS_IN_BIN * 2 * m.BALL_R * 0.9
    if stack < m.FLOOR - m.BIN_TOP - 15:
        return 0.0
    return None


def galton_make(m, p, seed, out):
    balls, fill = m.plan(seed)
    ev, t_curve = m.events(balls)
    vid, secs = m.render(balls, fill, t_curve, out, hook=p["hook"])
    final = produce.finish(out, vid, ev, secs, cap=5)
    return {"final": final, "complete": True, "info": {"bins": fill}}


# ---------------------------------------------------------------- 07 polygon (heptagon)
def heptagon_choose(rng):
    n = rng.choice([16, 18, 20])
    return {"hue": rng.random(), "SIDES": rng.choice([6, 7, 8]), "N": n, "n": n,
            "hook": f"{n} balls. 1 tiny exit."}


def heptagon_apply(m, p):
    m.N = p["N"]
    m.set_sides(p["SIDES"])


def heptagon_check(m, p, seed):
    sim, frames, end_t = m.simulate(seed, max_t=34)
    ts = sorted(sim.out.values())
    gaps = [b - a for a, b in zip([0.0] + ts, ts)]
    if end_t and 19 <= end_t <= 32 and gaps and max(gaps) < 5.0:
        return max(gaps)
    return None


def heptagon_make(m, p, seed, out):
    sim, frames, end_t = m.simulate(seed)
    ev = sim.events + [(end_t + 0.03 * q, "bell", x, 0.4, 0, 0) for q, x in enumerate((64, 68, 71, 76))]
    vid, secs = m.render(sim, frames, end_t, out, hook=p["hook"])
    final = produce.finish(out, vid, ev, secs, cap=5)
    return {"final": final, "complete": end_t is not None, "info": {"end": end_t}}


# ---------------------------------------------------------------- 08 colorwar
PALETTE = [("RED", 0.0), ("ORANGE", 0.07), ("YELLOW", 0.14), ("GREEN", 0.36), ("CYAN", 0.5), ("BLUE", 0.62),
           ("PURPLE", 0.76), ("PINK", 0.9)]


def colorwar_choose(rng):
    while True:
        four = sorted(rng.sample(PALETTE, 4), key=lambda c: c[1])
        hs = [h for _, h in four]
        if min((b - a) for a, b in zip(hs, hs[1:] + [hs[0] + 1])) >= 0.12:
            break
    rng.shuffle(four)
    return {"colors": four, "hook": "4 colors. Only 1 survives.",
            "names": [n.capitalize() for n, _ in four]}


def colorwar_apply(m, p):
    m.NAMES = [n for n, _ in p["colors"]]
    m.HUES = [h for _, h in p["colors"]]


def colorwar_check(m, p, seed):
    sim, frames, end_t = m.simulate(seed, max_t=34)
    ts = sorted(sim.dead.values())
    if end_t and 20 <= end_t <= 31 and len(ts) == 3:
        return abs(ts[1] - ts[0] - 2) + abs(ts[2] - ts[1] - 2)      # elemeler ~2 sn arayla en iyisi
    return None


def colorwar_make(m, p, seed, out):
    sim, frames, end_t = m.simulate(seed)
    w = sim.alive()[0]
    ev = sim.events + [(end_t + 0.04 * q, "bell", m.NOTES[w] + d, 0.45, 0, 0) for q, d in enumerate((0, 4, 7, 12))]
    vid, secs = m.render(sim, frames, end_t, out, hook=p["hook"])
    final = produce.finish(out, vid, ev, secs, cap=4)
    return {"final": final, "complete": end_t is not None, "info": {"winner": m.NAMES[w]}}


# ---------------------------------------------------------------- 09 breakout
def breakout_choose(rng):
    return {"hue": rng.random(), "hook": rng.choice(["Every brick = +1 ball", "1 brick = 1 new ball"])}


def breakout_check(m, p, seed):
    sim, frames, end_t = m.simulate(seed, max_t=32)
    ts = [t for t, _, _ in sim.broken]
    gaps = [b - a for a, b in zip(ts, ts[1:])]
    if end_t and 19 <= end_t <= 28 and gaps and max(gaps) < 1.5:
        return abs(end_t - 23)
    return None


def breakout_make(m, p, seed, out):
    sim, frames, end_t = m.simulate(seed)
    ev = sim.events + [(end_t + 0.04 * q, "bell", x, 0.45, 0, 0) for q, x in enumerate((60, 64, 67, 72, 76))]
    vid, secs = m.render(sim, frames, end_t, out, hook=p["hook"])
    final = produce.finish(out, vid, ev, secs, cap=5)
    return {"final": final, "complete": end_t is not None, "info": {"balls": len(sim.balls)}}


# ---------------------------------------------------------------- 10 survivor
def survivor_choose(rng):
    n = rng.choice([10, 12, 14])
    return {"hue": rng.random(), "N": n, "n": n,
            "hook": rng.choice(["Which number survives?", "Pick a number. Which one survives?"])}


def survivor_apply(m, p):
    m.N = p["N"]


def survivor_check(m, p, seed):
    sim, frames, end_t = m.simulate(seed, max_t=32)
    ts = sorted(t for t, _, _ in sim.dead.values())
    gaps = [b - a for a, b in zip([0.0] + ts, ts)]
    if end_t and 19 <= end_t <= 30 and ts and ts[0] > 1.2 and max(gaps) < 5.5:
        return max(gaps)
    return None


def survivor_make(m, p, seed, out):
    sim, frames, end_t = m.simulate(seed)
    ev = sim.events + [(end_t + 0.04 * q, "bell", x, 0.45, 0, 0) for q, x in enumerate((60, 64, 67, 72, 76))]
    vid, secs = m.render(sim, frames, end_t, out, hook=p["hook"])
    final = produce.finish(out, vid, ev, secs, cap=5)
    return {"final": final, "complete": end_t is not None, "info": {"winner": list(sim.balls)}}


# ---------------------------------------------------------------- 11 marble race
def marble_race_choose(rng):
    return {"hook": rng.choice(["Which color wins?", "Pick a color. Which one wins?"])}


def marble_race_check(m, p, seed):
    sim, frames, first, ch = m.simulate(seed, max_t=36)
    fin = sorted(sim.finished.values())
    if first and 17 <= first <= 26 and ch >= 6:
        return -ch + (fin[1] - fin[0] if len(fin) > 1 else 3)
    return None


def marble_race_make(m, p, seed, out):
    sim, frames, first, ch = m.simulate(seed)
    vid, secs = m.render(sim, frames, first, out, hook=p["hook"])
    final = produce.finish(out, vid, sim.events, secs, cap=5)
    win = min(sim.finished, key=sim.finished.get) if sim.finished else None
    return {"final": final, "complete": first is not None, "info": {"winner": m.NAMES[win] if win is not None else None}}


# ---------------------------------------------------------------- 12 domino
def domino_choose(rng):
    k = rng.choice([1.3, 1.33, 1.36])
    n = rng.choice([20, 21, 22, 23])
    h = 10 * k ** (n - 1) / 1000
    label = f"{h:.1f} m" if h >= 1 else f"{h * 100:.0f} cm"
    return {"hue": rng.random(), "K": k, "N": n, "SLOWMO": rng.choice([0.12, 0.16, 0.2, 0.25, 0.3, 0.35]), "n": n, "size": label,
            "hook": f"Domino #1: 1 cm. Domino #{n}: {label}."}


def domino_apply(m, p):
    m.K, m.N, m.SLOWMO = p["K"], p["N"], p["SLOWMO"]


def domino_check(m, p, seed):
    sim, frames, end_t = m.simulate()
    if end_t and 16 <= end_t <= 26 and len(sim.landed) == m.N:
        return abs(end_t - 21)
    return None


def domino_make(m, p, seed, out):
    sim, frames, end_t = m.simulate()
    vid, secs = m.render(sim, frames, end_t, out, hook=p["hook"])
    final = produce.finish(out, vid, m.events(sim, end_t), secs, cap=6, reverb=0.25)
    return {"final": final, "complete": end_t is not None, "info": {"end": end_t}}


# ---------------------------------------------------------------- kayıt
# hue: palet döndürülebilir mi (renk adı taşıyan formatlarda hayır)
FORMATS = {
    "multiply": dict(choose=multiply_choose, check=multiply_check, make=multiply_make),
    "rings": dict(choose=rings_choose, apply=rings_apply, check=rings_check, make=rings_make),
    "pendulum": dict(choose=pendulum_choose, apply=pendulum_apply, check=None, make=pendulum_make),
    "laser": dict(choose=laser_choose, check=laser_check, make=laser_make),
    "grow": dict(choose=grow_choose, apply=grow_apply, check=grow_check, make=grow_make),
    "galton": dict(choose=galton_choose, apply=galton_apply, check=galton_check, make=galton_make),
    "heptagon": dict(choose=heptagon_choose, apply=heptagon_apply, check=heptagon_check, make=heptagon_make),
    "colorwar": dict(choose=colorwar_choose, apply=colorwar_apply, check=colorwar_check, make=colorwar_make),
    "breakout": dict(choose=breakout_choose, check=breakout_check, make=breakout_make),
    "survivor": dict(choose=survivor_choose, apply=survivor_apply, check=survivor_check, make=survivor_make),
    "marble_race": dict(choose=marble_race_choose, check=marble_race_check, make=marble_race_make),
    "domino": dict(choose=domino_choose, apply=domino_apply, check=domino_check, make=domino_make),
}


def prepare(name, seed):
    """Tohumdan varyasyonu üretir, modülü ayarlar. Döner: (modül, parametreler)."""
    spec = FORMATS[name]
    m = _load(name)
    p = spec["choose"](random.Random(seed * 7919 + 17))
    canvas.HUE_SHIFT = p.get("hue", 0.0)
    if spec.get("apply"):
        spec["apply"](m, p)
    return m, p


def check(name, seed):
    m, p = prepare(name, seed)
    fn = FORMATS[name]["check"]
    return 0.0 if fn is None else fn(m, p, seed)


def make(name, seed, out):
    m, p = prepare(name, seed)
    os.makedirs(out, exist_ok=True)
    r = FORMATS[name]["make"](m, p, seed, out)
    r["params"] = {k: v for k, v in p.items() if k != "colors"}
    if "colors" in p:
        r["params"]["colors"] = [n for n, _ in p["colors"]]
    return r
