#!/bin/bash
# Real codec and KRdp callback checks. No live session connections or restarts.
set -euo pipefail
repo=$(cd -- "$(dirname -- "$0")/.." && pwd)
sources=${1:-"$repo/build/sources"}
out="$repo/build/tests"
mkdir -p "$out"
read -r -a codec_flags <<< "$(pkg-config --cflags --libs freerdp3)"
c++ -std=c++17 "$repo/tests/progressive-surface-roundtrip.cpp" "${codec_flags[@]}" -o "$out/progressive-roundtrip"
set +e
"$out/progressive-roundtrip" old
old_status=$?
set -e
test "$old_status" -eq 1
"$out/progressive-roundtrip"

read -r -a flags <<< "$(pkg-config --cflags --libs Qt6Core Qt6Gui freerdp3 libpipewire-0.3)"
c++ -std=c++20 -fPIC "$repo/tests/video-owner-thread.cpp" \
    -I"$sources/krdp-6.7.4/src" -I"$sources/krdp-6.7.4/build/src" \
    -I"$sources/kpipewire-6.7.4/src" -I"$sources/kpipewire-6.7.4/build/src" "${flags[@]}" \
    -L"$sources/krdp-6.7.4/build/bin" -lKRdp -o "$out/video-owner-thread"
LD_LIBRARY_PATH="$sources/krdp-6.7.4/build/bin${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" "$out/video-owner-thread"

c++ -std=c++20 -fPIC "$repo/tests/input-button-position.cpp" \
    -I"$sources/krdp-6.7.4/src" -I"$sources/krdp-6.7.4/build/src" "${flags[@]}" \
    -L"$sources/krdp-6.7.4/build/bin" -lKRdp -o "$out/input-button-position"
LD_LIBRARY_PATH="$sources/krdp-6.7.4/build/bin${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" "$out/input-button-position"
