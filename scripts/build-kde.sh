#!/bin/bash
# Build only. This script never installs packages or restarts services.
set -euo pipefail
repo=$(cd -- "$(dirname -- "$0")/.." && pwd)
sources=${1:-"$repo/build/sources"}
jobs=${JOBS:-2}
test -f "$sources/applied-series.json"

# Debian remains the default. Other distributions must supply their packaged
# helper directory and PAM profile explicitly; this does not install PAM rules.
pam_configuration=${PLASMA_RDP_PAM_CONFIGURATION:-debian}
session_command=${PLASMA_RDP_SESSION_COMMAND:-/etc/plasmalogin/Xsession}
if [[ -n ${PLASMA_RDP_LIBEXECDIR:-} ]]; then
    libexecdir=$PLASMA_RDP_LIBEXECDIR
elif command -v dpkg-architecture >/dev/null 2>&1; then
    libexecdir="lib/$(dpkg-architecture -qDEB_HOST_MULTIARCH)/libexec"
else
    echo 'Set PLASMA_RDP_LIBEXECDIR to the distro Plasma Login Manager helper directory.' >&2
    exit 2
fi

cmake -S "$sources/krdp-6.7.4" -B "$sources/krdp-6.7.4/build" \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_SKIP_RPATH=ON \
    -DBUILD_TESTING=OFF -DBUILD_EXAMPLES=OFF -DBUILD_PLASMA_SESSION=ON
cmake --build "$sources/krdp-6.7.4/build" --target krdpserver --parallel "$jobs"

# Preserve the tested greeter variant: only NLA/routing, no user-session resize patch.
cmake -S "$sources/krdp-greeter-6.7.4" -B "$sources/krdp-greeter-6.7.4/build" \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_SKIP_RPATH=ON \
    -DBUILD_TESTING=OFF -DBUILD_EXAMPLES=OFF -DBUILD_PLASMA_SESSION=ON
cmake --build "$sources/krdp-greeter-6.7.4/build" --target krdpserver --parallel "$jobs"

cmake -S "$sources/plasma-login-manager-6.7.4" -B "$sources/plasma-login-manager-6.7.4/build" \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr -DBUILD_TESTING=OFF \
    -DDBUS_CONFIG_FILENAME=plasmalogin_org.freedesktop.DisplayManager.conf \
    -DPAM_OS_CONFIGURATION="$pam_configuration" -DSESSION_COMMAND="$session_command" \
    -DKDE_INSTALL_LIBEXECDIR="$libexecdir"
cmake --build "$sources/plasma-login-manager-6.7.4/build" --target plasmalogin --parallel "$jobs"

cmake -S "$sources/kpipewire-6.7.4" -B "$sources/kpipewire-6.7.4/build" \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr -DBUILD_TESTING=OFF
cmake --build "$sources/kpipewire-6.7.4/build" --target KPipeWire KPipeWireRecord --parallel "$jobs"
