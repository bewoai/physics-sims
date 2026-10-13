# Hesaplar: adlar, bio'lar, açıklama kalıbı

Kod karşılığı: `story/brand.py` (ad, rozet, etiket), `story/captions.py` (açıklama üretici),
`story/avatar.py` (profil fotoğrafı). Kullanıcı adlarının boşta olup olmadığını buradan doğrulayamıyorum;
hesap açarken platformda kontrol et. Üç platformda aynı kullanıcı adı olsun.

## Adlar

| | EN (seçilen) | TR (seçilen) |
|---|---|---|
| Görünen ad | **Behind the Landmark** | **Kartpostalın Arkası** |
| Kullanıcı adı (IG / TikTok / YouTube) | `@behindthelandmark` | `@kartpostalinarkasi` |
| Doluysa | `@behind.the.landmark`, `@behindthelandmarks` | `@kartpostalin.arkasi`, `@kartpostalinarkasi.tr` |
| Seri etiketi | `#behindthelandmark` | `#kartpostalinarkasi` |
| Videodaki rozet | BEHIND THE LANDMARK | KARTPOSTALIN ARKASI |

Neden:
- **Behind the Landmark:** vaat adın içinde (simge yapının arkasındaki hikâye); "landmark" aranan kelime; uluslararası
  kitle için netlik espriden önemli. Videoda zaten bu rozet var.
- **Kartpostalın Arkası:** "Ön yüzünü herkes bilir, arkasında yazanı biz anlatıyoruz." Her bölümdeki kartpostal
  yer kartıyla aynı fikir. "Perde Tarih"e benzemiyor (önceki taslaktaki `#perdearkası` bu yüzden kaldırıldı).
  İlk taslak "Mekânın Hikâyesi" elendi: Türkçe sosyal medyada "mekân" kafe/bar önerisi çağrıştırıyor.
- Yedekler — EN: *Back of the Postcard* (TR adıyla eş), *Landmark Lore* (kısa). TR: *Mekânın Hikâyesi*, *Taş ve Zaman*.

## Profil

Profil fotoğrafı: `story/avatar.py` → Siluet Sinema: ışık kaynağının önünde kubbeli yapı silueti, huzmeler.
EN gece mavisi (ay), TR gün batımı (güneş); iki hesap telefonda karışmasın. Yazı yok (daireye küçülünce okunmuyor).

**EN — Instagram (≤ 150):**
```
Everyone knows the view. This is the story behind it. 🏛️
One landmark · one minute · sources in every caption
🎙️ AI narration
```
**EN — TikTok (≤ 80):** `The story behind famous landmarks. 1 place, 1 minute. AI narration.`

**EN — YouTube kanal açıklaması:**
```
Everyone knows what the world's famous landmarks look like. Few know why they exist, why they look the way
they do, or how close they came to disappearing. One landmark, one story, about a minute each.
Facts are checked against the sources listed under every video.
Narration is an AI voice (text-to-speech). Illustrations and animation are made in code.
```

**TR — Instagram (≤ 150):**
```
Ön yüzünü herkes bilir. Arkasında yazanı biz anlatıyoruz. ✉️
Bir yapı · bir dakika · kaynak her açıklamada
🎙️ Yapay zekâ seslendirme
```
**TR — TikTok (≤ 80):** `Ünlü yapıların arkasındaki hikâye. 1 yer, 1 dakika. YZ seslendirme.`

**TR — YouTube kanal açıklaması:**
```
Dünyanın ünlü yapılarının ön yüzünü herkes bilir: kartpostallardaki o manzara. Biz arkasını anlatıyoruz: neden
yapıldılar, neden böyle görünüyorlar, yok olmaktan nasıl kurtuldular. Her videoda bir yer, bir hikâye, yaklaşık
bir dakika. Bilgiler her videonun altındaki kaynaklarla doğrulanır.
Seslendirme yapay zekâ (metinden sese). Çizim ve animasyon kodla üretilir.
```

Yapay zekâ beyanı: bio'daki satır + TikTok'ta yüklerken "AI-generated content" anahtarı açık. EMA Lightning'in
model kartı sentetik ses beyanı istiyor; Meta/TikTok gerçekçi YZ sesi için etiket istiyor.

## Açıklama kalıbı

Bölüm JSON'unda dil başına: `title` (YouTube, soru biçimi, ≤ 90), `lines` (2 satır: kanca + düğüm),
`share` (TR'de zorunlu; EN kalıptan: "Send this to someone who's been to {city}."), `hashtags` (seri + yer + genel,
toplam 5). Bölüm başına: `source_short` (açıklamadaki kısa kaynak), `sources` (YouTube açıklamasında tam liste).

```
{kanca: videonun ilk cümlesinin gerçek bilgi hâli}
{düğüm: neden/nasıl, tek cümle}

📍 {şehir}, {ülke} · {yıl}
Kaynaklar: {kısa kaynak}

{paylaşım çağrısı}

{#seri #yer #yer2 #genel #genel}
```
Yapma: "yorum yaz / beğen" dilenmesi (Meta erişimi düşürüyor), üstünlük iddiası ("kimsenin bilmediği"),
5'ten fazla hashtag, kaynaksız sayı.

## Eyfel pilotu — yapıştırmaya hazır

`python3 story/captions.py story/episodes/eiffel.json` çıktısı:

**EN — Instagram + TikTok**
```
The Eiffel Tower was supposed to come down in 1909.
Its permit lasted only 20 years. Radio saved it.

📍 Paris, France · 1889
Sources: toureiffel.paris · JSTOR Daily

Send this to someone who's been to Paris.

#behindthelandmark #eiffeltower #paris #history #historyfacts
```
**EN — YouTube başlık:** `Why didn't Paris tear down the Eiffel Tower? #shorts`

**TR — Instagram + TikTok**
```
Eyfel Kulesi'nin 1909'da yıkılması gerekiyordu.
İzni sadece 20 yıllıktı. Onu telsiz kurtardı.

📍 Paris, Fransa · 1889
Kaynaklar: toureiffel.paris · JSTOR Daily

Paris'e gitmiş birine gönder.

#kartpostalinarkasi #eyfelkulesi #paris #tarih #bilgi
```
**TR — YouTube başlık:** `Paris, Eyfel Kulesi'ni neden yıkmadı? #shorts`

YouTube açıklamaları (tam kaynak listesi + YZ beyanı) için scripti çalıştır.
