# physics-sims

Kodla üretilen "satisfying" fizik simülasyonu kısa videoları (IG Reels, TikTok, YouTube Shorts). Dil gerektirmeyen, global kitle.

**Her oturumun başında `CONTEXT.md` dosyasını oku.** Formatlar, komutlar, ölçülmüş değerler, kararlar ve açık işler orada.

Kısa kurallar:
- Türkçe, kısa ve net yaz. Belirsizlikte kullanıcıya sor (AskUserQuestion).
- Videoyu izleyip dinleyemezsin: kontrol şeridi (`sheet.jpg`), kare, spektrogram ve ölçümle çalış.
- Tahmin etme, ölç: tempo (simülasyon istatistiği), render süresi, ses seviyesi (LUFS).
- Birebir kopya yok. Başka hesabın formatını değil, izlenme mekaniğini al (CONTEXT.md §2). Her videoda nesne/parametre/kanca değişsin.
- Telifli müzik yok; tüm ses `lib/audio.py` ile sentezlenir.
- Limit yaklaşırsa çıktıyı hemen sun. Push edilmeyen her şey oturum kapanınca kaybolur.

## Komutlar
```bash
bash setup.sh                                    # pymunk, skia-python, soundfile, numpy, ffmpeg
python3 formats/<format>.py --seed N --out out/x # ör. multiply, rings, galton (liste: README.md)
python3 formats/<format>.py --search N           # render etmeden tohum taraması
python3 -m auto.daily --format galton --dry-run  # günlük paylaşım önizlemesi
```
- `lib/`: canvas, audio, encode, hud, produce; `formats/*.py`: her video formatı; `teslim/`: yayınlanacak videolar
- Günlük otomatik paylaşım: `.github/workflows/daily.yml` + `auto/` (kurulum `auto/KURULUM.md`); platform anahtarları GitHub Secrets'ta, repoya yazma.
