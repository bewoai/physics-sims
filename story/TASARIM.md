# Tasarım dili (2026-10-13)

**Karar: Pul Gravürü** (kullanıcı seçti). Uygulama: `story/gravur.py` (seri tarzı; render varsayılanı).

## Seçenekler

Kullanıcı: "Bit_wonder piksel tarzda yapmış, bizim de özgün bir tarzımız olmalı." Aynı an (Eyfel kancası) dört
tarzda çizildi: `python3 story/looks.py out/story/looks` → `teslim/hikaye/tasarim/karsilastirma.jpg`.
Piksel sanatı bilerek yok (rakibin tarzı). Yazı tipleri Google Fonts, OFL lisanslı (`assets/fonts/`), Türkçe
karakterlerin hepsi var (glif kontrolü yapıldı).

| | 1 Pul Gravürü | 2 Seyahat Afişi | 3 Risograf | 4 Kâğıt Kesik |
|---|---|---|---|---|
| Fikir | Pul/banknot oyma baskısı: kâğıt üstüne tek mürekkep, kırmızı damga | 1930'lar Art Deco seyahat afişi | 3 mürekkepli serigrafi: yarım ton, kayık baskı | Katmanlı kâğıt diorama, gölgeli |
| Palet | kâğıt #EEE4CC, mürekkep #1E2233, tek vurgu #C23B22 | lacivert, krem, altın, turuncu; bant gökyüzü | mavi #0078BF, pembe #FF48B0, sarı #FFE800 | çivit katmanlar, krem, altın, mercan |
| Yazı | Playfair Display 900 + Cormorant | Bebas Neue (hep büyük harf) | Archivo Black + Space Grotesk | Fraunces 900 |
| İmza öğe | çift çizgili pul çerçevesi, "No. 001" bölüm no. | dev yer adı "PARİS 1889", güneş ışınları, madalyon | çıkartma altyazı kutuları | oyulmuş dantel kule, katman gölgeleri |
| Hareket | çizgiler çizilerek belirir, damga iner | geometrik silme, ışınlar döner | mürekkep katmanı titrer | paralaks, pop-up kitap gibi kalkan katman |
| Çizim süresi (ölçüldü) | 82 ms/kare | 29 ms/kare | ~1,2 sn/kare (3 × 0,4 sn yarım ton) | 1981 ms/kare (tam ekran bulanık gölge; önbellekle düşer) |
| 2,5 Mbps sonrası SSIM* | 0,953 | 0,994 | 0,880 | 0,992 |

\* Yavaş zoom (+%8, 3 sn) videosu kayıpsız ve 2,5 Mbps (IG/TikTok yeniden sıkıştırmasına yakın) kodlanıp
karşılaştırıldı. Mevcut tarz 0,996. Gravürde düşüş ince ay halkaları ve küçük yıldızlardan; kazıma çizgileri
gözle net kalıyor (kırpım karşılaştırması yapıldı). Aralığı 9 → 13 px yapmak yalnızca 0,963'e çıkardı.
Risografta yarım ton noktaları bulanıklaşıyor; hücreyi 11 → 18 px yapmak düzeltmedi (0,879).

Öneri: **1 Pul Gravürü.** Kısa video tarih nişinde görmedik (rakipler düz illüstrasyon ve piksel), hesap adıyla
aynı nesne (pul, kartpostal), "No. 001" numarası koleksiyon/seri izleme hissi veriyor, açık zemini karanlık akışta
ayrışıyor, ucuz render. Riski: tek renk → duygusal sahnelerde kırmızı vurgu ve ton yükü taşır; ince ayrıntı
(≤ 2 px çizgi) platform sıkıştırmasında kayboluyor, kalın tut.

## Pul Gravürü kuralları (story/gravur.py)

- Renk: kâğıt #EEE4CC, mürekkep #1E2233, tek vurgu kırmızı #C23B22 (damga, söylenen kelime, sinyal, Mors).
  Başka renk yok; ton = tarama yoğunluğu (gece kalın/sık, gündüz ince/seyrek, savaş en koyu).
- Gökyüzü taraması ekrana sabit (kamera itmesi sahneyi büyütür, çizgileri değil): kayan ince çizgi sıkıştırmada
  bit yiyor. Ay ve projektör ışıkları taramadan oyulur (delikler kamera matrisiyle ekrana eşlenir).
- Çizgi kalınlığı ≥ 1,5 px. Yapılar: kâğıt dolgu + mürekkep kontur + sağ yarıda dikey gölge taraması.
- Çerçeve: çift çizgili pul penceresi; üst boşlukta "No. 001", seri adı, "PARİS · 1889". Bölüm numarası
  bölüm JSON'undaki `no`.
- Altyazı: kâğıt etiket (mürekkep kontur + kaydırılmış mürekkep gölge); söylenen kelime kırmızı, gelecek kelimeler
  soluk. Taralı zemin üstündeki serbest yazılar kâğıt renkli hale (kontur) alır.
- Jenerik: perde yerine kırmızı posta damgası (üst yayda seri adı, ortada yer + yıl, alt yayda bölüm no.,
  sağda dalgalı iptal çizgileri) 1. cümleden 0,35 sn önce çarpar; ses: damga gümü.
- Belgeler (izin, gazete, kartpostal): kâğıt + çift çerçeve; gölge bulanık değil, taralı.
