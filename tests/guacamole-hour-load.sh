#!/bin/sh
set -eu
# Dedicated, bounded test processes. Leaves Kate and the Plasma sessions intact.
for account in native-a native-b; do
    uid=$(id -u "$account")
    sudo -u "$account" env XDG_RUNTIME_DIR=/run/user/$uid DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$uid/bus \
        systemd-run --user --collect --unit=rdp-guac-hour-load \
        --setenv=QT_QPA_PLATFORM=wayland --setenv=WAYLAND_DISPLAY=wayland-0 \
        /usr/bin/konsole --separate -e /usr/bin/timeout 4200 /bin/sh -c '
            n=0
            while :; do
                n=$((n+1))
                printf "\033[3%sm%s %-8s frame=%08d Plasma/Guacamole resize and reconnect load\033[0m\n" "$((n%7+1))" "$(date -u +%H:%M:%S)" "$USER" "$n"
                sleep .08
            done'
done
