"""Anlatım sesi: dil başına TTS arka ucu, cümle cümle sentez + kontrollü duraklama + kelime zamanları.

Neden cümle cümle: EMA Lightning tek parça metinde cümle aralarına ~0,3 sn koyuyor (ölçüldü); dramatik anlatım
için kısa. Cümleleri ayrı üretip aralara noktalamaya göre sessizlik koyuyoruz; "||" işareti uzun vurgu duraklaması.

TR: EMA Lightning (Apache-2.0, tek ses, kelime zamanlarını kendisi veriyor).
EN: Kokoro-82M (Apache-2.0; 4 vCPU'da RTF ~0,6; kelime zamanlarını kendisi veriyor). Python < 3.13 ister → venv312.

Telaffuz işaretlemesi: {gösterilen|okunan}. Altyazıda ilk kısım, seste ikinci kısım kullanılır; iki kısım aynı
sayıda kelime içermeli (ör. {Gustave Eiffel|Güstav Eyfel}). Kokoro için okunan kısım misaki sözdizimi olabilir:
{Panthéon|[Panthéon](/pˈænθiən/)}.
"""
import re

import numpy as np
import soundfile as sf

PAUSE = {".": 0.42, "?": 0.5, "!": 0.5, ":": 0.32, ";": 0.3, "…": 0.6}
BEAT = 0.55            # "||" işaretine eklenen ek duraklama
LEAD, TAIL = 0.15, 0.6


MARK = re.compile(r"\{([^|{}]*)\|([^{}]*)\}")


def show(s):
    return MARK.sub(r"\1", s)


def say(s):
    return MARK.sub(r"\2", s)


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


class KokoroEN:
    sr = 24000

    def __init__(self, voice="am_michael", speed=1.0):
        import torch
        from kokoro import KPipeline
        torch.set_num_threads(4)
        self.voice, self.speed = voice, speed
        self.pipe = KPipeline(lang_code=voice[0], repo_id="hexgrad/Kokoro-82M")   # 'a' ABD, 'b' İngiliz

    def synth(self, sentences):
        out = []
        for text in sentences:
            chunks, words, off = [], [], 0.0
            for r in self.pipe(text, voice=self.voice, speed=self.speed, split_pattern=r"\n+"):
                audio = r.audio.cpu().numpy().astype(np.float32)
                for t in r.tokens or []:
                    if t.start_ts is None or t.end_ts is None or not re.search(r"[A-Za-z0-9]", t.text):
                        continue
                    words.append((t.text, off + t.start_ts, off + t.end_ts))
                chunks.append(audio)
                off += len(audio) / self.sr
            out.append((np.concatenate(chunks), self.sr, words))
        return out


BACKENDS = {"tr": EmaTR, "en": KokoroEN}


def trim(audio, sr, floor_db=-42.0, margin=0.03):
    """Cümle sesinin baş/son sessizliğini kırpar (Kokoro her cümleye ~0,2–0,3 sn ekliyordu; duraklamayı biz koyuyoruz).
    Döner: (kırpılmış ses, baştan kırpılan saniye)."""
    n = int(sr * 0.01)
    k = len(audio) // n
    if k == 0:
        return audio, 0.0
    rms = np.sqrt(np.mean(audio[:k * n].reshape(k, n) ** 2, axis=1)) + 1e-9
    loud = np.where(20 * np.log10(rms / (np.max(np.abs(audio)) + 1e-9)) > floor_db)[0]
    if len(loud) == 0:
        return audio, 0.0
    a = max(0, loud[0] * n - int(margin * sr))
    b = min(len(audio), (loud[-1] + 1) * n + int(margin * sr))
    return audio[a:b], a / sr


def _norm(w):
    return re.sub(r"[^\wçğıöşüâîû]", "", w.lower().replace("’", "'").replace("'", ""))


def align(toks, wts):
    """Metin kelimelerini TTS kelimelerine eşler. TTS sayıları birden çok kelimeye açabiliyor (EMA: "1889" →
    "bin sekiz yüz seksen dokuz"); rakam içeren metin kelimesi, bir sonraki metin kelimesine kadar olan TTS
    kelimelerinin toplam süresini alır. Döner: [(metin kelimesi, başlangıç, bitiş)] ya da eşleşmezse None."""
    out, j = [], 0
    for i, tok in enumerate(toks):
        if j >= len(wts):
            return None
        if re.search(r"\d", tok):
            nxt = _norm(toks[i + 1]) if i + 1 < len(toks) else None
            k = j + 1
            while k < len(wts) and (nxt is None or _norm(wts[k][0]) != nxt):
                k += 1
            out.append((tok, wts[j][1], wts[k - 1][2]))
            j = k
        else:
            out.append((tok, wts[j][1], wts[j][2]))
            j += 1
    return out if j == len(wts) else None


def narrate(script, lang, out_wav, **kw):
    """Döner: {"wav", "duration", "words": [{w, s, e}], "sentences": [{text, s, e}]}.
    Kelimeler metindeki yazımla (büyük harf, noktalama) verilir; zamanlar TTS'ten."""
    beats = split_beats(script)
    eng = BACKENDS[lang](**kw)
    outs = eng.synth([say(s) for s, _ in beats])
    sr = outs[0][1]
    pieces = [np.zeros(int(LEAD * sr), np.float32)]
    t = LEAD
    words, sents = [], []
    for (raw, beat), (audio, _, wts) in zip(beats, outs):
        text = show(raw)
        toks = text.split()
        audio, cut = trim(audio, sr)
        dur_a = len(audio) / sr
        pairs = list(zip(toks, [w[1] for w in wts], [w[2] for w in wts])) if len(toks) == len(wts) else align(toks, wts)
        if pairs is None:                              # eşleşmedi: TTS'in kendi yazımı (uyarı ver)
            print(f"  uyarı: altyazı eşleşmedi, TTS yazımı kullanılıyor: {text!r}")
            pairs = wts
        for wt, s, e in pairs:
            s, e = min(max(0.0, s - cut), dur_a), min(max(0.0, e - cut), dur_a)
            words.append({"w": wt, "s": round(t + s, 3), "e": round(t + e, 3)})
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
