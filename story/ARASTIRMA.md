# Anlatımlı tarih kısa videoları — araştırma sentezi (2026-10-13)

Dört Opus alt ajanının raporlarından özet. Sayılar ajanların ölçtüğü/kaynakladığı değerlerdir; doğrulanamayanlar
belirtilmiştir. Çıkış noktası: kullanıcının gösterdiği Türk hesabı **Perde Tarih** (@perde.tarih).

## Karar
- **Konsept: "Behind the Landmark"** — bilinen bir yerin bilinmeyen hikâyesi. İngilizce kanalda dünya simgeleri +
  İstanbul/Osmanlı/Bizans bölümleri (boş niş), Türkçe kanal aynı hattan.
- **Ana platform YouTube Shorts**; TikTok ve Reels ikincil. TikTok sürümü > 60 sn (Creator Rewards şartı).
- **Ses:** EN Kokoro-82M `bm_george` (kullanıcı seçti), TR EMA Lightning. İkisi de Apache-2.0, CPU'da çalışıyor,
  kelime zamanlarını kendileri veriyor.
- **Görsel:** pilotta iki yol — (1) Google Gemini görsel + kod animasyon (kullanıcı `GEMINI_API_KEY` ekleyecek),
  (2) tamamen kodla çizim (skia).

## Perde Tarih verisi (TikTok, 13.10.2026)
1.022 takipçi, 5 video (8–12 Ekim 2026), toplam ~191,7K izlenme, süreler 59–71 sn. Yerebatan Medusa 87,8K,
Beyoğlu gemileri 78,6K, Kız Kulesi 19,7K, Truva atı 3,2K / 2,4K. Instagram'daki 9.131 takipçi doğrulanamadı (429).
→ Somut mekân tuhaflığı, mit düzeltmesinden ~25–37 kat iyi gitti (n=5, tahmin).

## Rakipler ve örüntüler
- "Bu neden böyle görünüyor?" en tutarlı kazanan: Zack D. Films (YT 29,1M; son 30 short medyanı 8,65M; TikTok
  medyanı 408K) — 3D. Simple History 5,12M abone ama short medyanı 31,5K (2D).
- **Düz 2D illüstrasyon Shorts'ta tek başına zayıf**: kamera hareketi, 2,5D derinlik, sabit seri kimliği şart.
- AI-gerçekçi hesaplar hızlı patlayıp sönüyor (POV Lab 7 haftada 434,7K sonra durdu); tarihçi eleştirisi ve
  YouTube'un "AI slop" önlemleri.
- Boşluk: İngilizce, illüstrasyonlu İstanbul/Osmanlı/Bizans short'u yok; uzun videolarda talep milyonlarca
  (Knowledgia Osmanlı 10,1M; "İstanbul'un 60 m altındaki kayıp liman" 1,5M). Mekânlar için "Why is it like this?".

## Konsept karşılaştırması (2025 Vikipedi görüntülenmesi vekil talep)
- A Landmark: yapı başına 0,4–2,2M/yıl; resmi kaynak bol (NPS, toureiffel.paris…); illüstrasyona en uygun.
- B Everyday things: talep yüksek ama Zack D. Films 3D ile baskın; köken hikâyeleri çoğunlukla folklor (risk).
- C Strangest days: abartıya açık. D Ottoman: İngilizcede ayrı seri değil, A içinde İstanbul bölümleri.
- 30 hikâyelik kaynaklı liste: alt ajan raporunda (Eiffel, Özgürlük Anıtı feneri, Mount Rushmore gizli oda,
  Hollywoodland, Big Ben çatlağı, Sagrada Família 137 yıl ruhsatsız, Empire State zeplin iskelesi, Ayasofya Viking
  runları, Kızıl Meydan "güzel" …). Mit içerenler işaretli; kullanmadan önce kaynak sayfası açılıp doğrulanacak.

## Kanca ve yapı
- İlk cümle formülleri: "[X] had an expiration date." · "[X] isn't [what you call it]." · "[X] wasn't …" (mit
  çürütme) · "For 137 years…" · "There's a secret room inside [X]." · "Why is [tuhaflık] like this?"
- İddia ilk 3 sn'de, siluet ilk karede (TikTok resmi rehberi). YouTube'da "Viewed vs swiped away" ile ölç.
- İskelet: 0–3 kanca → 3–10 bağlam + yer kartı → 10–30 hikâye → 30–45 twist (kanıt detayı ekranda) →
  45–55 bugüne bağla → son cümle ilk cümleye döngü.
- Seri kimliği: ≤1 sn perde açılış jeneriği, kartpostal yer kartı, kaynak rozeti, bitiş cümlesi;
  IG için "Send this to someone who's been there" (gönderme sinyali).

## Platform kuralları ve para kazanma
- YouTube 15.07.2025: "inauthentic content" — şablonlu hikâye, birbirinin yerine geçen videolar para kazanamaz.
  Aynı giriş/kapanış serbest; her bölüm ayrı araştırılmış hikâye olmalı, sahne/kamera/kanca türü değişmeli.
- YouTube 1 Şubat 2027'den: Shorts gelir payı için 90 günde 10M görüntüleme; YPP başvurusu 8.000 saat ya da
  90 günde 20M Shorts.
- AI etiketi: illüstrasyon tarzı (gerçekçi olmayan) görsel için YouTube beyan istemiyor; gerçekçi AI ses için
  TikTok/Meta'da etiket aç. EMA Lightning model kartı da "AI ses" beyanı istiyor.
- TikTok Creator Rewards: > 1 dk video, 10K takipçi, 30 günde 100K görüntüleme.

## Teknik
- TTS adayları ve lisans tuzakları: XTTS-v2, F5-TTS, OuteTTS ticari değil; Pocket TTS'in `cosette`/`jean` sesleri
  CC-BY-NC; Kokoro Python < 3.13 ister (venv312); misaki ile telaffuz: `[Mehmed](/mˈɛmɛd/)`.
- Kelime zamanı: Kokoro `tokens[i].start_ts`, EMA `Speech.words`; faster-whisper small yalnız QA (PyAV sürüm
  uyumsuzluğu: sesi numpy dizisi olarak ver).
- Görsel API fiyatları (13.10.2026): Gemini Nano Banana 2.1 1K $0.0336 (batch $0.0168), GPT Image 2 medium
  1024×1536 $0.041, Recraft V4 vektör $0.05 (`style_id`; şartlarda 30 gün önbellek maddesi), FLUX.2 pro $0.03.
- Katman: ayrı üret (arka/orta/ön plan); Depth Anything V2 Small (Apache) CPU'da 9:16 1,5 sn; BiRefNet-lite 16 sn;
  rembg'nin varsayılan modeli ticari lisans ister → `birefnet-*` seç.
- Kodla çizim: LLM ham SVG değil sahne JSON'u yazsın; CC0 setler: Open Peeps, Humaaans, Kenney; Tabler (MIT).
