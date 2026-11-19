#!/bin/sh
set -eu
exec /opt/system-krdp/bin/krdpserver --plasma --monitor 0 --address 127.0.0.1 --port 3390 \
    --username greeter --password "$(cat password)" \
    --certificate "$PWD/cert.pem" --certificate-key "$PWD/key.pem"
