#!/bin/bash
# Run as root on the isolated Debian sid VM, after building the patched components.
set -euo pipefail
if [[ ${1:-} != --apply-to-disposable-vm ]]; then
    echo 'Usage: sudo bash runtime/install-handover.sh --apply-to-disposable-vm' >&2
    echo 'Changes the login manager and starts a headless lab; use only a disposable Debian VM.' >&2
    exit 2
fi
cd -- "$(dirname -- "$0")"
test -x /opt/system-plasma-login/plasmalogin
test -r /opt/system-krdp/lib/libKRdp.so.6
test -x /opt/system-krdp-display/bin/krdpserver
test -r /opt/system-krdp-display/lib/libKRdp.so.6
test -r /opt/system-kpipewire-shm/lib/libKPipeWire.so.6
test -r /opt/system-kpipewire-pool/lib/libKPipeWire.so.6
test -r /opt/system-kpipewire-pool/lib/libKPipeWireRecord.so.6
test -x /usr/sbin/nft
greeter=/var/lib/plasmalogin/.local/state/plasma-rdp

install -D -m 0755 dispatcher.py /usr/local/libexec/plasma-rdp-dispatcher
install -D -m 0755 on-plasma-login.py /usr/local/libexec/plasma-rdp-login-complete
install -D -m 0755 start-greeter-rdp.sh /usr/local/libexec/plasma-rdp-greeter
install -D -m 0755 start-user-rdp.sh /usr/local/libexec/plasma-rdp-user
install -D -m 0644 transport-isolation.nft /etc/plasma-rdp-lab.nft
install -D -m 0644 transport-isolation.service /etc/systemd/system/plasma-rdp-isolation.service
install -D -m 0644 plasma-rdp-dispatch.service /etc/systemd/system/plasma-rdp-dispatch.service
install -D -m 0644 login-manager.conf /etc/systemd/system/plasmalogin.service.d/rdp.conf
install -D -m 0644 greeter-kwin.conf /etc/systemd/user/plasma-login-kwin_wayland.service.d/rdp.conf
install -D -m 0644 greeter-rdp.service /etc/systemd/user/plasma-rdp-greeter.service
install -D -m 0644 user-rdp.service /etc/systemd/user/plasma-rdp-user.service
install -D -m 0644 krdp-display.desktop /usr/local/share/applications/org.kde.krdpserver-plasma-rdp.desktop
install -D -m 0644 sleep.conf /etc/systemd/sleep.conf.d/90-plasma-rdp-lab.conf
install -d /etc/plasmalogin.conf.d
printf '[Autologin]\nUser=\nSession=\nRelogin=false\n' > /etc/plasmalogin.conf.d/90-rdp-lab-no-autologin.conf
install -d -o plasmalogin -g plasmalogin -m 0700 "$greeter"
runuser -u plasmalogin -- sh -ec 'umask 077
    cd "$1"
    test -s password || openssl rand -hex 16 > password
    if ! test -s cert.pem || ! test -s key.pem; then
        openssl req -x509 -newkey rsa:2048 -nodes -days 30 -subj /CN=kde-system-rdp-lab \
            -addext "subjectAltName=IP:127.0.0.1,DNS:localhost" -keyout key.pem -out cert.pem
    fi' sh "$greeter"
usermod -aG video,render plasmalogin
# This stock PAM rule is packaged under /usr/lib/pam.d, which Debian PAM ignores.
for service in plasmalogin plasmalogin-greeter; do
    test -e "/etc/pam.d/$service" || install -m 0644 "/usr/lib/pam.d/$service" "/etc/pam.d/$service"
done
for account in native-a native-b; do
    account_home=$(getent passwd "$account" | cut -d: -f6)
    test -n "$account_home"
    state="$account_home/.local/state/plasma-rdp"
    install -d -o "$account" -g "$account" -m 0700 "$state"
    for item in password cert.pem key.pem; do
        install -o "$account" -g "$account" -m 0600 "$greeter/$item" "$state/$item"
    done
    user_units="$account_home/.config/systemd/user"
    runuser -u "$account" -- mkdir -p \
        "$user_units/plasma-workspace-wayland.target.wants" "$user_units/plasma-kwin_wayland.service.d"
    runuser -u "$account" -- tee "$user_units/plasma-kwin_wayland.service.d/virtual.conf" < user-kwin.conf >/dev/null
    runuser -u "$account" -- ln -sfn /etc/systemd/user/plasma-rdp-user.service \
        "$user_units/plasma-workspace-wayland.target.wants/plasma-rdp-user.service"
    runuser -u "$account" -- kwriteconfig6 --file kscreenlockerrc --group Daemon --key Autolock false
    usermod -aG video,render "$account"
    loginctl disable-linger "$account"
done

systemctl daemon-reload
systemctl --global enable plasma-rdp-greeter.service
systemctl enable plasma-rdp-isolation.service plasma-rdp-dispatch.service plasmalogin.service
systemctl set-default graphical.target
systemctl restart plasma-rdp-dispatch.service plasmalogin.service
