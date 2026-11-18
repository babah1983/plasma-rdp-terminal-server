#!/usr/bin/env python3
"""Pass a successful, allowlisted PLM login to the RDP dispatcher."""
import os
import pwd
import socket
import sys
import tempfile
from pathlib import Path

PORTS = {"native-a": 3391, "native-b": 3392}
CONTROL = "/run/plasma-rdp-dispatch/control.sock"

def main():
    if os.getuid() != 0 or len(sys.argv) != 2 or sys.argv[1] not in PORTS:
        return 1
    greeter = pwd.getpwnam("plasmalogin")
    runtime = Path(f"/run/user/{greeter.pw_uid}")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as broker:
        broker.settimeout(2)
        broker.connect(CONTROL)
        broker.sendall(f"{PORTS[sys.argv[1]]}\n".encode("ascii"))
        with broker.makefile("rb") as stream:
            token = stream.readline(128)
    if not token.startswith(b"Cookie: msts=") or not token.endswith(b"\r\n") or len(token) != 47:
        return 1
    with tempfile.NamedTemporaryFile(dir=runtime, prefix=".plasma-rdp-route-", delete=False) as file:
        name = Path(file.name)
        try:
            file.write(token)
            file.flush()
            os.fchown(file.fileno(), greeter.pw_uid, greeter.pw_gid)
            name.replace(runtime / "plasma-rdp-route")
        finally:
            name.unlink(missing_ok=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
