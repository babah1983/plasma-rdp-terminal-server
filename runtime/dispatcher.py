#!/usr/bin/env python3
"""Local RDP dispatcher. A trusted login manager issues single-use routes."""

import asyncio
import logging
import os
import secrets
import socket
import struct

PUBLIC_PORT = 3389
GREETER_PORT = 3390
SESSION_PORTS = range(3391, 3411)
CONTROL_PATH = "/run/plasma-rdp-dispatch/control.sock"
TOKEN_PREFIX = b"Cookie: msts="
TOKEN_LENGTH = 32
ROUTE_LIFETIME = 30
MAX_ROUTES = 128
MAX_PEERS = 32


async def read_request(reader):
    header = await reader.readexactly(4)
    size = int.from_bytes(header[2:4], "big")
    if header[:2] != b"\x03\x00" or not 11 <= size <= 260:
        raise ValueError(f"Invalid TPKT header (length {size})")
    packet = header + await reader.readexactly(size - 4)
    if packet[4] != size - 5 or packet[5] != 0xE0:
        raise ValueError(f"Invalid X.224 connection request (length {size}, LI {packet[4]}, type {packet[5]})")
    first_field = packet[11:]
    if not first_field.startswith(TOKEN_PREFIX):
        return packet, None
    token, delimiter, negotiation = first_field[len(TOKEN_PREFIX):].partition(b"\r\n")
    # Windows App can wrap opaque load-balancing data in its own cookie.
    token = token.removeprefix(TOKEN_PREFIX)
    if not delimiter or len(token) != TOKEN_LENGTH:
        raise ValueError(f"Invalid routing token (length {len(token)}, CRLF {bool(delimiter)})")
    # The backend does not route. Strip the cookie and any outer CRLF before
    # presenting its ordinary X.224 negotiation request to FreeRDP.
    negotiation = negotiation.removeprefix(b"\r\n")
    size = 11 + len(negotiation)
    clean_header = packet[:2] + size.to_bytes(2, "big") + bytes((size - 5,)) + packet[5:11]
    return clean_header + negotiation, token


async def copy_stream(reader, writer):
    while data := await reader.read(65536):
        writer.write(data)
        await writer.drain()


class Dispatcher:
    def __init__(self):
        self.routes = {}
        self.peers = 0
        self.greeter_busy = False

    async def issue(self, reader, writer):
        try:
            peer = writer.get_extra_info("socket")
            _, uid, _ = struct.unpack("3i", peer.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
            if uid != 0:
                return
            if not self.greeter_busy:
                return
            line = await asyncio.wait_for(reader.readline(), 2)
            if not line.endswith(b"\n") or not line.strip().isdigit():
                return
            port = int(line)
            if port not in SESSION_PORTS:
                return
            loop = asyncio.get_running_loop()
            now = loop.time()
            self.routes = {
                token: route for token, route in self.routes.items() if route[1] > now
            }
            if len(self.routes) >= MAX_ROUTES:
                return
            token = secrets.token_hex(TOKEN_LENGTH // 2).encode("ascii")
            self.routes[token] = (port, now + ROUTE_LIFETIME)
            logging.info("Issued one-time route to port %d", port)
            writer.write(TOKEN_PREFIX + token + b"\r\n")
            await asyncio.wait_for(writer.drain(), 2)
        except (OSError, ValueError, TimeoutError):
            pass
        finally:
            writer.close()

    async def client(self, reader, writer):
        if self.peers >= MAX_PEERS:
            writer.close()
            return
        self.peers += 1
        greeter = False
        upstream_writer = None
        tasks = []
        try:
            request, token = await asyncio.wait_for(read_request(reader), 3)
            port = GREETER_PORT
            if token is not None:
                route = self.routes.pop(token, None)
                if route is None or route[1] <= asyncio.get_running_loop().time():
                    logging.info("Rejected unknown or expired RDP routing token")
                    return
                port = route[0]
            else:
                if self.greeter_busy:
                    logging.info("Greeter already has an RDP client")
                    return
                self.greeter_busy = greeter = True
            logging.info("Opening RDP transport to internal port %d", port)
            async with asyncio.timeout(15):
                while True:
                    try:
                        upstream, upstream_writer = await asyncio.open_connection("127.0.0.1", port)
                        break
                    except ConnectionRefusedError:
                        await asyncio.sleep(0.25)
            upstream_writer.write(request)
            await upstream_writer.drain()
            tasks = [
                asyncio.create_task(copy_stream(reader, upstream_writer)),
                asyncio.create_task(copy_stream(upstream, writer)),
            ]
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        except (OSError, ValueError, TimeoutError, asyncio.IncompleteReadError) as error:
            logging.info("RDP stream closed: %s", error if isinstance(error, ValueError) else type(error).__name__)
        finally:
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            if upstream_writer is not None:
                upstream_writer.close()
            writer.close()
            if greeter:
                self.greeter_busy = False
            self.peers -= 1


async def main():
    dispatcher = Dispatcher()
    os.umask(0o077)
    control = await asyncio.start_unix_server(dispatcher.issue, CONTROL_PATH, limit=32)
    async with control:
        server = await asyncio.start_server(dispatcher.client, "127.0.0.1", PUBLIC_PORT)
        async with server:
            logging.warning("RDP dispatcher listening at 127.0.0.1:%d", PUBLIC_PORT)
            await server.serve_forever()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
