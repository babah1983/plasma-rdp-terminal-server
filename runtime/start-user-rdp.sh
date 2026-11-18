#!/bin/sh
set -eu
case "$USER" in
    native-a) port=3391 ;;
    native-b) port=3392 ;;
    *) exit 1 ;;
esac
exec /opt/system-krdp-display/bin/krdpserver --plasma --monitor 0 --address 127.0.0.1 --port "$port" \
    --username greeter --password "$(cat password)" \
    --certificate "$PWD/cert.pem" --certificate-key "$PWD/key.pem"
