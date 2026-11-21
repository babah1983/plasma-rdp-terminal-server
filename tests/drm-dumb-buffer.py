#!/usr/bin/env python3
"""Linux headless-renderer probe; allocates a small buffer, releases it on close.

Run as the actual remote-session user, with the DRM node selected by KWin.
Opening a render node successfully does not imply CREATE_DUMB is supported.
"""
import fcntl
import os
import struct
import sys

device = sys.argv[1]
try:
    fd = os.open(device, os.O_RDWR | os.O_CLOEXEC)
    try:
        # struct drm_mode_create_dumb: height, width, bpp, flags, handle,
        # pitch, size. DRM_IOCTL_MODE_CREATE_DUMB = DRM_IOWR(0xb2, struct).
        request = bytearray(struct.pack('=IIIIIIQ', 240, 320, 32, 0, 0, 0, 0))
        fcntl.ioctl(fd, 0xc02064b2, request, True)
        *_, pitch, size = struct.unpack('=IIIIIIQ', request)
        print(f'{device}: CREATE_DUMB OK, pitch={pitch}, size={size}')
    finally:
        os.close(fd)
except OSError as exc:
    print(f'{device}: CREATE_DUMB FAILED, errno={exc.errno}: {exc.strerror}')
    sys.exit(1)
