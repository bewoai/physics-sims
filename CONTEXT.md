# CONTEXT — physics-sims

Yeni oturumda **ilk okunacak dosya**. Ne yaptığımızı, nedenlerini, ölçtüklerimizi ve açık işleri anlatır.
Sayılar ölçümdür; tahminler "tahmin" diye işaretli.

- Başlangıç: 2026-10-08. Kullanıcı: studio@rastcreative.com (Türkçe, kısa ve net yazar)
- Hedef platformlar: Instagram Reels, TikTok, YouTube Shorts (üçü de 1080×1920)
- Durum: 3 pilot format üretildi (`teslim/`), kullanıcı geri bildirimi bekleniyor

---

## 1. İş ve kararlar

Kullanıcı, izleyicinin "oturup takıldığı", izlenme süresi yüksek kısa videolar üreterek bir niş "farmlamak" istiyor.
Çıkış noktası @velvetphysicsji tarzı 3D fizik simülasyonları. Kullanıcı **birebir kopya istemiyor**, aynı izletme
mekaniğiyle özgün içerik istiyor.

| Karar | Neden |
|---|---|
| **Yapay zeka video modeli değil, kod** | "Tam 40 kesik" gibi parametre kontrolü, tutarlı fizik, aynı sahnenin seri varyasyonu ve deterministik tekrar sadece kodla mümkün. Yapay zeka en fazla fikir ve ses efekti için |
| **Önce 2D** (pymunk + skia), bulutta | Video başına ~4–6 dk render, tamamen bu konteynerde. Kullanıcı "2D fizik, 2–3 format" pilotunu seçti |
| **3D sonra, Blender (bpy, arayüzsüz), kullanıcının RTX makinesinde** | Bu konteynerde GPU yok (§5). Kullanıcı RTX'i olduğunu söyledi |
| Remotion / HyperFrames / three.js **gerekmiyor** | Yazı/kurgu katmanını skia zaten çiziyor. three.js stilize 3D için ileride opsiyonel |
| Ayrı repo | Dr. Erdem Çalışkan reels hattından (`bewoai/videolar`) bağımsız |
| Ekran yazıları **İngilizce** | Dil gerektirmeyen niş, global kitle. Değiştirmek tek satır (`hook=`) |
| Telifli müzik yok | Tüm ses çarpışma olaylarından sentezlenir (`lib/audio.py`) |

## 2. Referans analizi ve izletme mekaniği

Referans: kullanıcının yüklediği tweet videosu (918×720, 26,5 sn). Sol yarı @velvetphysicsji "1 Cut VS 40 Cuts" karpuz,
sağ yarı viewtrack.app reklamı (hesap: 20 gönderi / 181 gün, toplam 16,1M izlenme, haftada 1 paylaşım).

Ölçülenler:
- 6 kademe: 1 → 3 → 7 → 13 → 25 → 40 kesik. **Kademeler uzuyor**: ~2 sn → ~7 sn.
- Ses: müzik ve konuşma yok; sadece bıçak/parçalanma transientleri, kademe aralarında kısa sessizlik (spektrogram).
- Hesabın en çok izlenenleri foto-gerçekçi meyve değil **pastel, basit sahneler**: "Soft 0%" 8,5M, "Hole: 0.1cm" 4,6M;
  karpuz 1,7M, elma 162K.

Bundan çıkan mekanikler (her yeni formatta kontrol listesi):
1. **Başta vaat, sonda ödül** ("1 vs 40", "Can it escape?") → sonu görmeden çıkılmıyor.
2. **Ekranda sayaç** = ilerleme çubuğu.
3. **Tırmanış**: her kademe/an öncekinden büyük; en kaotik an sonda.
4. **Belirsizlik**: fizik sonucu tahmin edilemez.
5. **Dil yok** → global.
6. **Ses** tatmin edici ve olaya bağlı (her çarpışma bir nota/tık).
7. **Döngü**: son → baş geçişi yumuşak, tekrar izlenme. Sonda boş ekran bekletme (izleyici kaybı).

## 3. Formatlar (pilot)

| | Format | Mekanik | Seçilen | Ölçülen tempo |
|---|---|---|---|---|
| A | `formats/multiply.py` "Every bounce = +1 ball" | Beyaz ana top her çarpışmada arenaya +1 top ekler; ana top her eklemede %1,5 hızlanır; arena dolunca çember kırılır | seed 3 | 2 sn:5 · 8:25 · 14:48 · 20:103 · 23:144 · dolu 24,7 · kırılma 25,9 · bitiş 28,1 sn. Ses -13,4 LUFS |
| B | `formats/rings.py` "Can the ball escape 20 rings?" | 20 iç içe dönen boşluklu halka; top çıktıkça halka parçalanır, nota yükselir, top %3 hızlanır | seed 71 (120 tohum taramasından) | İlk kırılma 0,5 sn, ilk 1,5 sn'de 3 halka, en uzun takılma 3,1 sn, bitiş 23,7 sn. Ses -14,0 LUFS |
| C | `formats/pour.py` "1 Ball VS 5000 Balls" | Aynı cam bardağa 1 → 10 → 100 → 1000 → 5000 top; renk döküm sırasına göre → gökkuşağı katmanları; son kademede taşma | — | 1000 topta bardak ~%60 dolu, 5000'de 1868 top içeride, gerisi taşıyor |

Tempo ayarı öğrenimleri:
- A: "her topun her çarpışması +1" üstel büyür (6 sn'de 400 top); "sadece ana top" doğrusal kalır (30 sn'de 60).
  Çözüm: ana top + hızlanma + büyük toplar (r=26). Arena doldukça çarpışma sıklaşıyor → doğal ivme.
- B: halka aralığı top çapından küçükse (ilk denemede 17 px aralık, 26 px top) top bir sonraki halkanın içinde doğar ve
  hepsi zincirleme kırılır. Kırılma eşiği "merkez halka çizgisini geçti" + aralık 20 px, top r=11 ile çözüldü.
  Boşluk 0,62 rad iken takılmalar 10 sn'ye çıkıyordu → 0,95 rad ve daha hızlı dönüş.
- Tohum taraması (B): `--search N` render etmeden simüle eder, süre 22–34 sn ve en uzun takılması en kısa olanları sıralar.

## 4. Hat

```
formats/<f>.py:  simülasyon (pymunk, kare başına 3–4 alt adım) → kare listesi + ses olayları
                 → lib/canvas.Renderer (skia; parıltı çeyrek çözünürlükte; yazılar önbellekli) → ffmpeg x264 crf16 60 fps
                 → lib/audio.Mix (sentez + 10 ms kutuda yoğunluk sınırı + reverb + yumuşak tavan)
                 → lib/encode.mux (loudnorm -14 LUFS, AAC 256k) → final.mp4 + sheet.jpg
```
- Güvenli alan (`lib/canvas.py`): üst ~220, alt ~420, sağ ~150 px'e önemli şey koyma. Sayaç y≈470, arena merkezi y≈1010.
- Kurulum: `bash setup.sh` (skia-python için `libegl1` gerekir; ilk kurulumda `libEGL.so.1` hatası buydu).

## 5. Ölçülen performans

| İş | Ölçüm |
|---|---|
| 2D kare (170 top, parıltı, yazı) | 221 ms → optimizasyonla **137 ms** (parıltı yarım→çeyrek çözünürlük 68→17 ms; yazı gölgesi önbellek 24→~0 ms) |
| A render (1797 kare, ilk sürüm) | 5 dk 58 sn |
| B render (1576 kare) | 3 dk 38 sn |
| Blender 4.5 Cycles CPU, 4 çekirdek, karpuz 60 parça | 1080×1920 32 örnek **99 sn/kare**; 540×960 16 örnek 15 sn/kare |
| → 25 sn × 30 fps foto-gerçekçi 3D bu konteynerde | ~20 saat. Pratik değil → RTX'te render (tahmin: video başına ~1 saat Cycles, EEVEE ile dakikalar) |

3D başlangıç noktası: `blender/melon_still.py` (prosedürel karpuz, N düzlem kesimi, patlama anı; örnek `blender/melon_still_ornek.png`).
Bilinen kusurları: beyaz kabuk bandı kalın, zemin-arka plan çizgisi görünüyor (kavisli fon gerek).

## 6. Riskler

- Platformlar şablondan seri üretilmiş, birbirinin aynısı içeriğin erişimini/gelirini kısıyor (YouTube 2025'te bu kuralı
  sıkılaştırdı). Her videoda nesne, parametre, renk ve kanca değişmeli. Aynı videoyu başka hesaplarda yayınlama.
- Başka hesabın görsel kimliğini (isim, filigran, birebir sahne) kullanma.

## 7. Açık işler

1. Kullanıcıdan 3 pilot için geri bildirim (hangi format, tempo, ses).
2. Tutan formatın varyasyon üreticisi: tek komutla N farklı video (tohum + nesne + renk + kanca listesi).
3. Format oturunca **skill** yaz: fikir → parametre → simülasyon → render → ses → açıklama.
4. 3D: kullanıcının RTX makinesi için Blender script'leri (pastel parametre testleri: "Soft 0%", "Hole" tarzı ama özgün sahneler).
5. Kapak karesi ve platform açıklamaları her teslimde (`teslim/<video>/caption.md`).
