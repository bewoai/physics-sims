# physics-sims

Kodla üretilen fizik simülasyonu kısa videoları: 1080×1920, 60 fps, 20–35 sn, sentez ses, -14 LUFS.
Yapay zeka video modeli kullanılmaz: her video bir parametre dosyasından deterministik olarak üretilir,
aynı tohum aynı videoyu verir.

```bash
bash setup.sh
python3 formats/multiply.py --seed 3 --out out/a      # "Every bounce = +1 ball"
python3 formats/rings.py --search 120                 # halka formatı için tempo taraması
python3 formats/rings.py --seed 71 --out out/b        # "Can the ball escape 20 rings?"
python3 formats/pour.py --out out/c                   # "1 Ball VS 5000 Balls"
```

Her çıktı klasöründe: `video.mp4` (sessiz), `mix.wav`, `final.mp4` (teslim), `sheet.jpg` (2 sn'de bir kare, kontrol için).

```
lib/canvas.py    skia ile kare çizimi, parıltı, yazı önbelleği, ffmpeg borusu, platform güvenli alanları
lib/audio.py     çarpışma olaylarından ses sentezi (pluck, bell, pop, tick, shatter...), yoğunluk sınırı, reverb
lib/encode.py    görüntü+ses birleştirme (-14 LUFS), kontrol şeridi, ses ölçümü
formats/*.py     her format: simülasyon → kareler → ses olayları
teslim/          yayınlanacak videolar + platform açıklamaları
```

Ayrıntılar, ölçümler ve kararlar: `CONTEXT.md`.
