#!/bin/bash
# Populate a reviewable staging directory; no writes to the live /opt.
set -euo pipefail
repo=$(cd -- "$(dirname -- "$0")/.." && pwd)
sources=${1:-"$repo/build/sources"}
stage=${2:-"$repo/build/stage"}
if [[ -e "$stage" ]]; then
    printf 'Staging directory already exists; choose a new destination: %s\n' "$stage" >&2
    exit 2
fi
mkdir -p "$stage"
install -D -m 0755 "$sources/plasma-login-manager-6.7.4/build/bin/plasmalogin" "$stage/opt/system-plasma-login/plasmalogin"
install -D -m 0644 "$sources/krdp-greeter-6.7.4/build/bin/libKRdp.so.6.7.4" "$stage/opt/system-krdp/lib/libKRdp.so.6.7.4"
ln -sfn libKRdp.so.6.7.4 "$stage/opt/system-krdp/lib/libKRdp.so.6"
install -D -m 0644 "$sources/krdp-6.7.4/build/bin/libKRdp.so.6.7.4" "$stage/opt/system-krdp-display/lib/libKRdp.so.6.7.4"
ln -sfn libKRdp.so.6.7.4 "$stage/opt/system-krdp-display/lib/libKRdp.so.6"
install -D -m 0755 "$sources/krdp-6.7.4/build/bin/krdpserver" "$stage/opt/system-krdp-display/bin/krdpserver"
install -D -m 0644 "$sources/kpipewire-6.7.4/build/bin/libKPipeWire.so.6.7.4" "$stage/opt/system-kpipewire-shm/lib/libKPipeWire.so.6.7.4"
ln -sfn libKPipeWire.so.6.7.4 "$stage/opt/system-kpipewire-shm/lib/libKPipeWire.so.6"
for library in KPipeWire KPipeWireRecord; do
    install -D -m 0644 "$sources/kpipewire-6.7.4/build/bin/lib$library.so.6.7.4" "$stage/opt/system-kpipewire-pool/lib/lib$library.so.6.7.4"
    ln -sfn "lib$library.so.6.7.4" "$stage/opt/system-kpipewire-pool/lib/lib$library.so.6"
done
printf 'Staged files in %s\n' "$stage"
