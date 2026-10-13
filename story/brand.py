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
