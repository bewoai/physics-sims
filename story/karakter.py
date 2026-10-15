"""Seri karakteri ("sen"): sevimli, büyük kafalı siluet; parlak gözler ve tepede kıvrık perçem (imza). Siluet Sinema
diliyle uyumlu: gövde karanlık, ışık tarafında kenar parıltısı (rim light), yüz ifadesi gözler + ağızla.

  char(c, x, y, s, t, pose)  — x, y: ayakların ortası (zemin); s: ölçek (1.0 ≈ 400 px boy)

pose alanları (hepsi isteğe bağlı):
  walk: adım fazı (radyan) ya da None · face: +1 sağa, −1 sola bakar · lean: gövde eğimi (derece)
  arm_l / arm_r: (omuz, dirsek) açıları, derece; 0 = aşağı sarkık, + = yüzün baktığı yöne doğru kalkar
  eyes: open | wide | sleepy | closed | happy | angry · look: (dx, dy) göz bebeği yönü −1..1
  mouth: None | smile | o | frown | flat | grin · squash: dikey ölçek · jump: yukarı kayma (px)
  rim: kenar ışığı rengi · rim_dir: (dx, dy) ışığın geldiği yön · col: gövde rengi · blink: True ise kırpar
"""
import math

import skia

from story.style import C, paint

EYE_W, EYE_H = "#FFFFFF", "#0B0E18"


def _limb(c, x0, y0, a1, l1, a2, l2, w, col, edge=None):
    """İki parçalı uzuv: a1 omuz/kalça açısı (aşağıdan, derece), a2 dirsek/diz göreli açısı. edge: gövdenin önünden
    geçerken seçilsin diye ince açık kontur (tek renk silüette kol gövdeye karışıyordu)."""
    r1 = math.radians(a1)
    x1, y1 = x0 + math.sin(r1) * l1, y0 + math.cos(r1) * l1
    r2 = math.radians(a1 + a2)
    x2, y2 = x1 + math.sin(r2) * l2, y1 + math.cos(r2) * l2
    p = skia.Path()
    p.moveTo(x0, y0)
    p.lineTo(x1, y1)
    p.lineTo(x2, y2)
    if edge:
        c.drawPath(p, paint(edge, stroke=w + 5))
        c.drawCircle(x2, y2, w * 0.75 + 2.5, paint(edge))
    c.drawPath(p, paint(col, stroke=w))
    return x2, y2


def _shape(c, x, y, s, t, P, col, edge_off=False):
    face = P.get("face", 1)
    walk = P.get("walk")
    # bacaklar
    hip_y = y - 92 * s
    for side in (-1, 1):
        hx = x + side * 20 * s
        if walk is not None:
            ph = walk + (0 if side * face > 0 else math.pi)
            a = 28 * math.sin(ph) * face
            lift = max(0.0, math.sin(ph + math.pi / 2)) * 16 * s
            fx, fy = hx + math.sin(math.radians(a)) * 80 * s, y - lift
        else:
            spread = P.get("stance", 0.0)
            fx, fy = hx + side * spread * s, y
        c.drawLine(hx, hip_y, fx, fy - 8 * s, paint(col, stroke=19 * s))
        c.drawOval(skia.Rect(fx - 16 * s + face * 6 * s, fy - 16 * s, fx + 16 * s + face * 6 * s, fy + 2 * s), paint(col))
    # gövde (armut)
    body = skia.RRect.MakeRectXY(skia.Rect(x - 50 * s, y - 205 * s, x + 50 * s, y - 80 * s), 44 * s, 44 * s)
    c.drawRRect(body, paint(col))
    # kafa + perçem
    hx, hy, hr = x + face * 4 * s, y - 280 * s, 80 * s
    c.drawCircle(hx, hy, hr, paint(col))
    curl = skia.Path()
    curl.moveTo(hx - face * 4 * s, hy - hr + 6 * s)
    curl.cubicTo(hx + face * 6 * s, hy - hr - 40 * s, hx + face * 46 * s, hy - hr - 30 * s,
                 hx + face * 34 * s, hy - hr - 8 * s)
    curl.cubicTo(hx + face * 26 * s, hy - hr + 6 * s, hx + face * 14 * s, hy - hr - 6 * s,
                 hx + face * 20 * s, hy - hr - 16 * s)
    c.drawPath(curl, paint(col, stroke=11 * s))
    # kollar
    hands = {}
    for side, key in ((-1, "arm_l"), (1, "arm_r")):
        sh_a, el_a = P.get(key, (0.0, 0.0))
        if walk is not None and key not in P:
            sh_a = -22 * math.sin(walk + (0 if side * face > 0 else math.pi))
        sx, sy = x + side * 44 * s, y - 182 * s
        hand = _limb(c, sx, sy, side * 10 + sh_a * face, 62 * s,
                     el_a * face, 56 * s, 16 * s, col, None if edge_off else P.get("edge", "#3A4060"))
        c.drawCircle(hand[0], hand[1], 12 * s, paint(col))
        hands[key] = hand
    return hands, (hx, hy, hr)


def _eye(c, ex, ey, s, kind, look, col, blink):
    w, h = 15 * s, 21 * s
    if kind == "wide":
        w, h = 19 * s, 26 * s
    if blink or kind == "closed":
        p = skia.Path()
        p.addArc(skia.Rect(ex - w, ey - h * 0.5, ex + w, ey + h * 0.7), 20, 140)
        c.drawPath(p, paint(EYE_W, stroke=4.5 * s))
        return
    if kind == "happy":
        p = skia.Path()
        p.addArc(skia.Rect(ex - w, ey - h * 0.2, ex + w, ey + h * 1.0), 200, 140)
        c.drawPath(p, paint(EYE_W, stroke=5 * s))
        return
    c.drawOval(skia.Rect(ex - w, ey - h, ex + w, ey + h), paint(EYE_W))
    lx, ly = look
    pr = 8.5 * s if kind != "wide" else 7 * s
    c.drawCircle(ex + lx * (w - pr - 2 * s), ey + ly * (h - pr - 2 * s) + 2 * s, pr, paint(EYE_H))
    c.drawCircle(ex + lx * (w - pr - 2 * s) - 3 * s, ey + ly * (h - pr - 2 * s) - 2 * s, 2.6 * s, paint(EYE_W))
    if kind == "sleepy":                                   # üst göz kapağı
        c.drawRect(skia.Rect(ex - w - 2, ey - h - 2, ex + w + 2, ey - h * 0.1), paint(col))
    if kind == "angry":                                    # çatık kaş
        p = skia.Path()
        p.moveTo(ex - w - 3 * s, ey - h - 4 * s)
        p.lineTo(ex + w + 3 * s, ey - h - 4 * s)
        p.lineTo(ex + w + 3 * s, ey - h * 0.15)
        p.close()
        c.drawPath(p, paint(col))


def char(c, x, y, s, t, pose=None):
    P = dict(pose or {})
    col = P.get("col", "#0A0D18")
    face = P.get("face", 1)
    c.save()
    jump = P.get("jump", 0.0)
    sq = P.get("squash", 1.0)
    c.translate(x, y - jump)
    c.rotate(P.get("lean", 0.0) * face)
    c.scale(1 / math.sqrt(sq), sq)
    c.translate(-x, -y)
    rim = P.get("rim")
    if rim:                                                # kenar ışığı: ışık yönüne kaymış parlak kopya
        dx, dy = P.get("rim_dir", (1, -1))
        c.save()
        c.translate(dx * 4 * s, dy * 4 * s)
        _shape(c, x, y, s, t, P, rim, edge_off=True)
        c.restore()
    hands, (hx, hy, hr) = _shape(c, x, y, s, t, P, col)
    blink = P.get("blink", True) and (t % 3.7) < 0.12
    kind = P.get("eyes", "open")
    look = P.get("look", (0.25 * face, 0.0))
    for side in (-1, 1):
        _eye(c, hx + side * 27 * s + face * 12 * s, hy - 4 * s, s, kind, look, col, blink and kind not in ("closed",))
    m = P.get("mouth")
    mx, my = hx + face * 14 * s, hy + 38 * s
    if m == "smile":
        p = skia.Path()
        p.addArc(skia.Rect(mx - 16 * s, my - 14 * s, mx + 16 * s, my + 8 * s), 20, 140)
        c.drawPath(p, paint(EYE_W, stroke=4.5 * s))
    elif m == "frown":
        p = skia.Path()
        p.addArc(skia.Rect(mx - 15 * s, my, mx + 15 * s, my + 20 * s), 200, 140)
        c.drawPath(p, paint(EYE_W, stroke=4.5 * s))
    elif m == "o":
        c.drawOval(skia.Rect(mx - 8 * s, my - 6 * s, mx + 8 * s, my + 12 * s), paint(EYE_W))
    elif m == "flat":
        c.drawLine(mx - 13 * s, my + 4 * s, mx + 13 * s, my + 4 * s, paint(EYE_W, stroke=4.5 * s))
    elif m == "grin":
        p = skia.Path()
        p.addArc(skia.Rect(mx - 20 * s, my - 14 * s, mx + 20 * s, my + 16 * s), 0, 180)
        p.close()
        c.drawPath(p, paint(EYE_W))
    c.restore()
    return {"head": (hx, hy - jump, hr), **hands}


def mark(c, x, y, s, ch, col="#FFFFFF", glow="#FFC46B", a=1.0, bob=0.0):
    """Kafa üstünde "?" / "!" / "Z": parlayan işaret."""
    from story.siluet import BLACK, PLUS, blurp, font
    f = font(BLACK, 90 * s)
    w = f.measureText(ch)
    c.drawString(ch, x - w / 2, y + bob, f, blurp(10 * s, glow, 0.7 * a, PLUS))
    c.drawString(ch, x - w / 2, y + bob, f, paint(col, alpha=a))


def bubble(c, x, y, s, a=1.0, col="#F4F1EA", tail_to=None):
    """Düşünce balonu (bulut) + kuyruk baloncukları; içerik ayrı çizilir. Döner: iç merkez."""
    p = paint(col, alpha=a)
    for dx, dy, r in ((-60, 0, 62), (0, -26, 72), (62, 0, 60), (30, 34, 52), (-34, 34, 52)):
        c.drawCircle(x + dx * s, y + dy * s, r * s, p)
    if tail_to:
        tx, ty = tail_to
        for k, r in ((0.55, 16), (0.78, 10), (0.93, 6)):
            c.drawCircle(x + (tx - x) * k, y + 60 * s + (ty - y - 60 * s) * k, r * s, p)
    return x, y + 4 * s
