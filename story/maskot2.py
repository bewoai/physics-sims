"""Seri maskotu adayları, 2. tur (kullanıcı: "Duolingo baykuşu tarzı, insanın kendiyle eşleştirebileceği, biraz salak,
sevimli ama izleyici kendini görsün; akıcı animasyon").

Tasarım ilkeleri (Duo'dan alınan ilke, şekil değil): basit geometrik gövde, tek güçlü imza rengi + bir gölge tonu,
kocaman gözler, kaş ve göz kapağıyla ifade. Baykuş ve yeşil kullanılmadı.
Akıcılık: her şey sürekli parametrelerle (nefes, göz kırpma, bakış yumuşatma, hazırlık–esneme–ezilme–yaylanma,
takip eden hareket: kuyruk / filiz / kafa sallama). Kareler arası pozlar arasında geçiş yok, eğriler var.

  draw(name, c, x, y, s, t, st)  name: mango | gugu | patates ; st: durum sözlüğü (aşağıda)
st: mood (idle|confused|aha|shock|sleepy|happy|annoyed), look (dx,dy), squash (1=normal, <1 ezik, >1 uzun),
    tilt (derece), blink (0..1 kapalılık), walk (faz ya da None), wave (0..1), derp (0..1 gözler ayrı yöne)
"""
import math

import skia

from story.style import C, paint

PLUS = skia.BlendMode.kPlus


def _blur(sigma, col, a, plus=False):
    p = skia.Paint(AntiAlias=True, Color4f=C(col, a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma))
    if plus:
        p.setBlendMode(PLUS)
    return p


def spring(x, k=7.0, w=16.0):
    """0→1 yaylanarak oturma (x saniye): 1 − e^(−kx)·cos(wx)."""
    if x <= 0:
        return 0.0
    return 1 - math.exp(-k * x) * math.cos(w * x)


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _eyes(c, cx, cy, r, gap, st, sclera="#FFFFFF", pupil="#151826", lid="#000000", iris=None, ring=None):
    """İki büyük göz: kapak (blink/sleepy), kaş yerine kapak açısı, derp (gözler ayrı yöne), parlama noktası."""
    mood = st.get("mood", "idle")
    lx, ly = st.get("look", (0.0, 0.0))
    derp = st.get("derp", 0.0)
    blink = st.get("blink", 0.0)
    big = {"shock": 1.18, "aha": 1.1}.get(mood, 1.0)
    for side in (-1, 1):
        ex, ey, er = cx + side * gap, cy, r * big
        if ring:
            c.drawCircle(ex, ey, er * 1.12, paint(ring))
        c.drawOval(skia.Rect(ex - er, ey - er * 1.08, ex + er, ey + er * 1.08), paint(sclera))
        dx = lx + derp * side * 0.55                              # derp: gözler dışa kayar
        dy = ly - derp * side * 0.25
        pr = er * (0.42 if mood != "shock" else 0.28)
        px, py = ex + dx * (er - pr - 3), ey + dy * (er - pr - 3)
        if iris:
            c.drawCircle(px, py, pr * 1.45, paint(iris))
        c.drawCircle(px, py, pr, paint(pupil))
        c.drawCircle(px - pr * 0.38, py - pr * 0.42, pr * 0.34, paint("#FFFFFF"))
        # kapaklar: blink + ruh hali (sleepy yarı kapalı, annoyed düz, confused tek kaş kalkık)
        top = {"sleepy": 0.55, "annoyed": 0.38}.get(mood, 0.0)
        if mood == "confused":
            top = 0.28 if side > 0 else 0.0
        top = max(top, blink)
        if top > 0.01:
            y_lid = ey - er * 1.08 + 2 * er * 1.08 * top
            c.save()
            clip = skia.Path()
            clip.addOval(skia.Rect(ex - er - 1, ey - er * 1.08 - 1, ex + er + 1, ey + er * 1.08 + 1))
            c.clipPath(clip, doAntiAlias=True)
            ang = {"annoyed": -8 * side, "confused": 10 if side > 0 else 0}.get(mood, 0)
            c.translate(ex, y_lid)
            c.rotate(ang)
            c.drawRect(skia.Rect(-er * 1.6, -er * 3, er * 1.6, 0), paint(lid))
            c.restore()


def _mouth(c, x, y, w, mood, col="#3A1C1C", tongue="#FF7C8E", t=0.0):
    p = skia.Path()
    if mood in ("happy", "aha"):
        p.moveTo(x - w, y - w * 0.2)
        p.quadTo(x, y + w * 1.3, x + w, y - w * 0.2)
        p.close()
        c.drawPath(p, paint(col))
        c.save()
        c.clipPath(p, doAntiAlias=True)
        c.drawCircle(x, y + w * 1.0, w * 0.6, paint(tongue))
        c.restore()
    elif mood == "shock":
        c.drawOval(skia.Rect(x - w * 0.45, y - w * 0.3, x + w * 0.45, y + w * 0.9), paint(col))
    elif mood == "confused":                                       # yamuk ağız + dil ucu (blep)
        p.moveTo(x - w * 0.8, y + w * 0.1)
        p.quadTo(x, y - w * 0.15, x + w * 0.7, y + w * 0.25)
        c.drawPath(p, paint(col, stroke=w * 0.22))
        c.drawOval(skia.Rect(x + w * 0.05, y + w * 0.05, x + w * 0.45, y + w * 0.55), paint(tongue))
    elif mood == "annoyed":
        c.drawLine(x - w * 0.7, y + w * 0.15, x + w * 0.7, y + w * 0.05, paint(col, stroke=w * 0.22))
    elif mood == "sleepy":
        c.drawOval(skia.Rect(x - w * 0.25, y, x + w * 0.25, y + w * 0.35), paint(col))
    else:
        p.moveTo(x - w * 0.6, y)
        p.quadTo(x, y + w * 0.45, x + w * 0.6, y)
        c.drawPath(p, paint(col, stroke=w * 0.2))


# ---------------------------------------------------------------- 1) Mango: tek beyin hücreli kedi (kullanıcı seçti)
# Renk: tekir (kullanıcı: "tekir kedi renginde olsun"). Eski turuncu palet ORANGE olarak duruyor.
TEKIR = dict(base="#9B9187", shade="#7E756C", stripe="#3F3933", cream="#F3ECE2", ear="#F2A7B0", nose="#F07F95",
             iris="#A8C94A")
ORANGE = dict(base="#FF8A2A", shade="#E0661A", stripe="#C85410", cream="#FFE6C6", ear="#FF9AA8", nose="#FF6F86",
              iris="#9BD15A")
M_O, M_D, M_C, M_P = TEKIR["base"], TEKIR["shade"], TEKIR["cream"], TEKIR["ear"]


def _dash(col, w, on, off, phase=0.0):
    p = paint(col, stroke=w, cap=skia.Paint.kButt_Cap)
    p.setPathEffect(skia.DashPathEffect.Make([on, off], phase))
    return p


def mango(c, x, y, s, t, st, pal=None):
    P = pal or TEKIR
    O, Dk, S, Cr = P["base"], P["shade"], P["stripe"], P["cream"]
    mood = st.get("mood", "idle")
    sq = st.get("squash", 1.0) * (1 + 0.018 * math.sin(t * 2.4))
    c.save()
    c.translate(x, y)
    c.rotate(st.get("tilt", 0.0))
    c.scale(1 / math.sqrt(sq), sq)
    sway = math.sin(t * 2.0) * 12 + st.get("tail_kick", 0.0)        # kuyruk: gecikmeli salınım
    tail = skia.Path()
    tail.moveTo(70 * s, -40 * s)
    tail.cubicTo(170 * s, -30 * s, 150 * s + sway * s, -170 * s, 120 * s + sway * 1.6 * s, -210 * s)
    c.drawPath(tail, paint(O, stroke=30 * s))
    c.drawPath(tail, _dash(S, 30 * s, 13 * s, 17 * s, 6 * s))       # kuyruk halkaları
    walk = st.get("walk")
    for side in (-1, 1):                                            # ayaklar
        lift = max(0.0, math.sin(walk + (0 if side > 0 else math.pi))) * 14 * s if walk is not None else 0
        c.drawOval(skia.Rect(side * 52 * s - 30 * s, -24 * s - lift, side * 52 * s + 30 * s, 6 * s - lift), paint(O))
    body = skia.Path()                                              # gövde: armut, baş-gövde birleşik
    body.addOval(skia.Rect(-110 * s, -200 * s, 110 * s, 0))
    c.drawPath(body, paint(O))
    c.save()                                                        # gövde yan çizgileri (tekir)
    c.clipPath(body, doAntiAlias=True)
    for side in (-1, 1):
        for k in range(3):
            p = skia.Path()
            yy = -160 * s + k * 42 * s
            p.moveTo(side * 115 * s, yy)
            p.quadTo(side * 80 * s, yy + 10 * s, side * 70 * s, yy + 30 * s)
            c.drawPath(p, paint(S, stroke=11 * s))
    c.restore()
    c.drawOval(skia.Rect(-62 * s, -140 * s, 62 * s, -8 * s), paint(Cr))  # göbek
    hy = -270 * s                                                   # baş
    for side in (-1, 1):                                            # kulaklar
        ear = skia.Path()
        ex = side * 92 * s
        ear.moveTo(ex - side * 50 * s, hy - 92 * s)
        ear.lineTo(ex + side * 18 * s, hy - 175 * s + (8 * s if mood == "sleepy" else 0))
        ear.lineTo(ex + side * 34 * s, hy - 60 * s)
        ear.close()
        c.drawPath(ear, paint(O))
        inner = skia.Path()
        inner.moveTo(ex - side * 28 * s, hy - 95 * s)
        inner.lineTo(ex + side * 12 * s, hy - 150 * s)
        inner.lineTo(ex + side * 20 * s, hy - 80 * s)
        inner.close()
        c.drawPath(inner, paint(P["ear"]))
    head = skia.Path()
    head.addOval(skia.Rect(-150 * s, hy - 130 * s, 150 * s, hy + 120 * s))
    c.drawPath(head, paint(O))
    c.save()
    c.clipPath(head, doAntiAlias=True)
    m = skia.Path()                                                 # alında tekir "M" deseni
    m.moveTo(-58 * s, hy - 62 * s)
    m.lineTo(-34 * s, hy - 104 * s)
    m.lineTo(0, hy - 74 * s)
    m.lineTo(34 * s, hy - 104 * s)
    m.lineTo(58 * s, hy - 62 * s)
    c.drawPath(m, paint(S, stroke=11 * s))
    for dx in (-30, 0, 30):                                         # tepe çizgileri
        c.drawLine(dx * s, hy - 135 * s, dx * 0.8 * s, hy - (112 if dx else 96) * s, paint(S, stroke=12 * s))
    for side in (-1, 1):                                            # yanak çizgileri + göz kenarı çizgisi
        for k in range(2):
            p = skia.Path()
            p.moveTo(side * 152 * s, hy + (4 + 30 * k) * s)
            p.quadTo(side * 128 * s, hy + (2 + 30 * k) * s, side * 112 * s, hy + (14 + 30 * k) * s)
            c.drawPath(p, paint(S, stroke=10 * s))
        c.drawLine(side * 108 * s, hy - 26 * s, side * 150 * s, hy - 40 * s, paint(S, stroke=7 * s))
    c.restore()
    c.drawOval(skia.Rect(-70 * s, hy + 18 * s, 70 * s, hy + 112 * s), paint(Cr))  # ağız çevresi
    _eyes(c, 0, hy - 20 * s, 44 * s, 62 * s, st, lid=O, iris=P["iris"])
    c.drawPath(_tri(0, hy + 30 * s, 13 * s), paint(P["nose"]))      # burun
    _mouth(c, 0, hy + 58 * s, 26 * s, mood, t=t)
    for side in (-1, 1):                                            # bıyıklar
        for k in (-1, 0, 1):
            c.drawLine(side * 64 * s, hy + (44 + k * 12) * s, side * 150 * s, hy + (30 + k * 26) * s,
                       paint("#FFFFFF", stroke=3 * s, alpha=0.85))
    _arms(c, s, st, O, sh_y=-150 * s, sh_x=100 * s, stripe=S)
    if st.get("extra"):
        st["extra"](c, s, hy)                                       # sahneye özel ek (çan, şapka…)
    c.restore()


def _tri(x, y, r):
    p = skia.Path()
    p.moveTo(x - r, y - r * 0.6)
    p.lineTo(x + r, y - r * 0.6)
    p.lineTo(x, y + r * 0.6)
    p.close()
    return p


def _arms(c, s, st, col, sh_y, sh_x, w=26, stripe=None):
    """Kollar. arm_l / arm_r: aşağıdan dışa açı (0 sarkık, 90 yatay, 180 yukarı) verilirse o; yoksa ruh hali
    (aha/happy: yukarı) ve wave (sağ el sallama)."""
    wave = st.get("wave", 0.0)
    mood = st.get("mood", "idle")
    for side, key in ((-1, "arm_l"), (1, "arm_r")):
        if key in st:
            deg = st[key]
        else:
            deg = 25 + (135 if mood in ("aha", "happy") else 0)
            if side > 0 and wave > 0:
                deg = 25 + 135 * (0.85 + 0.25 * math.sin(wave * 14))
        a = math.radians(deg)
        ex, ey = side * (sh_x + math.sin(a) * 70 * s), sh_y + math.cos(a) * 70 * s
        c.drawLine(side * sh_x * 0.85, sh_y, ex, ey, paint(col, stroke=w * s))
        if stripe:
            arm = skia.Path()
            arm.moveTo(side * sh_x * 0.85, sh_y)
            arm.lineTo(ex, ey)
            c.drawPath(arm, _dash(stripe, w * s, 7 * s, 15 * s, 4 * s))
        c.drawCircle(ex, ey, w * 0.7 * s, paint(col))


# ---------------------------------------------------------------- 2) Gugu: kafa sallayan güvercin
G_B, G_D, G_L, G_N1, G_N2, G_F = "#A5ADD3", "#7F88B4", "#D6DAF0", "#3FC6B0", "#9B6BD8", "#FF7A6B"


def gugu(c, x, y, s, t, st):
    mood = st.get("mood", "idle")
    walk = st.get("walk")
    bob = 0.0
    if walk is not None:                                            # güvercin imzası: kafa ileri–geri
        bob = math.sin(walk * 2) * 22 * s
    sq = st.get("squash", 1.0) * (1 + 0.02 * math.sin(t * 2.6))
    c.save()
    c.translate(x, y)
    c.rotate(st.get("tilt", 0.0))
    c.scale(1 / math.sqrt(sq), sq)
    for side in (-1, 1):                                            # ayaklar
        lift = max(0.0, math.sin(walk + (0 if side > 0 else math.pi))) * 16 * s if walk is not None else 0
        fx = side * 34 * s
        c.drawLine(fx, -40 * s, fx, -6 * s - lift, paint(G_F, stroke=12 * s))
        for d in (-1, 0, 1):
            c.drawLine(fx, -6 * s - lift, fx + d * 22 * s + 10 * s, 2 * s - lift, paint(G_F, stroke=9 * s))
    tail = skia.Path()
    tail.moveTo(-90 * s, -90 * s)
    tail.lineTo(-190 * s, -40 * s + 6 * s * math.sin(t * 3))
    tail.lineTo(-170 * s, -10 * s)
    tail.lineTo(-80 * s, -50 * s)
    tail.close()
    c.drawPath(tail, paint(G_D))
    c.drawOval(skia.Rect(-130 * s, -230 * s, 120 * s, -30 * s), paint(G_B))   # gövde (tombul)
    c.drawOval(skia.Rect(-60 * s, -170 * s, 100 * s, -40 * s), paint(G_L))    # göğüs
    wing = skia.Path()
    wing.moveTo(-110 * s, -170 * s)
    wing.cubicTo(-40 * s, -200 * s, 40 * s, -150 * s, 30 * s, -90 * s)
    wing.cubicTo(-20 * s, -70 * s, -100 * s, -80 * s, -110 * s, -170 * s)
    c.drawPath(wing, paint(G_D))
    for k in range(2):                                              # kanat çizgileri
        c.drawLine(-60 * s + k * 30 * s, -120 * s, -10 * s + k * 30 * s, -105 * s, paint(G_B, stroke=6 * s))
    hx, hy = 20 * s + bob, -300 * s
    neck = skia.Path()
    neck.addOval(skia.Rect(hx - 95 * s, hy + 20 * s, hx + 95 * s, hy + 130 * s))
    sh = skia.GradientShader.MakeLinear([(hx - 90 * s, 0), (hx + 90 * s, 0)], [C(G_N1).toColor(), C(G_N2).toColor()])
    c.drawPath(neck, skia.Paint(AntiAlias=True, Shader=sh))         # yanardöner boyun
    c.drawCircle(hx, hy - 10 * s, 110 * s, paint(G_B))              # baş
    _eyes(c, hx + 6 * s, hy - 20 * s, 40 * s, 52 * s, st, lid=G_B, ring="#FF9F43")
    beak = skia.Path()                                              # gaga
    bx, by = hx + 8 * s, hy + 40 * s
    beak.moveTo(bx - 26 * s, by - 6 * s)
    beak.quadTo(bx, by - 18 * s, bx + 26 * s, by - 6 * s)
    beak.lineTo(bx, by + 34 * s)
    beak.close()
    c.drawPath(beak, paint("#F2B35A"))
    c.drawOval(skia.Rect(bx - 16 * s, by - 18 * s, bx + 16 * s, by - 4 * s), paint("#FFFFFF", alpha=0.85))
    if mood in ("shock", "aha", "happy", "confused"):
        _mouth(c, bx, by + 30 * s, 16 * s, mood, t=t)
    _arms(c, s, st, G_D, sh_y=-150 * s, sh_x=110 * s, w=24)
    c.restore()


# ---------------------------------------------------------------- 3) Patates: tembel, uykulu
P_B, P_D, P_S, P_L = "#E0AE63", "#C08A41", "#A06E2E", "#6CCB5F"


def patates(c, x, y, s, t, st):
    mood = st.get("mood", "idle")
    sq = st.get("squash", 1.0) * (1 + 0.025 * math.sin(t * 1.8))
    c.save()
    c.translate(x, y)
    c.rotate(st.get("tilt", 0.0))
    c.scale(1 / math.sqrt(sq), sq)
    walk = st.get("walk")
    for side in (-1, 1):
        lift = max(0.0, math.sin(walk + (0 if side > 0 else math.pi))) * 12 * s if walk is not None else 0
        c.drawLine(side * 46 * s, -60 * s, side * 50 * s, -12 * s - lift, paint(P_D, stroke=20 * s))
        c.drawOval(skia.Rect(side * 50 * s - 26 * s, -22 * s - lift, side * 50 * s + 26 * s, 2 * s - lift), paint(P_D))
    body = skia.Path()                                              # yumrulu gövde
    pts = []
    for i in range(24):
        a = i / 24 * 2 * math.pi
        r = 1 + 0.06 * math.sin(a * 3 + 1) + 0.04 * math.sin(a * 5)
        pts.append((math.cos(a) * 150 * s * r, -230 * s + math.sin(a) * 200 * s * r))
    body.moveTo(*pts[0])
    for i in range(len(pts)):
        p1, p2 = pts[i], pts[(i + 1) % len(pts)]
        body.quadTo(p1[0], p1[1], (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
    body.close()
    c.drawPath(body, paint(P_B))
    c.save()
    c.clipPath(body, doAntiAlias=True)
    c.drawOval(skia.Rect(-40 * s, -160 * s, 240 * s, 60 * s), paint(P_D, alpha=0.35))  # gölge tarafı
    c.restore()
    for dx, dy, r in ((-80, -330, 9), (60, -120, 8), (-100, -150, 6), (90, -300, 7), (-30, -80, 6)):
        c.drawCircle(dx * s, dy * s, r * s, paint(P_S, alpha=0.6))  # benekler
    sway = math.sin(t * 2.4) * 14 + st.get("sprout_kick", 0.0)      # filiz: takip eden hareket
    st_path = skia.Path()
    st_path.moveTo(0, -425 * s)
    st_path.quadTo(sway * 0.4 * s, -470 * s, sway * s, -500 * s)
    c.drawPath(st_path, paint(P_L, stroke=8 * s))
    for side in (-1, 1):
        leaf = skia.Path()
        lx, ly = sway * s, -500 * s
        leaf.moveTo(lx, ly)
        leaf.quadTo(lx + side * 40 * s, ly - 34 * s, lx + side * 60 * s, ly + 4 * s)
        leaf.quadTo(lx + side * 30 * s, ly + 10 * s, lx, ly)
        c.drawPath(leaf, paint(P_L))
    _eyes(c, 0, -290 * s, 46 * s, 60 * s, st, lid=P_B)
    _mouth(c, 0, -205 * s, 30 * s, mood, t=t)
    for side in (-1, 1):
        c.drawCircle(side * 95 * s, -225 * s, 22 * s, paint("#FF8C7A", alpha=0.45))  # al yanak
    _arms(c, s, st, P_D, sh_y=-200 * s, sh_x=135 * s, w=22)
    c.restore()


CHARS = {"mango": mango, "gugu": gugu, "patates": patates}


def draw(name, c, x, y, s, t, st):
    CHARS[name](c, x, y, s, t, st)


# ---------------------------------------------------------------- akıcı animasyon denemesi (6 sn)
def demo_state(t):
    """0–1,5 bekleme (nefes, kırpma, bakış) · 1,5–3 kafası karışık (eğilme, derp, "?") · 3–4,4 hazırlık–zıplama–
    "!" · 4,4–6 mutlu el sallama. Her geçiş yumuşatma/yay ile."""
    st = {"mood": "idle", "look": (0.0, 0.0), "squash": 1.0, "tilt": 0.0, "blink": 0.0, "jump": 0.0}
    for b in (0.8, 2.6, 5.2):                                       # göz kırpma: 0,14 sn
        if b <= t < b + 0.14:
            st["blink"] = math.sin((t - b) / 0.14 * math.pi)
    if t < 1.5:
        st["look"] = (0.6 * math.sin(t * 2.2), 0.0)
    elif t < 3.0:
        k = ease((t - 1.5) / 0.35)
        st.update({"mood": "confused", "tilt": -12 * k, "derp": 0.9 * k, "look": (0.2, -0.4)})
        st["mark"] = ("?", spring(t - 1.6))
    elif t < 4.4:
        u = t - 3.0
        if u < 0.25:                                                # hazırlık: ezilme
            st.update({"mood": "aha", "squash": 1 - 0.18 * ease(u / 0.25)})
        elif u < 0.75:                                              # havada: uzama
            v = (u - 0.25) / 0.5
            st.update({"mood": "aha", "squash": 1.12 - 0.12 * v, "jump": 4 * v * (1 - v) * 160})
        else:                                                       # iniş: ezilme + yaylanma
            v = u - 0.75
            st.update({"mood": "aha", "squash": 1 - 0.16 * math.exp(-v * 7) * math.cos(v * 18)})
        st["mark"] = ("!", spring(t - 3.25))
        st["tail_kick"] = 30 * math.exp(-max(0.0, u - 0.75) * 4) * math.sin(u * 12)
        st["sprout_kick"] = st["tail_kick"]
    else:
        st.update({"mood": "happy", "wave": t - 4.4, "look": (0.0, -0.1)})
    return st


def render_demo(name, out, seconds=6.0, bg=("#3B2F4F", "#C98A7A"), floor="#1E1826"):
    """6 sn akıcılık denemesi: 1080×1920, 30 fps."""
    from lib import canvas
    from story.siluet import BLACK, blurp, font
    from story.style import linear
    rd = canvas.Renderer(out, glow=0.0, fps=30)
    head = {"mango": 450, "gugu": 420, "patates": 530}[name]       # kulak / tepe / filiz ucu (s = 1 iken)
    for fi in range(int(seconds * 30)):
        t = fi / 30

        def frame(c, t=t):
            c.drawRect(skia.Rect(0, 0, 1080, 1920), linear(0, 0, 0, 1350, list(bg)))
            c.drawCircle(540, 760, 700, _blur(120, "#FFE3B8", 0.25))
            c.drawRect(skia.Rect(0, 1350, 1080, 1920), paint(floor))
            st = demo_state(t)
            c.drawOval(skia.Rect(540 - 170 + st["jump"] * 0.3, 1330, 540 + 170 - st["jump"] * 0.3, 1370),
                       paint("#000000", alpha=0.35 - st["jump"] / 1200))
            draw(name, c, 540, 1350 - st["jump"], 1.6, t, st)
            if "mark" in st:
                ch, k = st["mark"]
                f = font(BLACK, 170 * max(0.0, k))
                w = f.measureText(ch)
                y = 1350 - head * 1.6 - 30 - st["jump"]
                c.drawString(ch, 760 - w / 2, y, f, blurp(16, "#FFC46B", 0.7, PLUS))
                c.drawString(ch, 760 - w / 2, y, f, paint("#FFFFFF"))
        rd.frame(frame)
    rd.close()
    return out


def demo_audio(out_wav, seconds=6.0, lead="vibes"):
    """Deneme sesi: seri teması (sinsi → jingle → zıplayan) + "?" baloncuk, iniş gümü."""
    import numpy as np
    import soundfile as sf
    from lib import audio
    from story import score
    st = score.compose([(0.0, "tiptoe"), (3.0, "sting"), (4.4, "bounce")], seconds, "quirky", 110, 5, lead=lead)
    y = st["melody"] + st["acc"]
    y = y / (np.sqrt(np.mean(y ** 2)) + 1e-9) * 0.08
    for t0, kind, midi, g in ((1.6, "pop", 76, 0.25), (3.75, "thud", 40, 0.35), (3.25, "whoosh", 64, 0.12)):
        fx = audio.synth(kind, midi)
        fx = fx / (np.max(np.abs(fx)) + 1e-9) * g
        p0 = int(t0 * 48000)
        m = min(len(fx), len(y) - p0)
        y[p0:p0 + m] += fx[:m, None]
    y = y / np.max(np.abs(y)) * 0.89
    sf.write(out_wav, y.astype(np.float32), 48000)
    return out_wav
