"""Yayından önce otomatik kalite kontrolü. Kullanıcı tam otomatik seçti: video ancak bunları geçerse yüklenir.

Ölçütler, elle teslim edilen 12 videonun ölçümlerinden (CONTEXT.md §3, §5):
- 1080×1920, 60 fps, 15–35 sn
- entegre ses -16…-12 LUFS
- konuşma/müzik yok ama 1,5 sn'den uzun sessizlik de olmamalı (son 2,5 sn hariç; C formatındaki hata buydu)
- 3 sn'den uzun donuk görüntü yok
- formatın kendi bitişine ulaşmış olması (kazanan, kırılma, hizalanma…)
"""
import json
import subprocess

import numpy as np

from lib import encode


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path],
                       capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def longest_silence(path, win=0.25, floor_db=-45.0, skip_tail=2.5):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    n = int(16000 * win)
    k = max(0, (len(x) - int(16000 * skip_tail)) // n)
    run = best = 0
    for i in range(k):
        rms = np.sqrt(np.mean(x[i * n:(i + 1) * n] ** 2)) + 1e-9
        run = run + 1 if 20 * np.log10(rms) < floor_db else 0
        best = max(best, run)
    return best * win


def longest_freeze(path, min_d=1.0):
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-vf", f"scale=270:-1,freezedetect=n=0.001:d={min_d}",
                        "-an", "-f", "null", "-"], capture_output=True, text=True)
    durs = [float(l.split("freeze_duration:")[1]) for l in r.stderr.splitlines() if "freeze_duration:" in l]
    return max(durs) if durs else 0.0


def check(path, complete):
    info = probe(path)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    num, den = map(int, v["r_frame_rate"].split("/"))
    dur = float(info["format"]["duration"])
    lufs = encode.integrated(path)
    sil = longest_silence(path)
    frz = longest_freeze(path)
    m = {"w": v["width"], "h": v["height"], "fps": num / den, "duration": round(dur, 2), "lufs": lufs,
         "silence": sil, "freeze": frz, "complete": complete,
         "size_mb": round(int(info["format"]["size"]) / 1e6, 1)}
    problems = []
    if (m["w"], m["h"]) != (1080, 1920):
        problems.append("çözünürlük")
    if abs(m["fps"] - 60) > 0.5:
        problems.append("fps")
    if not 15 <= dur <= 35:
        problems.append(f"süre {dur:.1f}")
    if not -16 <= lufs <= -12:
        problems.append(f"ses {lufs}")
    if sil > 1.5:
        problems.append(f"sessizlik {sil:.1f} sn")
    if frz > 3.0:
        problems.append(f"donuk görüntü {frz:.1f} sn")
    if not complete:
        problems.append("bitişe ulaşmadı")
    if m["size_mb"] > 250:
        problems.append("dosya büyük")
    m["problems"] = problems
    m["ok"] = not problems
    return m
