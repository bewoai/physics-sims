"""Tasarım dili denemeleri, 2. tur (kullanıcı ilk dördünü beğenmedi: "No. 1 gibi klasik süs ekleme, Instagram
güvenli alanına çok dikkat et"). Çerçeve, rozet, numara yok; tam ekran, sinematik ışık. Yazılar SAFE içinde.

  python3 story/looks2.py out/story/looks2
"""
import math
import os
import random
import sys

import numpy as np
import skia

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from story import draw as D  # noqa: E402
from story import style  # noqa: E402
from story.safezone import CX, SAFE, draw_qa  # noqa: E402
from story.style import C, paint, radial, linear, typeface  # noqa: E402

W, H = D.W, D.H
WORDS, CUR = ["Eyfel", "Kulesi'nin", "bir"], 1
PLUS = skia.BlendMode.kPlus


def font(face, size):
    f = skia.Font(typeface(face), size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def blurp(sigma, color, alpha=1.0, blend=None):
    p = skia.Paint(AntiAlias=True, Color4f=C(color, alpha),
                   MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma))
    if blend:
        p.setBlendMode(blend)
    return p


def cur_word(t):
    return CUR if not t else min(len(WORDS) - 1, int(t / 0.9) % (len(WORDS) + 1))


def caption(c, fill, hi, shadow=True, y=1390, size=68, face="Montserrat-900.ttf", glow=None, cur=CUR):
    """Kelime kelime altyazı, SAFE içinde ortalı (x = CX)."""
    f = font(face, size)
    sp = f.measureText(" ")
    ws = [f.measureText(w) for w in WORDS]
    tot = sum(ws) + sp * (len(ws) - 1)
    assert tot <= SAFE.width() - 20, "altyazı güvenli alana sığmıyor"
    x = CX - tot / 2
    for i, (w, wd) in enumerate(zip(WORDS, ws)):
        col = hi if i == cur else fill
        if shadow:
            c.drawString(w, x + 3, y + 6, f, blurp(8, "#000000", 0.75))
        if glow and i == cur:
            c.drawString(w, x, y, f, blurp(14, glow, 0.9, PLUS))
        c.drawString(w, x, y, f, paint(col))
        x += wd + sp


def spaced(c, s, x, y, size, color, face, spacing, alpha=1.0, p=None):
    f = font(face, size)
    for ch in s:
        c.drawString(ch, x, y, f, p or paint(color, alpha=alpha))
        x += f.measureText(ch) + spacing
    return x


# ---------------------------------------------------------------- A) Siluet Sinema
def sinema(c, t=0.0):
    """Arkadan ışıklı siluetler + hacimli ışık + sis katmanları + toz. Renk sahneye göre değişir (gece mavi,
    gün batımı turuncu, savaş kırmızı); burada gece."""
    c.drawRect(skia.Rect(0, 0, W, H), linear(0, 0, 0, 1550, ["#060B18", "#0E2240", "#24506E", "#4E8396"],
                                              [0.0, 0.42, 0.78, 1.0]))
    k = D.ease(t / 6.0)
    c.save()
    c.translate(W / 2, H / 2)
    c.scale(1 + 0.06 * k, 1 + 0.06 * k)                           # yavaş kamera itmesi
    c.translate(-W / 2, -H / 2)
    mx, my, mr = 660, 720, 215
    c.drawCircle(mx, my, 1150, radial(mx, my, 1150, [C("#CFEAF2", 0.42), C("#9CCBDA", 0.12), C("#9CCBDA", 0.0)],
                                       [0.0, 0.32, 1.0]))
    rng = random.Random(2)
    rays = blurp(16, "#DDF2F7", 0.07, PLUS)
    for _ in range(26):                                           # ışık huzmeleri
        a = rng.uniform(0, 2 * math.pi) + 0.03 * t
        da = math.radians(rng.uniform(0.8, 2.6)) * (0.85 + 0.15 * math.sin(t * 0.9 + a * 3))
        L = rng.uniform(800, 1500)
        p = skia.Path()
        p.moveTo(mx, my)
        p.lineTo(mx + L * math.cos(a - da), my + L * math.sin(a - da))
        p.lineTo(mx + L * math.cos(a + da), my + L * math.sin(a + da))
        p.close()
        c.drawPath(p, rays)
    for _ in range(70):                                           # yıldızlar (ay ışığından uzakta)
        x, y = rng.uniform(40, W - 40), rng.uniform(80, 700)
        if math.hypot(x - mx, y - my) < 520:
            continue
        r = rng.uniform(1.0, 2.6)
        tw = 0.55 + 0.45 * math.sin(t * rng.uniform(1.5, 4) + rng.uniform(0, 6))
        c.drawCircle(x, y, r * 3, blurp(4, "#BFE6F5", 0.35 * tw, PLUS))
        c.drawCircle(x, y, r, paint("#EAF6FB", alpha=0.9 * tw))
    c.drawCircle(mx, my, mr, radial(mx - 50, my - 60, mr * 1.3, ["#FBFCF6", "#E3EEEA", "#C9DCDA"], [0, 0.6, 1]))
    for dx, dy, r in ((-60, -40, 38), (50, 30, 26), (-10, 90, 30), (80, -80, 18), (-100, 60, 16)):
        c.drawCircle(mx + dx, my + dy, r, paint("#9FB8B8", alpha=0.18))
    fog = "#5C93A6"
    layers = [(1330, 21, 0.55, "#3D6C83", 0.55), (1420, 22, 0.72, "#25485F", 0.45), (1520, 23, 0.9, "#13293C", 0.35)]
    for li, (y, seed, sc, col, fa) in enumerate(layers):           # hava perspektifi: uzak katman sise karışır
        c.save()
        c.translate(-(li + 1) * 6 * t, 0)                         # paralaks: yakın katman daha hızlı
        for dx in (-8, 8, 0):                                     # binalar arası boşlukları kapat
            c.save(); c.translate(dx, 0); D.skyline(c, y, seed, col, col, None, scale=sc); c.restore()
        c.restore()
        c.drawRect(skia.Rect(0, y - 170, W, y + 90), linear(0, y - 170, 0, y + 90,
                                                             [C(fog, 0.0), C(fog, fa), C(fog, 0.0)], [0, 0.6, 1]))
    tx, ty, th = 640, 1600, 1180
    tp = D.tower_path(tx, ty, th)
    c.drawPath(tp, paint("#050912"))
    c.save()                                                      # kafesten sızan ay ışığı
    c.clipPath(tp, doAntiAlias=True)
    lp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3.2, BlendMode=PLUS,
                    Shader=skia.GradientShader.MakeRadial((mx, my), 420, [C("#E8F6FA", 0.95).toColor(),
                                                                         C("#9CCBDA", 0.35).toColor(),
                                                                         C("#9CCBDA", 0.0).toColor()], [0, 0.55, 1]))
    k, step = -th, 0.022 * th
    while k < th:
        c.drawLine(tx + k, ty, tx + k + th, ty - th, lp)
        c.drawLine(tx - k, ty, tx - k - th, ty - th, lp)
        k += step
    c.restore()
    for f, extra in ((0.176, 1.18), (0.356, 1.22), (0.85, 1.6)):
        w = float(np.interp(f, D._F, D._Wd)) * th * extra
        c.drawRect(skia.Rect(tx - w, ty - f * th - 16, tx + w, ty - f * th + 4), paint("#050912"))
    c.drawLine(tx, ty - th, tx, ty - th - 60, paint("#050912", stroke=7))
    c.save()
    c.translate(-30 * t, 0)
    for dx in (-8, 8, 0):                                         # ön plan çatıları
        c.save(); c.translate(dx, 0); D.skyline(c, 1700, 24, "#03060D", "#03060D", None, scale=1.35); c.restore()
    c.restore()
    c.drawRect(skia.Rect(0, 1700, W, H), paint("#03060D"))
    for x, y in ((180, 1530), (300, 1575), (820, 1560)):            # sıcak pencere ışıkları (soğuk/sıcak karşıtlığı)
        x -= 30 * t
        c.drawRect(skia.Rect(x, y, x + 18, y + 26), paint("#FFB65C"))
        c.drawCircle(x + 9, y + 13, 60, blurp(30, "#FF9A3C", 0.45, PLUS))
    for _ in range(90):                                           # toz zerreleri ışıkta
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0, 700) ** 1.0
        x = mx + d * math.cos(a) + 14 * t * rng.uniform(0.5, 1.5)
        y = my + d * math.sin(a) * 1.4 - 9 * t * rng.uniform(0.3, 1.2) + 6 * math.sin(t * 1.3 + d)
        r = rng.uniform(1.2, 3.2)
        c.drawCircle(x, y, r * 2.5, blurp(3, "#E9F7FB", 0.25, PLUS))
    c.drawRect(skia.Rect(0, 1380, W, 1760), linear(0, 1380, 0, 1760, [C(fog, 0.0), C(fog, 0.22), C(fog, 0.0)]))
    c.restore()
    ta = D.ease((t - 0.8) / 0.6) if t > 0 else 1.0                 # başlık: kamera dışı, sabit
    spaced(c, "SON TARİH", SAFE.left(), 380, 40, "#DDEFF5", "Montserrat-800.ttf", 12, alpha=0.9 * ta)
    f = font("Montserrat-900.ttf", 180)
    c.drawString("1909", SAFE.left() - 6, 560, f, blurp(26, "#BFE6F5", 0.55 * ta, PLUS))
    c.drawString("1909", SAFE.left() - 6, 560, f, paint("#F4FAFB", alpha=ta))
    style.grain(c, W, H, 1, alpha=0.06)
    style.vignette(c, W, H, 0.55)
    caption(c, "#FFFFFF", "#FFC46B", cur=cur_word(t))


# ---------------------------------------------------------------- B) Işık Çizgisi
def roofs(y_base, seed, scale):
    """Bina çizgileri (yol) + pencere konumları."""
    rng = random.Random(seed)
    p, wins = skia.Path(), []
    x = -60
    while x < W + 60:
        w = rng.uniform(80, 160) * scale
        h = rng.uniform(170, 360) * scale
        top, rh = y_base - h, 38 * scale
        p.moveTo(x, y_base)
        p.lineTo(x, top)
        p.lineTo(x + 10 * scale, top - rh)
        p.lineTo(x + w - 10 * scale, top - rh)
        p.lineTo(x + w, top)
        p.lineTo(x + w, y_base)
        for _ in range(rng.randint(1, 2)):
            cx = x + rng.uniform(0.2, 0.8) * w
            p.moveTo(cx - 7 * scale, top - rh)
            p.lineTo(cx - 7 * scale, top - rh - 26 * scale)
            p.lineTo(cx + 7 * scale, top - rh - 26 * scale)
            p.lineTo(cx + 7 * scale, top - rh)
        cols, floors = max(2, int(w / (34 * scale))), max(2, int(h / (52 * scale)))
        for i in range(cols):
            for j in range(floors):
                wy = top + 22 * scale + j * 50 * scale
                if wy < y_base - 30 * scale and rng.random() < 0.5:
                    wins.append((x + (i + 0.5) * w / cols - 7 * scale, wy, 14 * scale, 22 * scale, rng.random()))
        x += w + rng.uniform(4, 14) * scale
    return p, wins


def isik(c, t=None):
    """Karanlık zeminde kendini çizen ışık çizgileri (bloom). Çizim ucunda parlayan kalem kıvılcımı."""
    c.drawRect(skia.Rect(0, 0, W, H), paint("#04060C"))
    c.drawCircle(540, 900, 1100, radial(540, 900, 1100, [C("#0E1A33", 1.0), C("#04060C", 1.0)]))
    art = skia.Surface(W, H)
    a = art.getCanvas()
    a.clear(skia.Color4f(0, 0, 0, 0))
    rng = random.Random(5)
    for _ in range(80):
        a.drawCircle(rng.uniform(30, W - 30), rng.uniform(80, 1000), rng.uniform(1.0, 2.4), paint("#9FD8FF", alpha=0.8))
    a.drawCircle(830, 700, 80, paint("#BFE8FF", stroke=4))
    cr = skia.Path()
    cr.addArc(skia.Rect(795, 665, 885, 755), 110, 160)
    a.drawPath(cr, paint("#BFE8FF", stroke=3, alpha=0.7))
    for y, seed, sc, col, al in ((1470, 21, 0.6, "#2E7BD6", 0.55), (1600, 22, 0.85, "#38B6FF", 0.85)):
        p, wins = roofs(y, seed, sc)
        a.drawPath(p, paint(col, stroke=3.2, alpha=al))
        for wx, wy, ww, wh, r in wins:
            if r < 0.22:
                a.drawRect(skia.Rect(wx, wy, wx + ww, wy + wh), paint("#FFC46B", alpha=0.9))
    tx, ty, th = 600, 1560, 1050
    tp = D.tower_path(tx, ty, th)
    a.save()
    a.clipPath(tp, doAntiAlias=True)
    k, step = -th, 0.03 * th
    la = 0.55 if t is None else 0.55 * D.ease((t - 2.5) / 1.5)     # kafes sonra belirir
    while k < th:
        a.drawLine(tx + k, ty, tx + k + th, ty - th, paint("#FFB34D", stroke=2.0, alpha=la))
        a.drawLine(tx - k, ty, tx - k - th, ty - th, paint("#FFB34D", stroke=2.0, alpha=la))
        k += step
    a.restore()
    if t is None or t >= 3.5:
        a.drawPath(tp, paint("#FFC46B", stroke=5))
    else:                                                         # kule çizgisi kendini çiziyor
        pm2 = skia.PathMeasure(tp, False)
        part = skia.Path()
        pm2.getSegment(0, pm2.getLength() * max(0.0, t / 3.5), part, True)
        a.drawPath(part, paint("#FFC46B", stroke=5))
    for f, extra in ((0.176, 1.18), (0.356, 1.22), (0.85, 1.6)):
        w = float(np.interp(f, D._F, D._Wd)) * th * extra
        a.drawLine(tx - w, ty - f * th, tx + w, ty - f * th, paint("#FFD58A", stroke=6))
    a.drawLine(tx, ty - th, tx, ty - th - 60, paint("#FFD58A", stroke=4))
    p, _ = roofs(1700, 23, 1.2)                                   # ön plan: yarıya kadar çizilmiş (çizim sürüyor)
    pm = skia.PathMeasure(p, False)
    seg = skia.Path()
    total, done = 0.0, 0.0
    lens = []
    while True:
        lens.append(pm.getLength())
        if not pm.nextContour():
            break
    goal = sum(lens) * (0.55 if t is None else min(1.0, t / 5.0))
    pm = skia.PathMeasure(p, False)
    tip = None
    while True:
        L = pm.getLength()
        take = min(L, goal - done)
        if take > 0:
            pm.getSegment(0, take, seg, True)
            if take < L:
                tip = pm.getPosTan(take)[0]
        done += take
        if done >= goal or not pm.nextContour():
            break
    a.drawPath(seg, paint("#7FD3FF", stroke=4))
    img = art.makeImageSnapshot()
    for sigma, al in ((22, 0.9), (7, 0.9)):                       # parıltı (bloom)
        c.drawImage(img, 0, 0, skia.SamplingOptions(),
                    skia.Paint(ImageFilter=skia.ImageFilters.Blur(sigma, sigma), BlendMode=PLUS, Alphaf=al))
    c.drawImage(img, 0, 0)
    if tip is not None and (t is None or t < 5.0):
        tx2, ty2 = tip.x(), tip.y()
        c.drawCircle(tx2, ty2, 40, blurp(18, "#BFF0FF", 0.9, PLUS))
        c.drawCircle(tx2, ty2, 7, paint("#FFFFFF"))
    f = font("Montserrat-900.ttf", 170)
    na = 1.0
    if t is not None:                                             # neon yanışı: titreyerek açılır
        na = 0.0 if t < 1.0 else (1.0 if t > 1.6 else (1.0 if int(t * 20) % 3 else 0.2))
    st = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5, Color4f=C("#FF5A4E", na))
    c.drawString("1909", SAFE.left(), 540, f, blurp(18, "#FF5A4E", 0.8 * na, PLUS))
    c.drawString("1909", SAFE.left(), 540, f, st)
    spaced(c, "SON TARİH", SAFE.left() + 4, 365, 40, "#FF8A80", "Montserrat-800.ttf", 12, alpha=na)
    style.grain(c, W, H, 2, alpha=0.05)
    sr = skia.Rect(SAFE.left() + 20, 1310, SAFE.right() - 20, 1425)  # altyazı arkası karartma (parlak çizgiler üstünde okunsun)
    c.drawRoundRect(sr, 40, 40, blurp(24, "#02040A", 0.8))
    caption(c, "#EAF6FF", "#FFC46B", shadow=False, glow="#FFC46B", cur=cur_word(t or 0.0))


LOOKS = {"A_siluet_sinema": sinema, "B_isik_cizgisi": isik}


def render_all(d):
    os.makedirs(d, exist_ok=True)
    out = []
    for name, fn in LOOKS.items():
        for qa in (False, True):
            surf = skia.Surface(W, H)
            c = surf.getCanvas()
            fn(c)
            if qa:
                draw_qa(c)
            p = os.path.join(d, f"{name}{'_qa' if qa else ''}.png")
            surf.makeImageSnapshot().save(p, skia.kPNG)
            out.append(p)
    return out


def teaser(name, out, seconds=6.0, music_wav=None, music_from=3.6):
    """Hareketli örnek: tarzın hareket dili + konu müziği (müziğin music_from saniyesinden)."""
    from lib import canvas, encode
    fn = LOOKS[name]
    rd = canvas.Renderer(out.replace(".mp4", "_v.mp4"), glow=0.0, fps=30)
    for fi in range(int(seconds * 30)):
        rd.frame(lambda c, fi=fi: fn(c, fi / 30))
    rd.close()
    if music_wav:
        import subprocess
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out.replace(".mp4", "_v.mp4"), "-ss", str(music_from),
                        "-t", str(seconds), "-i", music_wav, "-af", f"afade=t=out:st={seconds - 0.8}:d=0.8",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    return out


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "out/story/looks2"
    for p in render_all(d):
        print(p)
