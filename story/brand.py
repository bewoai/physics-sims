"""Hesap kimliği (dil başına): kanal adı, video rozeti, kullanıcı adı, seri etiketi, açıklama kalıpları.

Adlar (2026-10-13, gerekçe story/HESAPLAR.md): EN "Behind the Landmark", TR "Kartpostalın Arkası".
TR'de "Mekânın Hikâyesi" elendi: sosyal medyada "mekân" kafe/bar önerisi çağrıştırıyor.
"""

BRAND = {
    "en": {
        "name": "Behind the Landmark",
        "badge": "BEHIND THE LANDMARK",
        "handle": "behindthelandmark",
        "tag": "#behindthelandmark",
        "source": "Source", "sources": "Sources",
        "share": "Send this to someone who's been to {city}.",
        "credits": "Narration: AI voice (text-to-speech). Illustrations and animation made in code.",
    },
    "tr": {
        "name": "Kartpostalın Arkası",
        "badge": "KARTPOSTALIN ARKASI",
        "handle": "kartpostalinarkasi",
        "tag": "#kartpostalinarkasi",
        "source": "Kaynak", "sources": "Kaynaklar",
        "share": None,          # Türkçe ek uyumu (Paris'e, Roma'ya) kalıpla güvenilmez → bölüm JSON'unda "share"
        "credits": "Seslendirme: yapay zekâ (metinden sese). Çizim ve animasyon kodla üretildi.",
    },
}


# "Neden hep böyle?" serisi (2026-10-15): maskot Mango (tekir kedi). Ad önerisi seri imza cümlesinden:
# TR "Suç Sende Değil", EN "It's Not You". Kullanıcı onayı bekleniyor; değişirse yalnız burası değişir.
NEDEN = {
    "en": {
        "name": "It's Not You · Mango",
        "handle": "itsnotyou.mango",
        "tag": "#itsnotyou",
        "source": "Source", "sources": "Sources",
        "share": None,
        "credits": "Narration: AI voice (text-to-speech). Animation made in code. Mascot: Mango the tabby.",
    },
    "tr": {
        "name": "Suç Sende Değil · Mango",
        "handle": "sucsendedegil",
        "tag": "#sucsendedegil",
        "source": "Kaynak", "sources": "Kaynaklar",
        "share": None,
        "credits": "Seslendirme: yapay zekâ (metinden sese). Animasyon kodla üretildi. Maskot: tekir kedi Mango.",
    },
}
SERIES = {"landmark": BRAND, "neden": NEDEN}


def brand_for(ep):
    return SERIES.get(ep.get("series", "landmark"), BRAND)
