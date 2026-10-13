"""Güvenli alan (1080×1920). Yazı ve ana görsel bu dikdörtgenin içinde kalır.

Ölçüm (kullanıcının IG Reels ekran görüntüsü, 1220×2712; video y 102–2417 arası, ölçek 1,2057, yanlardan 34 px kırpık):
  sağ ikon sütunu  x 938–1004, y 869–1857  ·  alt kullanıcı adı + açıklama  x 76–581, y 1718–1863
Meta Reels yazı alanı 896×1264, üstten 260 px, yanlardan 48 px (reap.video / adaptlypost özetleri); TikTok ve Shorts
altta ~480 px'e kadar kaplıyor; IG akışı 9:16'yı 4:5'e kırpabiliyor (y 285–1635).
Birleşim: SAFE = x 92–920, y 285–1440. Yazı merkezi x = 506.
"""
import skia

SAFE = skia.Rect(92, 285, 920, 1440)
CX = (SAFE.left() + SAFE.right()) / 2

# platform arayüz alanları (QA katmanı için): (ad, x0, y0, x1, y1)
UI = [
    ("IG sağ ikonlar", 925, 860, 1080, 1860),
    ("IG alt yazı", 0, 1700, 1080, 1920),
    ("TikTok alt", 0, 1450, 940, 1920),
    ("TikTok sağ", 920, 700, 1080, 1500),
    ("Shorts alt", 0, 1540, 1080, 1920),
    ("Üst menü", 0, 0, 1080, 230),
    ("Kenar kırpma", 0, 0, 34, 1920),
    ("Kenar kırpma", 1046, 0, 1080, 1920),
]


def draw_qa(c):
    """Arayüzün kapladığı yerleri yarı saydam kırmızı, güvenli alanı yeşil çerçeve olarak çizer."""
    red = skia.Paint(Color4f=skia.Color4f(1, 0.15, 0.1, 0.22))
    for _, x0, y0, x1, y1 in UI:
        c.drawRect(skia.Rect(x0, y0, x1, y1), red)
    c.drawRect(SAFE, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.2, 1, 0.4, 0.9),
                                Style=skia.Paint.kStroke_Style, StrokeWidth=4))
