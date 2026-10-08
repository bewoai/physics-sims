"""Ortak ekran yazısı: kanca cümlesi baştan sona sabit (kullanıcı isteği), altında büyük sayaç ve etiket."""
import skia

from lib.canvas import W, text

HOOK_Y, BIG_Y, LABEL_Y = 300, 470, 530


def hud(c, hook, big=None, label=None, pop=0.0, big_size=150, alpha=1.0):
    """pop: 0..1, sayaç değiştiği anda kısa büyüme."""
    if hook:
        text(c, hook, W / 2, HOOK_Y, size=60, weight=800, max_w=W - 140)
    if big is not None:
        text(c, str(big), W / 2, BIG_Y, size=int(big_size * (1 + 0.15 * pop)), weight=900,
             color=skia.Color4f(1, 1, 1, alpha))
    if label:
        text(c, label, W / 2, LABEL_Y, size=40, weight=700, color=skia.Color4f(1, 1, 1, 0.6 * alpha), shadow=False)


class Pop:
    """Sayaç değişince 0.15 sn'lik büyüme animasyonu."""

    def __init__(self, dur=0.15):
        self.last, self.t0, self.dur = None, -9.0, dur

    def __call__(self, value, t):
        if value != self.last:
            self.last, self.t0 = value, t
        return max(0.0, 1 - (t - self.t0) / self.dur)
