"""Format dosyalarının ortak son adımı: ses olayları → mix.wav → final.mp4 + sheet.jpg."""
import os
import time

from lib import audio, encode


def finish(out_dir, vid, events, seconds, cap=5, grow=False, reverb=0.18):
    mx = audio.Mix(seconds)
    for e in events:
        mx.add(*e)
    wav = mx.render(os.path.join(out_dir, "mix.wav"), cap=cap, grow=grow, reverb=reverb)
    final = encode.mux(vid, wav, os.path.join(out_dir, "final.mp4"))
    encode.contact_sheet(final, os.path.join(out_dir, "sheet.jpg"))
    print("çıktı", final, encode.loudness(final), flush=True)
    return final


class Clock:
    def __init__(self):
        self.t0 = time.time()

    def __str__(self):
        return f"{time.time() - self.t0:.0f} sn"
