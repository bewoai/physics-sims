"""Konuya özel müzik (kullanıcı: "arkaya konuyla alakalı kendi yaptığın müzikleri ekleyeceksin"). Telifsiz:
melodi kuralla üretilir (tohumlu), tüm çalgılar numpy ile sentezlenir. Hazır şarkı ya da bilinen melodi yok.

Bölüm JSON'u "music": {"theme": "musette", "bpm": 150, "seed": 3, "moods": {sahne türü: ruh hali}}.
Temalar:
  musette  Paris, 1890'lar: valse musette (3/4). Akordeon (üç dil, "musette" akordu: ±7 sent → titreşim),
           sol el bas + akor vuruşu (um-pa-pa), fırça trampet.
Ruh halleri: mystery (gizem: tutulan akordeon akoru + müzik kutusu + saat tıkırtısı), waltz, waltz_dark (seyrek,
pes), pizz (pizzicato; Mors bip'lerine yer bırakır), tension (davul, trampet rulosu, pedal bas), rise (majöre geçiş),
finale (majör vals + bitiş akoru).
Ruh hali değişimi sahne başından sonraki ilk ölçü başına oturur (müzik ölçü ortasında kırılmasın).
Çıktı iki kanal (stem): "melody" ve "acc" — miks anlatım sırasında melodiyi daha çok kısar.
"""
import math
import random

import numpy as np

from lib import audio

SR = 48000

CH = {"Dm": (2, [2, 5, 9]), "Gm": (7, [7, 10, 2]), "A7": (9, [9, 1, 4, 7]), "A": (9, [9, 1, 4]),
      "Bb": (10, [10, 2, 5]), "D": (2, [2, 6, 9]), "Bm": (11, [11, 2, 6]), "Em": (4, [4, 7, 11]),
      "G": (7, [7, 11, 2]), "C": (0, [0, 4, 7]), "F": (5, [5, 9, 0]), "E7": (4, [4, 8, 11, 2])}
PROG = {
    "minor": ["Dm", "Gm", "A7", "Dm", "Bb", "Gm", "A7", "Dm"],
    "major": ["D", "Bm", "Em", "A7", "D", "G", "A7", "D"],
    "mystery": ["Dm", "Dm", "Bb", "A"],
    "tension": ["Dm", "Bb", "Dm", "A7"],
    "rise": ["Bb", "C", "F", "A7", "D", "G", "A7", "D"],
}
SCALE = {"minor": [2, 4, 5, 7, 9, 10, 1], "major": [2, 4, 6, 7, 9, 11, 1], "natural": [2, 4, 5, 7, 9, 10, 0]}
RHY = [[1, 1, 1], [2, 1], [1.5, 0.5, 1], [1, 0.5, 0.5, 1], [3], [0.5, 0.5, 1, 1]]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ---------------------------------------------------------------- çalgılar
_cache = {}


def reed(m, dur, bright=1.0, att=0.03, rel=0.10):
    """Akordeon: üç dil (0, +7, −7 sent) → musette titreşimi. Toplamsal; harmonikler 1/k^1.1."""
    key = ("reed", m, round(dur, 3), bright)
    if key in _cache:
        return _cache[key]
    n = int((dur + rel) * SR)
    t = np.arange(n) / SR
    f = hz(m)
    y = np.zeros(n)
    rng = np.random.default_rng(m)
    nh = max(1, min(12, int(7000 / f)))
    for cents in (0.0, 7.0, -7.0):
        ff = f * 2 ** (cents / 1200)
        for k in range(1, nh + 1):
            y += np.sin(2 * np.pi * ff * k * t + rng.uniform(0, 6.28)) * (bright / k ** 1.1 if k > 1 else 1.0)
    e = np.ones(n)
    a, r = int(att * SR), int(rel * SR)
    e[:a] = np.linspace(0, 1, a)
    e[-r:] = np.linspace(1, 0, r)
    e *= 1 - 0.12 * (t / max(dur, 0.1)).clip(0, 1)                # körük: hafif sönüm
    y = y * e / (3 * 2.2)
    _cache[key] = y
    return y


def pluck(m, dur=0.6, decay=3.0, harm=6):
    """Telli çekme (kontrbas / pizzicato): harmonikler üstel söner, tizler daha hızlı."""
    key = ("pluck", m, round(dur, 3), decay)
    if key in _cache:
        return _cache[key]
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    y = np.zeros(n)
    for k in range(1, harm + 1):
        if f * k > 9000:
            break
        y += np.sin(2 * np.pi * f * k * t) * np.exp(-t * decay * (1 + 0.7 * (k - 1))) / k
    a, r = int(0.004 * SR), int(0.03 * SR)
    y[:a] *= np.linspace(0, 1, a)
    y[-r:] *= np.linspace(1, 0, r)                                 # kesik bitiş tık yapıyordu (spektrogramda görüldü)
    _cache[key] = y
    return y


def noise_burst(dur, decay, seed, bright=0.5):
    n = int(dur * SR)
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n)
    x = x - bright * np.concatenate([[0], x[:-1]])                 # kaba renk
    y = x * np.exp(-np.arange(n) / SR / decay)
    r = min(n, int(0.01 * SR))
    y[-r:] *= np.linspace(1, 0, r)
    return y


def lowpass(x, fc, hp=40.0):
    """FFT ile yumuşak bant geçiren (scipy yok): fc üstü ve hp altı (alt bas uğultusu) kısılır."""
    size = 1 << int(np.ceil(np.log2(len(x) + 1)))
    X = np.fft.rfft(x, size, axis=0)
    fr = np.fft.rfftfreq(size, 1 / SR)
    g = 1 / np.sqrt(1 + (fr / fc) ** 4) / np.sqrt(1 + (hp / np.maximum(fr, 1e-3)) ** 4)
    return np.fft.irfft(X * (g[:, None] if x.ndim > 1 else g), size, axis=0)[:len(x)]


# ---------------------------------------------------------------- yardımcılar
def nearest(pc_list, ref, lo, hi):
    best = None
    for m in range(lo, hi + 1):
        if m % 12 in pc_list and (best is None or abs(m - ref) < abs(best - ref)):
            best = m
    return best


def scale_step(m, direction, scale):
    x = m + direction
    while x % 12 not in scale:
        x += direction
    return x


class Score:
    def __init__(self, total, bpm=150, seed=3):
        self.n = int((total + 3) * SR)
        self.mel = np.zeros((self.n, 2))
        self.acc = np.zeros((self.n, 2))
        self.beat = 60.0 / bpm
        self.bar = 3 * self.beat
        self.rng = random.Random(seed)

    def put(self, buf, y, t, gain=1.0, pan=0.0):
        p0 = int(t * SR)
        if p0 >= self.n or p0 < 0:
            return
        m = min(len(y), self.n - p0)
        lg, rg = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        buf[p0:p0 + m, 0] += y[:m] * gain * lg * 1.414
        buf[p0:p0 + m, 1] += y[:m] * gain * rg * 1.414

    # ---- eşlik
    def oompah(self, t, chord, bar_i, light=False):
        root, pcs = CH[chord]
        bass = nearest([root if bar_i % 2 == 0 else (root + 7) % 12], 43, 36, 50)
        self.put(self.acc, pluck(bass, 0.7, 3.5), t, 0.75, -0.1)
        voic = sorted(nearest([pc], 60, 55, 67) for pc in pcs[:3])
        for b in (1, 2):
            for m in voic:
                self.put(self.acc, reed(m, self.beat * 0.45, bright=0.6, att=0.01, rel=0.06),
                         t + b * self.beat, 0.16 if not light else 0.10, 0.25)
            self.put(self.acc, noise_burst(0.12, 0.035, int(t * 100) + b, 0.9) * 0.05, t + b * self.beat, 1.0, 0.4)

    def pad(self, t, chord, bars=1, gain=0.22):
        root, pcs = CH[chord]
        voic = sorted(nearest([pc], 57, 50, 64) for pc in pcs[:3])
        for m in voic:
            self.put(self.acc, reed(m, self.bar * bars, bright=0.45, att=0.5, rel=0.6), t, gain, -0.2)
        self.put(self.acc, pluck(nearest([root], 38, 33, 45), self.bar * bars, 1.2), t, 0.5)

    def musicbox(self, t, chord):
        root, pcs = CH[chord]
        notes = [nearest([pc], 84, 79, 91) for pc in pcs[:3]]
        for b in range(3):
            self.put(self.mel, audio.synth("bell", notes[(b + self.rng.randint(0, 2)) % 3]) * 0.5,
                     t + b * self.beat, 0.22, 0.3 * (1 if b % 2 else -1))

    def ticks(self, t):
        for b in range(3):
            self.put(self.acc, audio.synth("tick", 76 if b == 0 else 72), t + b * self.beat, 0.10, 0.5 * (-1) ** b)

    def drums(self, t, roll=0.0):
        self.put(self.acc, audio.synth("thud", 38), t, 0.9)          # 30 → 38: 40 Hz süzgecinin altında kalıyordu
        steps = 12
        for s in range(steps):
            v = 0.02 + roll * 0.06 * (s / steps)
            if s % 2 == 0 or roll > 0:
                self.put(self.acc, noise_burst(0.08, 0.02, int(t * 1000) + s, 0.95), t + s * self.bar / steps, v, 0.15)

    # ---- melodi
    def phrase(self, t0, prog, bars, scale, lo=64, hi=84, sparse=False, octave=0, glock=False, start=None):
        """bars ölçülük melodi: 2 ölçülük motif, 3-4'te akora taşınır, 5-6 yeni, 7-8 kadans."""
        prev = start or 69
        motif = [self.rng.choice(RHY[:4] if not sparse else [[2, 1], [3], [1.5, 0.5, 1]]) for _ in range(2)]
        for b in range(bars):
            chord = prog[b % len(prog)]
            root, pcs = CH[chord]
            rhy = motif[b % 2] if (b % 8) < 4 else self.rng.choice(RHY[:4] if not sparse else [[2, 1], [3]])
            if b % 8 == 7 or b == bars - 1:
                rhy = [3] if not sparse else [3]
            tb = t0 + b * self.bar
            pos = 0.0
            sc_b = scale if all(p in scale for p in pcs) else SCALE["natural"]   # ödünç akor (Bb, C, F): doğal minör
            minor = 5 in sc_b
            target = nearest(pcs, prev + self.rng.choice((-2, 0, 2, 3)), lo, hi)
            if b % 8 == 7 or b == bars - 1:
                target = nearest([root], prev, lo, hi)
            note = target
            for k, d in enumerate(rhy):
                if k > 0:
                    nxt = nearest(CH[prog[(b + 1) % len(prog)]][1], note + self.rng.choice((-3, 2, 4)), lo, hi)
                    note = scale_step(note, 1 if nxt > note else -1, sc_b)
                    if minor and self.rng.random() < 0.15 and d <= 0.5:   # musette süsü (yalnız minör): kromatik alt komşu
                        note = note - 1
                dur = d * self.beat
                y = reed(note + 12 * octave, dur * 0.92, bright=0.9, att=0.02, rel=0.08)
                self.put(self.mel, y, tb + pos * self.beat, 0.55, 0.05)
                if glock:
                    self.put(self.mel, audio.synth("bell", note + 24) * 0.4, tb + pos * self.beat, 0.10, 0.2)
                pos += d
            prev = note
        return prev


def compose(spans, total, theme="musette", bpm=150, seed=3):
    """spans: [(başlangıç sn, ruh hali)] sıralı. Döner: {"melody": (n,2), "acc": (n,2)}."""
    assert theme == "musette", f"tema yok: {theme}"
    sc = Score(total, bpm, seed)
    bar = sc.bar
    nbars = int(math.ceil(total / bar)) + 1
    snapped = [(math.ceil(max(0.0, s) / bar - 1e-6) if i else 0, mood) for i, (s, mood) in enumerate(spans)]
    runs = []
    for i, (b0, mood) in enumerate(snapped):
        b1 = snapped[i + 1][0] if i + 1 < len(snapped) else nbars
        if b1 > b0:
            if runs and runs[-1][2] == mood:
                runs[-1] = (runs[-1][0], b1, mood)
            else:
                runs.append((b0, b1, mood))
    prev = 69
    for b0, b1, mood in runs:
        t0, nb = b0 * bar, b1 - b0
        if mood == "mystery":
            prog = PROG["mystery"]
            for b in range(nb):
                tb = t0 + b * bar
                if b % 2 == 0:
                    sc.pad(tb, prog[(b // 2) % len(prog)], bars=2, gain=0.20)
                sc.musicbox(tb, prog[(b // 2) % len(prog)])
                sc.ticks(tb)
        elif mood in ("waltz", "waltz_dark", "pizz"):
            prog = PROG["minor"]
            for b in range(nb):
                tb = t0 + b * bar
                if mood == "pizz":
                    root, pcs = CH[prog[b % 8]]
                    sc.put(sc.acc, pluck(nearest([root], 43, 36, 50), 0.5, 5.0), tb, 0.7)
                    for k, pc in enumerate(pcs[:3]):
                        sc.put(sc.acc, pluck(nearest([pc], 67, 62, 74), 0.25, 9.0, harm=4), tb + (k + 1) * sc.beat * 0.66,
                               0.22, 0.3 * (-1) ** k)
                else:
                    sc.oompah(tb, prog[b % 8], b, light=(mood == "waltz_dark"))
            if mood != "pizz":
                prev = sc.phrase(t0, prog, nb, SCALE["minor"], sparse=(mood == "waltz_dark"),
                                 lo=60 if mood == "waltz_dark" else 64, hi=79 if mood == "waltz_dark" else 84,
                                 start=prev)
        elif mood == "tension":
            prog = PROG["tension"]
            for b in range(nb):
                tb = t0 + b * bar
                if b % 2 == 0:
                    sc.pad(tb, prog[(b // 2) % 4], bars=2, gain=0.18)
                sc.drums(tb, roll=min(1.0, b / max(1, nb - 1)))
        elif mood in ("rise", "finale"):
            prog = PROG["rise"] if mood == "rise" else PROG["major"]
            for b in range(nb):
                sc.oompah(t0 + b * bar, prog[b % 8], b)
            prev = sc.phrase(t0, prog, nb, SCALE["major"], glock=True, start=prev)
    end = (int(total / bar) - 1) * bar                              # bitiş: Re majör akor, uzun
    if end > 0:
        sc.pad(end, "D", bars=2, gain=0.28)
        sc.put(sc.mel, reed(74, bar * 1.8, bright=0.8, att=0.05, rel=0.8), end, 0.4)
    out = {}
    for name, buf in (("melody", sc.mel), ("acc", sc.acc)):
        y = lowpass(buf, 6500)
        y = y + 0.18 * audio._reverb(y, 1.6, 0.45)
        out[name] = y[:int(total * SR)]
    return out


MOODS = {"hook": "mystery", "place_card": "waltz", "permit": "waltz_dark", "newspaper": "waltz",
         "science": "pizz", "radio": "pizz", "military": "tension", "renewal": "rise", "war": "tension",
         "today": "finale"}
