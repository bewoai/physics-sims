# Otomatik paylaşım — kurulum (bir kerelik)

Sistem hazır: GitHub Actions her gün 15:43 UTC'de (TR 18:43) yeni bir video üretir, kalite kontrolünden geçirir ve
Upload-Post üzerinden **TikTok + Instagram Reels + YouTube Shorts**'a yükler. Senin yapacakların:

## 1. Üç hesabı aç (aynı isimle)
- **Instagram**: hesabı aç → Ayarlar → "Hesap türü ve araçlar" → **Profesyonel hesaba geç** (Creator). API sadece profesyonel hesaplara paylaşım yapar.
- **TikTok**: normal hesap yeterli.
- **YouTube**: Google hesabıyla bir **kanal** oluştur.
- İsim önerileri (müsaitliğini sen kontrol et): `bouncelab.sim`, `physicscandy`, `calm.chaos.sim`, `looplab.physics`.
- İlk gün profil fotoğrafı ve kısa bir bio koy (ör. "Satisfying physics, one simulation a day"). Boş profil erişimi düşürür.

## 2. Upload-Post
1. upload-post.com'a kaydol → **Basic plan** (aylık 24 $, yıllık ödemede ayda 16 $).
   Ücretsiz planda TikTok yok ve ayda 10 yükleme sınırı var; günde 1 video × 3 platform buna sığmaz.
2. Bir **profil** oluştur (ör. `physics`) → bu profile Instagram, TikTok ve YouTube hesaplarını bağla.
3. **API anahtarını** kopyala.

## 3. GitHub sırları
Repo → Settings → Secrets and variables → Actions → New repository secret:
- `UPLOAD_POST_API_KEY` = Upload-Post API anahtarı
- `UPLOAD_POST_USER` = 2. adımdaki profil adı (ör. `physics`)

Sırlar girilene kadar zamanlanmış çalışma hiçbir şey yapmadan biter (Actions dakikası harcamaz).

## 4. İlk deneme
Repo → Actions → **daily-post** → Run workflow:
1. `dry_run` işaretli çalıştır → bitince sayfanın altındaki **Artifacts**'tan videoyu, kontrol şeridini ve açıklamayı indir.
2. Beğendiysen `dry_run` işaretsiz çalıştır → ilk gerçek paylaşım. Sonrası her gün kendiliğinden.

## Günlük işleyiş
- Format sırası: 12 formatın en uzun süredir paylaşılmayanı (aynı format üst üste gelmez, 12 günde bir döner).
- Her video yeni: yeni tohum + o güne özgü varyasyon (halka/top/sarkaç sayısı, renk paleti, kanca cümlesi, açıklama).
- Kalite kontrolü (`auto/qa.py`): 1080×1920, 60 fps, 15–35 sn, -16…-12 LUFS, 1,5 sn'den uzun sessizlik yok,
  3 sn'den uzun donuk görüntü yok, simülasyon bitişine ulaşmış. Geçemeyen video yüklenmez, sıradaki tohum denenir.
- Bir şey ters giderse (üretim, kalite, yayın) iş "failed" olur ve GitHub sana e-posta atar.
- Her paylaşım `auto/history.jsonl`'a yazılır (format, tohum, açıklama, platform sonuçları).
- Videolar 14 gün boyunca Actions → ilgili çalışma → Artifacts'ta durur.

## Ayarlar
- Saat: `.github/workflows/daily.yml` içindeki `cron` satırı (UTC).
- Açıklama/hashtag şablonları: `auto/captions.py`.
- Hangi formatlar dönsün: `auto/daily.py` → `ORDER` listesi.
- Platform listesi: `auto/publish.py` → `PLATFORMS`.

## Maliyet (tahmin)
- Upload-Post Basic: aylık 16–24 $.
- GitHub Actions: video başına ~15–25 dk. Ayda ~600 dk; özel repolarda ücretsiz kota planına bağlı
  (GitHub Free: 2000 dk/ay).
