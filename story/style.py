"""Seri görsel kimliği: palet, yazı tipleri, gren, vinyet. 'Behind the Landmark' — sıcak, dokulu editoryal illüstrasyon."""
import os

import skia

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "assets", "fonts")


def C(hexs, a=1.0):
    h = hexs.lstrip("#")
    return skia.Color4f(int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


INK = "#23252B"
NIGHT, NIGHT2 = "#1B2640", "#2C3B5C"
CREAM, PAPER = "#F3E7CF", "#E7D6B4"
TERRA, RUST = "#C9673E", "#9E4A2E"
MUSTARD = "#E3AE45"
TEAL, TEAL_D = "#3F7F7B", "#2D5E5B"
SKY_DAY, SKY_DAY2 = "#9CC7C2", "#EAD9B5"
IRON, IRON_LIT = "#5A4434", "#E9B35A"
VELVET, VELVET_D = "#8E2B2B", "#5C1717"


def paint(color, stroke=None, alpha=None, cap=skia.Paint.kRound_Cap):
    c = C(color) if isinstance(color, str) else color
    if alpha is not None:
        c = skia.Color4f(c.fR, c.fG, c.fB, alpha)
    p = skia.Paint(AntiAlias=True, Color4f=c)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def linear(x0, y0, x1, y1, colors, pos=None):
    cols = [(C(c) if isinstance(c, str) else c).toColor() for c in colors]
    return skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(x0, y0), (x1, y1)], cols, pos))


def radial(cx, cy, r, colors, pos=None):
    cols = [(C(c) if isinstance(c, str) else c).toColor() for c in colors]
    return skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((cx, cy), r, cols, pos))


_tf = {}


def typeface(name):
    if name not in _tf:
        _tf[name] = skia.Typeface.MakeFromFile(os.path.join(FONTS, name))
    return _tf[name]


SANS_B, SANS_XB, SANS_K = "Montserrat-700.ttf", "Montserrat-800.ttf", "Montserrat-900.ttf"
SERIF, SERIF_B = "LiberationSerif-Regular.ttf", "LiberationSerif-Bold.ttf"


def text(c, s, x, y, size, color=CREAM, face=SANS_XB, align="center", alpha=1.0, spacing=0.0, max_w=None):
    f = skia.Font(typeface(face), size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    w = f.measureText(s) + spacing * max(0, len(s) - 1)
    if max_w and w > max_w:
        return text(c, s, x, y, size * max_w / w, color, face, align, alpha, spacing)
    x0 = x - w / 2 if align == "center" else (x - w if align == "right" else x)
    p = paint(color, alpha=alpha)
    if spacing:
        for ch in s:
            c.drawString(ch, x0, y, f, p)
            x0 += f.measureText(ch) + spacing
    else:
        c.drawString(s, x0, y, f, p)
    return w


def measure(s, size, face=SANS_XB):
    return skia.Font(typeface(face), size).measureText(s)


def grain(c, w, h, seed, alpha=0.07):
    """Kâğıt/film greni: fraktal gürültü, her karede tohum kayar."""
    sh = skia.PerlinNoiseShader.MakeFractalNoise(0.9, 0.9, 2, float(seed % 97))
    p = skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kOverlay, Alphaf=alpha)
    c.drawRect(skia.Rect(0, 0, w, h), p)


def vignette(c, w, h, strength=0.45):
    c.drawRect(skia.Rect(0, 0, w, h),
               radial(w / 2, h * 0.48, h * 0.75, [skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, 0),
                                                 skia.Color4f(0, 0, 0, strength)], [0.0, 0.55, 1.0]))
