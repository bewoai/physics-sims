"""Görüntü + ses birleştirme, platform ses seviyesi (-14 LUFS) ve kontrol şeridi."""
import subprocess


def integrated(path):
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    vals = [l.split()[1] for l in r.stderr.splitlines() if l.strip().startswith("I:")]
    return float(vals[-1])


def mux(video, wav, out, lufs=-14):
    """Ölç → kazanç → sınırlayıcı. Tek geçişli loudnorm seyrek tıklı seste hedefe ulaşamadı (C: -17,2 LUFS)."""
    gain = lufs - integrated(wav) + 0.4          # sınırlayıcının yediği ~0,4 dB
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", video, "-i", wav,
         "-af", f"volume={gain:.2f}dB,alimiter=limit=0.84:attack=2:release=60:level=disabled",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
         "-shortest", "-movflags", "+faststart", out], check=True)
    return out


def contact_sheet(video, out, every=2.0, cols=8, width=270, rows=2):
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", video, "-vf",
         f"fps=1/{every},scale={width}:-1,drawtext=text='%{{pts\\:hms}}':x=6:y=6:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.5,"
         f"tile={cols}x{rows}", "-frames:v", "1", out], check=True)
    return out


def loudness(path):
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    lines = [l.strip() for l in r.stderr.splitlines() if l.strip().startswith(("I:", "LRA:", "Peak:"))]
    return " | ".join(lines[-3:])
