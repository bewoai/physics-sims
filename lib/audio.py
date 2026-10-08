"""Olaydan ses: simülasyondaki her çarpışma bir ses olayı olur, burada sentezlenip miksajlanır.

Telifli müzik yok; tüm sesler kodla üretilir. Yoğun anlarda (yüzlerce çarpışma/sn) ses duvarına
dönmemesi için 10 ms'lik kutularda olay sayısı sınırlanır ve kazanç ölçeklenir.
"""
import numpy as np
import soundfile as sf

SR = 48000
PENTA = [0, 2, 4, 7, 9]          # majör pentatonik: hangi sırayla çalınırsa çalınsın kulağa hoş gelir
MINOR_PENTA = [0, 3, 5, 7, 10]


def scale_note(i, base=60, scale=PENTA):
    return base + 12 * (i // len(scale)) + scale[i % len(scale)]


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def _env(n, tau, attack=0.002):
    t = np.arange(n) / SR
    e = np.exp(-t / tau)
    a = int(attack * SR)
    if a > 0:
        e[:a] *= np.linspace(0, 1, a)
    return e


def _noise(n, seed):
    return np.random.default_rng(seed).standard_normal(n)


def _hp(x):            # kaba yüksek geçiren: ilk fark
    return np.diff(x, prepend=0.0)


def _lp(x, k):         # kaba alçak geçiren: hareketli ortalama
    return np.convolve(x, np.ones(k) / k, mode="same")


def synth(kind, midi=60, seed=0):
    f = hz(midi)
    if kind == "pluck":                      # marimba benzeri
        tau = float(np.clip(0.55 * (60 / midi) ** 1.5, 0.12, 0.8))
        n = int(SR * tau * 5)
        t = np.arange(n) / SR
        y = (np.sin(2 * np.pi * f * t) * _env(n, tau)
             + 0.22 * np.sin(2 * np.pi * 3.93 * f * t) * _env(n, tau * 0.18)
             + 0.05 * np.sin(2 * np.pi * 9.8 * f * t) * _env(n, tau * 0.05))
        return y * 0.8
    if kind == "bell":                       # cam/çan: inharmonik kısmiler, uzun kuyruk
        tau = 0.9
        n = int(SR * tau * 4)
        t = np.arange(n) / SR
        y = sum(a * np.sin(2 * np.pi * f * r * t) * _env(n, tau * d)
                for r, a, d in [(1, 1, 1), (2.76, 0.45, 0.6), (5.4, 0.25, 0.35), (8.93, 0.12, 0.2)])
        return y * 0.6
    if kind == "tick":                       # kısa tık; üst tizler kırpılır (ilk sürüm 20 kHz'e kadar sertti)
        n = int(SR * 0.02)
        return _lp(_hp(_noise(n, seed)), 4) * _env(n, 0.003, 0.0005) * 0.9
    if kind == "pop":                        # baloncuk: perdesi düşen kısa sinüs
        n = int(SR * 0.09)
        t = np.arange(n) / SR
        fr = f * (1 + 0.9 * np.exp(-t / 0.012))
        return np.sin(2 * np.pi * np.cumsum(fr) / SR) * _env(n, 0.025, 0.001)
    if kind == "thud":                       # yumuşak düşme; perde midi ile ölçeklenir (40 = varsayılan)
        n = int(SR * 0.25)
        t = np.arange(n) / SR
        fr = (55 + 140 * np.exp(-t / 0.03)) * hz(midi) / hz(40)
        return (np.sin(2 * np.pi * np.cumsum(fr) / SR) * _env(n, 0.07, 0.001)
                + 0.15 * _lp(_noise(n, seed), 6) * _env(n, 0.01, 0.0005))
    if kind == "shatter":                    # kırılma: gürültü patlaması + yüksek cam pingleri
        n = int(SR * 1.2)
        rng = np.random.default_rng(seed)
        y = _hp(_hp(_noise(n, seed))) * _env(n, 0.06, 0.0008) * 0.35
        t = np.arange(n) / SR
        for _ in range(9):
            d = int(rng.uniform(0, 0.12) * SR)
            fr = rng.uniform(2500, 7000)
            m = n - d
            y[d:] += 0.08 * np.sin(2 * np.pi * fr * t[:m]) * _env(m, rng.uniform(0.05, 0.25))
        return y
    if kind == "whoosh":
        n = int(SR * 0.6)
        x = _lp(_noise(n, seed), 12)
        w = np.sin(np.linspace(0, np.pi, n)) ** 2
        return x * w * 0.5
    raise ValueError(kind)


class Mix:
    def __init__(self, seconds):
        self.n = int(seconds * SR) + SR * 3
        self.events = []          # (t, kind, midi, gain, pan, seed)
        self._cache = {}

    def add(self, t, kind, midi=60, gain=1.0, pan=0.0, seed=0):
        self.events.append((t, kind, midi, gain, float(np.clip(pan, -1, 1)), seed))

    def _get(self, kind, midi, seed):
        k = (kind, round(midi, 2), seed % 8)
        if k not in self._cache:
            self._cache[k] = synth(kind, midi, seed % 8)
        return self._cache[k]

    def render(self, path, bin_ms=10, cap=5, reverb=0.18, grow=False):
        """grow=False: yoğunluk arttıkça kazanç düşer (sabit doku). grow=True: kalabalık kısımlar
        yavaşça yükselir (n/cap)^0.25 → kademeli formatlarda tırmanışı ses de taşır."""
        out = np.zeros((self.n, 2))
        bins = {}
        for e in self.events:
            bins.setdefault(int(e[0] * 1000 / bin_ms), []).append(e)
        for evs in bins.values():
            evs.sort(key=lambda e: -e[3])
            n = len(evs)
            scale = (max(1.0, n / cap) ** 0.25) if grow else 1 / np.sqrt(max(1.0, n / 2))
            for t, kind, midi, gain, pan, seed in evs[:cap]:
                y = self._get(kind, midi, seed) * gain * scale
                i = int(t * SR)
                m = min(len(y), self.n - i)
                if m <= 0:
                    continue
                out[i:i + m, 0] += y[:m] * np.sqrt((1 - pan) / 2)
                out[i:i + m, 1] += y[:m] * np.sqrt((1 + pan) / 2)
        if reverb > 0:
            out = out * (1 - reverb) + reverb * _reverb(out)
        peak = np.max(np.abs(out)) + 1e-9
        out = np.tanh(out / peak * 1.4) / np.tanh(1.4) * 0.89   # yumuşak tavan, ~-1 dBFS
        sf.write(path, out.astype(np.float32), SR, subtype="PCM_24")
        return path


def _reverb(x, seconds=1.4, tau=0.4):
    n = int(seconds * SR)
    out = np.empty_like(x)
    size = 1 << int(np.ceil(np.log2(len(x) + n)))
    for ch in range(2):
        ir = _lp(_noise(n, 100 + ch), 4) * np.exp(-np.arange(n) / SR / tau)
        ir[: int(0.012 * SR)] = 0          # erken yansıma boşluğu
        ir /= np.sqrt(np.sum(ir ** 2))
        y = np.fft.irfft(np.fft.rfft(x[:, ch], size) * np.fft.rfft(ir, size), size)
        out[:, ch] = y[: len(x)]
    return out
