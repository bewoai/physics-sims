"""Bölüm JSON'undan platform açıklamaları. Çıktı anahtarları auto/captions.py ile aynı (auto/publish.py doğrudan alır).

Kurallar (story/ARASTIRMA.md): ilk satır kanca, ikinci satır düğüm; yer · yıl satırı; kaynak; paylaşım çağrısı
("yorum yaz" dilenmesi yok, Meta düşürüyor); 5 hashtag = seri + yer + genel; YouTube başlığı soru, ≤ 100 karakter.

  python3 story/captions.py story/episodes/eiffel.json        # iki dilin metnini yazdırır
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from story.brand import BRAND, brand_for  # noqa: E402


def build(ep, lang):
    if ep.get("series") == "neden":
        return build_neden(ep, lang)
    b, d, pl = BRAND[lang], ep[lang], ep["place"]
    city = pl.get(f"city_{lang}", pl["city"]) if lang != "en" else pl["city"]
    country = pl.get(f"country_{lang}", pl["country"]) if lang != "en" else pl["country"]
    share = d.get("share") or (b["share"] or "").format(city=city)
    tags = list(dict.fromkeys([b["tag"]] + d["hashtags"]))[:5]
    where = f"📍 {city}, {country} · {pl['year']}"
    src = f"{b['sources'] if '·' in ep['source_short'] else b['source']}: {ep['source_short']}"
    caption = "\n".join([*d["lines"], "", where, src, "", share, "", " ".join(tags)])
    title = d["title"]
    assert len(title) <= 90, f"YouTube başlığı uzun: {len(title)}"
    desc = "\n".join([" ".join(d["lines"]), "", where, "", f"{b['sources']}:",
                      *[f"• {u}" for u in ep["sources"]], "", b["credits"], "", " ".join(tags) + " #shorts"])
    return {"caption": caption, "youtube_title": f"{title} #shorts", "youtube_description": desc,
            "tags": [t.lstrip("#") for t in tags]}


def build_neden(ep, lang):
    """"Neden hep böyle?" serisi: yer · yıl satırı yok; kanca + düğüm, kaynak, paylaşım, 5 etiket."""
    b, d = brand_for(ep)[lang], ep[lang]
    tags = list(dict.fromkeys([b["tag"]] + d["hashtags"]))[:5]
    src = f"{b['source']}: {ep['source_short']}"
    caption = "\n".join([*d["lines"], "", src, "", d["share"], "", " ".join(tags)])
    title = d["title"]
    assert len(title) <= 90, f"YouTube başlığı uzun: {len(title)}"
    desc = "\n".join([" ".join(d["lines"]), "", f"{b['sources']}:", *[f"• {u}" for u in ep["sources"]], "",
                      b["credits"], "", " ".join(tags) + " #shorts"])
    return {"caption": caption, "youtube_title": f"{title} #shorts", "youtube_description": desc,
            "tags": [t.lstrip("#") for t in tags]}


if __name__ == "__main__":
    ep = json.load(open(sys.argv[1]))
    for lang in ("en", "tr"):
        c = build(ep, lang)
        print(f"===== {lang.upper()} · {brand_for(ep)[lang]['name']} =====")
        print(f"--- Instagram + TikTok ({len(c['caption'])} karakter)\n{c['caption']}")
        print(f"--- YouTube başlık ({len(c['youtube_title'])} karakter)\n{c['youtube_title']}")
        print(f"--- YouTube açıklama\n{c['youtube_description']}\n")
