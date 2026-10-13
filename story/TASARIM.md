# Tasarım dili seçenekleri (2026-10-13)

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
