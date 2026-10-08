"""Kare çizimi: skia ile 1080x1920 kare, parıltı (glow), yazı, ffmpeg'e ham kare borusu."""
import colorsys
import os
import subprocess

import numpy as np
import skia

W, H, FPS = 1080, 1920, 60
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "assets", "fonts")

# Platform arayüzlerinin kapattığı bölgeler (IG/TikTok/Shorts ortak, yaklaşık):
# üst ~220 px sekmeler, alt ~420 px açıklama/ses satırı, sağ ~150 px butonlar.
SAFE_TOP, SAFE_BOTTOM, SAFE_RIGHT = 220, 420, 150

_fonts = {}


def font(weight=800, size=96):
    key = (weight, size)
    if key not in _fonts:
        tf = skia.Typeface.MakeFromFile(os.path.join(FONTS, f"Montserrat-{weight}.ttf"))
        f = skia.Font(tf, size)
        f.setEdging(skia.Font.Edging.kSubpixelAntiAlias)
        _fonts[key] = f
    return _fonts[key]


def hsv(h, s=0.85, v=1.0, a=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return skia.Color4f(r, g, b, a)


def paint(color, stroke=None, blend=None):
    p = skia.Paint(AntiAlias=True, Color4f=color)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
    if blend:
        p.setBlendMode(blend)
    return p


_text_cache = {}


def _text_image(s, size, weight, shadow, max_w):
    """Yazıyı (gölgesiyle) bir kez görüntüye çizer; her karede bulanıklık hesaplamamak için önbellek."""
    key = (s, size, weight, shadow, max_w)
    if key not in _text_cache:
        f = font(weight, size)
        w = f.measureText(s)
        if w > max_w:
            f = font(weight, max(20, int(size * max_w / w)))
            w = f.measureText(s)
        pad = 40
        hgt = int(f.getSize() * 1.5) + 2 * pad
        surf = skia.Surface(int(w) + 2 * pad, hgt)
        c = surf.getCanvas()
        c.clear(skia.Color4f(0, 0, 0, 0))
        blob = skia.TextBlob.MakeFromString(s, f)
        base = pad + f.getSize() * 1.1
        if shadow:
            sp = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0, 0, 0, 0.55),
                            ImageFilter=skia.ImageFilters.Blur(10, 10))
            c.drawTextBlob(blob, pad, base + 6, sp)
        c.drawTextBlob(blob, pad, base, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, 1)))
        _text_cache[key] = (surf.makeImageSnapshot(), w, pad, base)
    return _text_cache[key]


def text(canvas, s, cx, y, size=96, weight=800, color=skia.Color4f(1, 1, 1, 1), max_w=W - 160, shadow=True):
    """Ortalanmış beyaz yazı (renk alfası saydamlık olarak uygulanır); sığmazsa küçülür. y = taban çizgisi."""
    img, w, pad, base = _text_image(s, size, weight, shadow, max_w)
    p = skia.Paint(AntiAlias=True, Alphaf=color.fA)
    canvas.drawImage(img, cx - w / 2 - pad, y - base, skia.SamplingOptions(skia.FilterMode.kLinear), p)


class Renderer:
    """Sahne `draw(canvas)` ile çizilir; parıltı katmanı çeyrek çözünürlükte bulanıklaştırılıp toplanır
    (yarım çözünürlükte 68 ms/kare, çeyrekte 17 ms; yumuşak parıltıda fark görünmüyor)."""

    def __init__(self, out_path, bg=(0.035, 0.035, 0.05), glow=0.9, glow_sigma=12, crf=16):
        self.bg = skia.Color4f(*bg, 1)
        self.glow, self.glow_sigma = glow, glow_sigma
        self.scene = skia.Surface(W, H)
        self.final = skia.Surface(W, H)
        self.small = skia.Surface(W // 4, H // 4)
        self.buf = np.empty((H, W, 4), np.uint8)
        self.n = 0
        self.proc = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
             "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p",
             "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", out_path],
            stdin=subprocess.PIPE)

    def frame(self, draw, overlay=None):
        """draw: parlayan sahne. overlay: parıltısız üst katman (yazılar)."""
        c = self.scene.getCanvas()
        c.clear(skia.Color4f(0, 0, 0, 0))
        draw(c)
        img = self.scene.makeImageSnapshot()
        out = self.final.getCanvas()
        out.clear(self.bg)
        if self.glow > 0:
            hc = self.small.getCanvas()
            hc.clear(skia.Color4f(0, 0, 0, 0))
            sg = self.glow_sigma / 2
            hc.drawImageRect(img, skia.Rect(0, 0, W // 4, H // 4),
                             skia.SamplingOptions(skia.FilterMode.kLinear),
                             skia.Paint(ImageFilter=skia.ImageFilters.Blur(sg, sg)))
            gp = skia.Paint(BlendMode=skia.BlendMode.kPlus, Alphaf=self.glow)
            out.drawImageRect(self.small.makeImageSnapshot(), skia.Rect(0, 0, W, H),
                              skia.SamplingOptions(skia.FilterMode.kLinear), gp)
        out.drawImage(img, 0, 0)
        if overlay:
            overlay(out)
        self.final.readPixels(skia.ImageInfo.Make(W, H, skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType),
                              self.buf, W * 4, 0, 0)
        self.proc.stdin.write(self.buf.tobytes())
        self.n += 1

    def close(self):
        self.proc.stdin.close()
        self.proc.wait()
        return self.n
