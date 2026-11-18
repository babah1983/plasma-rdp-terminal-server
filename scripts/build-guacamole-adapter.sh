#!/bin/bash
# Compile on the same architecture/OS as guacd 1.6.0. Does not install or restart it.
set -euo pipefail
repo=$(cd -- "$(dirname -- "$0")/.." && pwd)
mkdir -p "$repo/build"
read -r -a cairo_flags <<< "$(pkg-config --cflags cairo)"
cc -shared -fPIC -O2 -Wall -Wextra -Werror \
    -I"$repo/upstream/guacamole-server-1.6.0/src/libguac" "${cairo_flags[@]}" \
    "$repo/runtime/guacamole-external-buffer-resize.c" -ldl \
    -o "$repo/build/libguac-external-buffer-resize.so"
