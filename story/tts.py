"""Anlatım sesi: dil başına TTS arka ucu, cümle cümle sentez + kontrollü duraklama + kelime zamanları.

Neden cümle cümle: EMA Lightning tek parça metinde cümle aralarına ~0,3 sn koyuyor (ölçüldü); dramatik anlatım
için kısa. Cümleleri ayrı üretip aralara noktalamaya göre sessizlik koyuyoruz; "||" işareti uzun vurgu duraklaması.

TR: EMA Lightning (Apache-2.0, tek ses, kelime zamanlarını kendisi veriyor).
EN: araştırma sonucuna göre eklenecek (aynı arayüz: synth(sentences) -> [(audio, sr, [(word, s, e)])]).
"""
import re

import numpy as np
import soundfile as sf

PAUSE = {".": 0.42, "?": 0.5, "!": 0.5, ":": 0.32, ";": 0.3, "…": 0.6}
BEAT = 0.55            # "||" işaretine eklenen ek duraklama
LEAD, TAIL = 0.15, 0.6


def split_beats(script):
    """Metni cümlelere böler; '||' bir önceki cümleye ek duraklama verir."""
    parts = []
    for chunk in script.split("||"):
        sents = [s.strip() for s in re.split(r"(?<=[.!?…:])\s+", chunk.strip()) if s.strip()]
        if sents:
            parts.append(sents)
    out = []
    for i, sents in enumerate(parts):
        for j, s in enumerate(sents):
            beat = (j == len(sents) - 1) and i < len(parts) - 1
            out.append((s, beat))
    return out


class EmaTR:
    sr = 48000

    def __init__(self, seed=7, speed=1.0):
        from ema_lightning import EMA
        self.tts, self.seed, self.speed = EMA(), seed, speed

    def synth(self, sentences):
        res = self.tts.say(list(sentences), seed=self.seed, speed=self.speed, sample_rate=self.sr)
        return [(np.asarray(r.audio, np.float32), r.sample_rate, [(w.text, w.start, w.end) for w in r.words])
                for r in res]


BACKENDS = {"tr": EmaTR}


def narrate(script, lang, out_wav, **kw):
    """Döner: {"wav", "duration", "words": [{w, s, e}], "sentences": [{text, s, e}]}.
    Kelimeler metindeki yazımla (büyük harf, noktalama) verilir; zamanlar TTS'ten."""
    beats = split_beats(script)
    eng = BACKENDS[lang](**kw)
    outs = eng.synth([s for s, _ in beats])
    sr = outs[0][1]
    pieces = [np.zeros(int(LEAD * sr), np.float32)]
    t = LEAD
    words, sents = [], []
    for (text, beat), (audio, _, wts) in zip(beats, outs):
        toks = text.split()
        use_src = len(toks) == len(wts)            # sayı tutarsa metindeki yazımı kullan
        for k, (wt, s, e) in enumerate(wts):
            words.append({"w": toks[k] if use_src else wt, "s": round(t + s, 3), "e": round(t + e, 3)})
        dur = len(audio) / sr
        sents.append({"text": text, "s": round(t, 3), "e": round(t + dur, 3)})
        pieces.append(audio)
        t += dur
        gap = PAUSE.get(text[-1], 0.25) + (BEAT if beat else 0.0)
        pieces.append(np.zeros(int(gap * sr), np.float32))
        t += gap
    pieces.append(np.zeros(int(TAIL * sr), np.float32))
    y = np.concatenate(pieces)
    y = y / (np.max(np.abs(y)) + 1e-9) * 0.89
    sf.write(out_wav, y, sr, subtype="PCM_24")
    return {"wav": out_wav, "duration": round(len(y) / sr, 3), "words": words, "sentences": sents, "lang": lang}
