"""Prosedürel müzik yatağı + ses efektleri + miks. Telifsiz: hepsi kodla sentezlenir.

Yatak: Re minör, gizemli belgesel havası (Dm–Bb–Gm–A), toplamsal sentezli pad + bas + müzik kutusu arpeji.
Anlatım konuşurken müzik ~6 dB kısılır (ducking)."""
import numpy as np
import soundfile as sf

from lib import audio

SR = 48000
CHORDS = [(50, [62, 65, 69]), (46, [62, 65, 70]), (43, [62, 67, 70]), (45, [61, 64, 69])]   # Dm Bb Gm A


def _tone(f, n, harmonics=6, detune=0.0):
    t = np.arange(n) / SR
    y = np.zeros(n)
    for k in range(1, harmonics + 1):
        y += np.sin(2 * np.pi * f * k * (1 + detune) * t) / (k ** 1.6)
    return y


def _env(n, att, rel):
    e = np.ones(n)
    a, r = int(att * SR), int(rel * SR)
    e[:a] = np.linspace(0, 1, a)
    e[-r:] = np.linspace(1, 0, r)
    return e


def bed(seconds, bar=3.33):
    n = int(seconds * SR) + SR
    out = np.zeros((n, 2))
    seg = int(2 * bar * SR)
    i = 0
    pos = 0
    while pos < n:
        root, notes = CHORDS[i % len(CHORDS)]
        m = min(seg + SR, n - pos)
        env = _env(m, 1.2, 1.2)
        for ch, det in ((0, -0.003), (1, 0.003)):
            pad = sum(_tone(audio.hz(x), m, 6, det) for x in notes) * 0.08
            bass = np.sin(2 * np.pi * audio.hz(root - 12) * np.arange(m) / SR) * 0.10
            out[pos:pos + m, ch] += (pad + bass) * env
        # müzik kutusu arpeji (çeyrek notalar)
        step = int(bar / 4 * SR)
        arp = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[1] + 12]
        for j in range(8):
            p0 = pos + j * step
            if p0 >= n:
                break
            y = audio.synth("pluck", arp[j % 4]) * 0.05
            m2 = min(len(y), n - p0)
            out[p0:p0 + m2, 0] += y[:m2] * (0.8 if j % 2 else 1.0)
            out[p0:p0 + m2, 1] += y[:m2] * (1.0 if j % 2 else 0.8)
        pos += seg
        i += 1
    return out


def beep(dur, f=760.0, gain=0.25):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) * gain
    r = int(0.005 * SR)
    y[:r] *= np.linspace(0, 1, r)
    y[-r:] *= np.linspace(1, 0, r)
    return y


def morse_seq(code="·−· ·− −·· ·· −−−", unit=0.07):
    """Mors dizisi → (zaman, süre) listesi."""
    seq, t = [], 0.0
    for ch in code:
        if ch == "·":
            seq.append((t, unit)); t += 2 * unit
        elif ch == "−":
            seq.append((t, 3 * unit)); t += 4 * unit
        else:
            t += 3 * unit
    return seq, t


# Efekt seviyeleri: konuşmanın RMS'ine göre, efektin en yüksek 50 ms RMS'i (dB). Kullanıcı "sfx'ler yüksek" dedi;
# ölçüm: güm +10,6 dB, Mors −5,8, çan −6 dB'di (konuşmadan yüksek/yakın) → hepsi konuşmanın belirgin altına.
SFX_DB = {"thud": -8.0, "tick": -14.0, "bell": -14.0, "whoosh": -16.0, "beepseq": -16.0, "pluck": -14.0}


def _peak_rms(y, win=0.05):
    h = int(win * SR)
    k = max(1, len(y) // h)
    return float(np.sqrt(np.mean(y[:k * h].reshape(k, h) ** 2, axis=1)).max()) + 1e-9


def mix(narr_wav, total, sfx, out_wav, music_db=-21.0, duck_db=-6.0, stems=None, rel_db=-11.0,
        duck_acc_db=-8.0, duck_mel_db=-13.0):
    """sfx: [(t, kind, midi, gain)] ; kind 'beepseq' → Mors bip dizisi. Seviye SFX_DB'den (gain artık kullanılmıyor).
    stems verilirse (score.compose: "melody", "acc") eski yatak yerine o çalar: konuşma yokken müzik anlatımın
    rel_db altında; konuşurken eşlik duck_acc_db, melodi duck_mel_db daha kısılır (melodi sesle çakışmasın)."""
    x, sr = sf.read(narr_wav, dtype="float32")
    if x.ndim > 1:
        x = x.mean(1)
    if sr != SR:
        idx = np.arange(int(len(x) * SR / sr)) * (sr / SR)
        x = np.interp(idx, np.arange(len(x)), x).astype(np.float32)
    n = int(total * SR) + SR
    out = np.zeros((n, 2))
    m = min(len(x), n)
    out[:m, 0] += x[:m]
    out[:m, 1] += x[:m]
    # ducking zarfı: anlatımın 50 ms RMS'i, 300 ms yumuşatma
    hop = int(0.05 * SR)
    k = n // hop
    xx = np.zeros(n)
    xx[:m] = x[:m]
    rms = np.sqrt(np.mean(xx[:k * hop].reshape(k, hop) ** 2, axis=1))
    act = (rms > 0.02).astype(float)
    act = np.convolve(act, np.ones(6) / 6, mode="same")
    duck = 10 ** ((duck_db * act) / 20)
    duck = np.repeat(duck, hop)
    duck = np.pad(duck, (0, n - len(duck)), constant_values=1.0)[:n]
    if stems is None:
        b = bed(total)[:n]
        g = 10 ** (music_db / 20) / (np.sqrt(np.mean(b ** 2)) + 1e-9) * 0.1
        out += b * g * duck[:, None]
    else:
        speech = np.sqrt(np.mean(rms[rms > 0.02] ** 2)) if np.any(rms > 0.02) else 0.1
        both = sum(np.pad(v, ((0, max(0, n - len(v))), (0, 0)))[:n] for v in stems.values())
        g = speech * 10 ** (rel_db / 20) / (np.sqrt(np.mean(both ** 2)) + 1e-9)
        for name, ddb in (("acc", duck_acc_db), ("melody", duck_mel_db)):
            v = np.pad(stems[name], ((0, max(0, n - len(stems[name]))), (0, 0)))[:n]
            dk = np.repeat(10 ** ((ddb * act) / 20), hop)
            dk = np.pad(dk, (0, n - len(dk)), constant_values=1.0)[:n]
            out += v * g * dk[:, None]
    speech_rms = np.sqrt(np.mean(rms[rms > 0.02] ** 2)) if np.any(rms > 0.02) else 0.1
    for t, kind, midi, gain in sfx:
        tgt = speech_rms * 10 ** (SFX_DB.get(kind, -14.0) / 20)        # efekt seviyesi konuşmaya göre (dB)
        if kind == "beepseq":
            seq, _ = morse_seq()
            g = tgt / _peak_rms(beep(0.21, gain=1.0))
            for st, d in seq:
                y = beep(d, gain=1.0) * g
                p0 = int((t + st) * SR)
                if p0 + len(y) < n:
                    out[p0:p0 + len(y)] += y[:, None]
            continue
        y = audio.synth(kind, midi)
        y = y * tgt / _peak_rms(y)
        p0 = int(t * SR)
        m2 = min(len(y), n - p0)
        if m2 > 0:
            out[p0:p0 + m2] += y[:m2, None]
    out = out[:int(total * SR)]
    out = out / (np.max(np.abs(out)) + 1e-9) * 0.89
    sf.write(out_wav, out.astype(np.float32), SR, subtype="PCM_24")
    return out_wav
