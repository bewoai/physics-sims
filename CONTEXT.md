# CONTEXT — physics-sims

Yeni oturumda **ilk okunacak dosya**. Ne yaptığımızı, nedenlerini, ölçtüklerimizi ve açık işleri anlatır.
Sayılar ölçümdür; tahminler "tahmin" diye işaretli.

- Başlangıç: 2026-10-08. Kullanıcı: studio@rastcreative.com (Türkçe, kısa ve net yazar)
- Hedef platformlar: Instagram Reels, TikTok, YouTube Shorts (üçü de 1080×1920)
- Durum: 12 format teslim edildi (`teslim/`). **Günlük otomatik paylaşım kuruldu** (§8); hesaplar ve Upload-Post bağlantısı kullanıcıda (`auto/KURULUM.md`)

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

## 3. Formatlar ve geri bildirim

### Kullanıcı geri bildirimi (tur 1)
- **A ve B iyi**, **C ("1 Ball VS 5000 Balls" bardağa döküm) kötü** → çıkarıldı (git geçmişinde `formats/pour.py`).
  Nedeni söylenmedi. Ölçülen kusurları: kademe başlarında ~1 sn sessiz/boş ekran, yoğun kademeler 10 topluk kademeden
  sessizdi, her kademede sahne sıfırlanıyor (birikim yok). Benzer "kademeli döküm" formatından kaçın; sorulabilir.
- **Kanca cümlesi sürekli ekranda kalsın** → `lib/hud.py`, tüm formatlarda y=300'de baştan sona.
- "10 tane daha kreatif" istendi → 10 yeni format üretildi (aşağıda 03–12).

### Teslim edilenler

| # | Dosya / kod | Mekanik | Tohum | Ölçülen tempo |
|---|---|---|---|---|
| 01 | `multiply.py` "Every bounce = +1 ball" | Ana top her çarpışmada +1 top, %1,5 hızlanır; dolunca çember kırılır | 3 | 2 sn:5 · 14:48 · 23:144 · dolu 24,7 · kırılma 25,9 |
| 02 | `rings.py` "Can the ball escape 20 rings?" | Dönen boşluklu halkalar, her kırılmada nota yükselir | 71 | ilk kırılma 0,5 sn, en uzun takılma 3,1 sn, bitiş 23,7 |
| 03 | `pendulum.py` "Wait until they line up again" | 18 sarkaç, T=27 sn'de (20+i) salınım; geri sayım; başı = sonu (döngü) | — | analitik |
| 04 | `laser.py` "1 laser inside a heart-shaped mirror" | Kalp aynada ışın, kalıcı iz; sekme hızı üstel (τ=4 sn) | — | 3000 sekme / 24 sn |
| 05 | `grow.py` "Every bounce, the ball gets bigger" | Her sekmede r×1,035, r0=40 | 7 | 69 sekme, dolma 21,0 sn |
| 06 | `galton.py` "400 balls. Will they make a bell curve?" | Kinematik Galton (p=0,5), top varacağı bölmenin renginde, sonda normal eğri | 5 | bölmeler 8·19·58·69·84·79·52·24·7 |
| 07 | `heptagon.py` "20 balls. 1 tiny exit." | Dönen yedigen (1,35 rad/s), 150 px açıklık | 27 | bitiş 23,0, en uzun bekleme 4,3 sn |
| 08 | `colorwar.py` "4 colors. Only 1 survives." | Pong Wars + büyük bölge = hızlı top + pay arttıkça yeni top; <16 kare elenir | 9 | elemeler 19,9 / 22,0 / 24,0 |
| 09 | `breakout.py` "Every brick = +1 ball" | Her kırılan tuğla → fırlatıcıdan +1 top; tuğla canı alt 1 → üst ~17 | 4 | temizlenme 21,9 sn, 211 top |
| 10 | `survivor.py` "Which number survives?" | 12 numaralı top, dönen kırmızı lazer yayı (zamanla uzar) değeni eler | 34 | ilk eleme 1,7, bitiş 23,9, en uzun ara 4,8 |
| 11 | `marble_race.py` "Which color wins?" | 8 misket, parkur (rampa, çivi, pervane, tampon, huni), kamera lideri izler, solda sıralama haritası | 4 | finiş 19,3, 10 liderlik değişimi, ikinciyle fark 0,03 sn |
| 12 | `domino.py` "Domino #1: 1 cm. Domino #22: 5.5 m." | Her domino 1,35×; gerçek ölçek (mm), yavaş çekim g×0,3; kamera uzaklaşır | — | son domino 20,5 sn'de yerde |

### Tempo/fizik öğrenimleri (tekrar yaşamamak için)
- **Tohum taraması her rastgele formatta şart** (`--search N`): render etmeden simüle et, süre 20–30 sn ve en uzun
  "olaysız" aralığı en kısa olanı seç. Hedef: ilk olay < 2 sn, en uzun boşluk < 5 sn, bitiş 20–28 sn.
- A: "her topun her çarpışması +1" üstel (6 sn'de 400); "sadece ana top" doğrusal → ana top + hızlanma + büyük top.
- B: halka aralığı > top çapı olmalı; kırılma "merkez çizgiyi geçti" ile ölçülmeli.
- 05: r0=16 ile ilk 12 sn top %4→%11 (sıkıcı açılış) → r0=40.
- 06: pymunk Galton çan vermedi (huni 2,6 çapta kemer yaptı; geniş huni kenardan kaydırıp iki tepe yaptı; çivi aralığı
  top çapına göre geniş olunca dağılım düz). Kinematik çözüm doğru ve hızlı.
- 07: kaçış "merkeze uzaklık" ile ölçülemez (üstten çıkan top dış kenarda sekiyor) → çokgen dışı testi. 30 top / 92 px
  açıklıkta son toplar 36 sn'de çıkamadı → 20 top, 150 px, v_floor 650.
- 08: saf Pong Wars 36 sn'de hiç eleme vermedi (paylar %22–29) → kartopu kuralları.
- 09: yeni top kırılan tuğlada doğunca duvar 1,4 sn'de zincirleme çöktü → fırlatıcıdan çıkış + tuğla canı.
- 10: lazer 0,45→1,7 rad iken 7–13 sn'de bitti → 0,16→0,75 rad, ω=0,75.
- 11: tampon rengi bir misket rengiyle aynı olmamalı (pembe tampon/PINK karıştı → beyaz halka).
- 12: ilk dominoya dönüş vermek yetmez (alt köşe zemine gömülür) → tepeden yatay darbe.

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
| Format başına render (60 fps, 20–28 sn) | 2,7–5 dk (Galton 162 sn, pendulum 314 sn; 2–3 iş paralel koşarken) |
| Blender 4.5 Cycles CPU, 4 çekirdek, karpuz 60 parça | 1080×1920 32 örnek **99 sn/kare**; 540×960 16 örnek 15 sn/kare |
| → 25 sn × 30 fps foto-gerçekçi 3D bu konteynerde | ~20 saat. Pratik değil → RTX'te render (tahmin: video başına ~1 saat Cycles, EEVEE ile dakikalar) |

3D başlangıç noktası: `blender/melon_still.py` (prosedürel karpuz, N düzlem kesimi, patlama anı; örnek `blender/melon_still_ornek.png`).
Bilinen kusurları: beyaz kabuk bandı kalın, zemin-arka plan çizgisi görünüyor (kavisli fon gerek).

## 6. Riskler

- Platformlar şablondan seri üretilmiş, birbirinin aynısı içeriğin erişimini/gelirini kısıyor (YouTube 2025'te bu kuralı
  sıkılaştırdı). Her videoda nesne, parametre, renk ve kanca değişmeli. Aynı videoyu başka hesaplarda yayınlama.
- Başka hesabın görsel kimliğini (isim, filigran, birebir sahne) kullanma.

## 7. Açık işler

1. Kullanıcıdan 12 format için geri bildirim: hangileri seri üretime girsin. C neden kötüydü (sorulabilir).
1b. Otomasyon: kullanıcı hesapları açıp Upload-Post'a bağlayacak, GitHub sırlarını girecek (`auto/KURULUM.md`); ilk gerçek
    paylaşımdan sonra `auto/history.jsonl` ve platform sonuçlarını kontrol et.
2. Tutan formatın varyasyon üreticisi: tek komutla N farklı video (tohum + nesne + renk + kanca listesi).
3. Format oturunca **skill** yaz: fikir → parametre → simülasyon → render → ses → açıklama.
4. 3D: kullanıcının RTX makinesi için Blender script'leri (pastel parametre testleri: "Soft 0%", "Hole" tarzı ama özgün sahneler).
5. Kapak karesi ve platform açıklamaları her teslimde (`teslim/<video>/caption.md`).

## 8. Otomatik paylaşım (2026-10-09)

Kullanıcı kararları: **tam otomatik** (onaysız), **her platformda günde 1**, yol seçimi bana bırakıldı → **Upload-Post**
(denetimli; resmi API'lerde TikTok ve YouTube denetimi bitene kadar videolar gizli kalıyor). Hesaplar henüz yok.

```
.github/workflows/daily.yml   cron 15:43 UTC + elle tetikleme (format, dry_run); sır yoksa zamanlı çalışma atlanır
auto/daily.py                 format seç (en uzun süredir paylaşılmayan) → tohum tara → render → QA → açıklama → yayın
auto/formats.py               12 format adaptörü: choose (günlük varyasyon) / check (sadece simülasyon) / make
auto/qa.py                    1080×1920·60fps·15–35 sn·-16…-12 LUFS·sessizlik ≤1,5 sn·donma ≤3 sn·bitişe ulaşma
auto/captions.py              format başına şablon + dönen hashtag; YouTube başlığı ≤100 + #shorts
auto/publish.py               Upload-Post: tek istek, 3 platform, async + durum sorgusu
auto/history.jsonl            her çalışma (Actions commit'ler); dry_run sırayı ilerletmez
```
- Varyasyon: tohum → parametreler (halka 14–20, sarkaç 15–20, Galton 300–450 top / 10–12 sıra, çokgen 6–8 kenar,
  survivor 10–14 top, domino K 1,3–1,36 / N 20–23 / yavaş çekim, renk savaşında 8 renkten 4'ü), `canvas.HUE_SHIFT`
  ile palet kaydırma (renk adı olan formatlarda kapalı), kanca ve açıklama şablonları.
- Kalite eşikleri teslim edilen 12 videoyla kalibre edildi; hepsi geçiyor (en uzun sessizlik domino 1,25 sn).
- Simülasyon kontrolü 0–4 sn/tohum. Uygun tohum oranı formatlara göre ~%4 (halka) – %80 (çarpışma).
- Uçtan uca dry-run (2026-10-09, 12 formatın hepsi): hepsi ilk tohumda kaliteden geçti; tarama 1 parti (halka 6,
  yedigen 2); render 178–281 sn (4 çekirdek, iki iş paralel). Örnek varyasyonlar: yedigen → 8 kenar/16 top,
  renk savaşı YELLOW/RED/PURPLE/BLUE, domino K=1,3 N=23 (3,2 m) yavaş çekim 0,16.
- Upload-Post istemcisi sahte HTTP ile denendi (alanlar, multipart, karışık sonuç → "partial"); gerçek hesapla
  henüz denenmedi — ilk gerçek paylaşımda `auto/history.jsonl` → `result` alanını kontrol et.
- Upload-Post: Basic plan gerekli (ücretsizde TikTok yok, 10 yükleme/ay). Limitler: TikTok 15, IG 50, YouTube 10 gönderi/gün.
- Yapılmadı: performans verisine göre format ağırlığı (izlenme/izlenme süresi). Upload-Post analitiği ya da platform
  istatistikleri bağlanınca `pick_format` ağırlıklı hale getirilebilir.
