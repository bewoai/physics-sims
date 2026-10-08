#!/usr/bin/env bash
# Bulut konteynerinde (ya da yerelde) hattı kurar. skia-python libEGL ister.
set -e
if ! ldconfig -p | grep -q libEGL.so.1; then
  (apt-get install -y -q libegl1 libgl1 || (apt-get update -q && apt-get install -y -q libegl1 libgl1)) >/dev/null
fi
pip install -q pymunk skia-python soundfile numpy
command -v ffmpeg >/dev/null || (apt-get install -y -q ffmpeg >/dev/null)
python3 -c "import pymunk, skia, soundfile; print('hazır: pymunk', pymunk.version, '| skia', skia.__version__)"
