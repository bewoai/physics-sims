# physics-sims

Kodla üretilen fizik simülasyonu kısa videoları: 1080×1920, 60 fps, 20–35 sn, sentez ses, -14 LUFS.
Yapay zeka video modeli kullanılmaz: her video bir parametre dosyasından deterministik olarak üretilir,
aynı tohum aynı videoyu verir.

```bash
bash setup.sh
python3 formats/multiply.py --seed 3 --out out/a           # 01 Every bounce = +1 ball
python3 formats/rings.py --seed 71 --out out/b             # 02 Can the ball escape 20 rings?
python3 formats/pendulum.py --out out/pendulum             # 03 sarkaç dalgası
python3 formats/laser.py --out out/laser                   # 04 kalp aynada lazer
python3 formats/grow.py --seed 7 --out out/grow            # 05 büyüyen top
python3 formats/galton.py --out out/galton                 # 06 Galton tahtası
python3 formats/heptagon.py --seed 27 --out out/heptagon   # 07 dönen yedigen
python3 formats/colorwar.py --seed 9 --out out/colorwar    # 08 renk savaşı
python3 formats/breakout.py --seed 4 --out out/breakout    # 09 tuğla kırma
python3 formats/survivor.py --seed 34 --out out/survivor   # 10 son kalan top
python3 formats/marble_race.py --seed 4 --out out/marble_race  # 11 misket yarışı
python3 formats/domino.py --out out/domino                 # 12 domino büyütme
```

Rastgele formatlarda yeni varyasyon: `--search N` ile tohum taraması (render etmeden tempo ölçer), sonra `--seed`.

Her çıktı klasöründe: `video.mp4` (sessiz), `mix.wav`, `final.mp4` (teslim), `sheet.jpg` (2 sn'de bir kare, kontrol için).

```
lib/canvas.py    skia ile kare çizimi, parıltı, yazı önbelleği, ffmpeg borusu, platform güvenli alanları
lib/audio.py     çarpışma olaylarından ses sentezi (pluck, bell, pop, tick, shatter...), yoğunluk sınırı, reverb
lib/encode.py    görüntü+ses birleştirme (-14 LUFS), kontrol şeridi, ses ölçümü
lib/hud.py       sabit kanca cümlesi + sayaç
lib/produce.py   ses → birleştirme → kontrol şeridi
formats/*.py     her format: simülasyon → kareler → ses olayları
teslim/          yayınlanacak videolar + platform açıklamaları
```

**Günlük otomatik paylaşım** (TikTok + Instagram Reels + YouTube Shorts): `.github/workflows/daily.yml` + `auto/`.
Kurulum: `auto/KURULUM.md`. Yerelde önizleme: `python3 -m auto.daily --format galton --dry-run`.

Ayrıntılar, ölçümler ve kararlar: `CONTEXT.md`.
