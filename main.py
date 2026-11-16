#!/usr/bin/env python3
"""Draw one image designed to excite an AI judge.

Entry for the make.fun bounty "Make the AI judge excited"
(https://make.fun/bounty/ai-excited-01).

Python 3.13, standard library only. No arguments, no network, no model
calls, no file reads: the picture is generated from fixed constants and a
seeded generator, so every run writes the exact same PNG to
/output/entry.png (creating /output if needed).

The scene: a whale breaching out of a sunset sea, between two mountain
ridges, under early stars - a single striking, wall-worthy image.
"""

import math
import os
import struct
import zlib

W, H = 1024, 768
HORIZON = 470  # where the sea starts

# Deterministic pseudo-random numbers (fixed seed, no `random` module).
_state = 20261116


def rnd():
    global _state
    _state = (_state * 1103515245 + 12345) & 0x7FFFFFFF
    return _state / 0x7FFFFFFF


buf = bytearray(W * H * 3)


def put(x, y, r, g, b):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = r
        buf[i + 1] = g
        buf[i + 2] = b


def blend(x, y, r, g, b, a):
    if 0 <= x < W and 0 <= y < H and 0.0 < a <= 1.0:
        i = (y * W + x) * 3
        buf[i] = int(buf[i] * (1.0 - a) + r * a)
        buf[i + 1] = int(buf[i + 1] * (1.0 - a) + g * a)
        buf[i + 2] = int(buf[i + 2] * (1.0 - a) + b * a)


def lerp(a, b, t):
    return a + (b - a) * t


def disc(cx, cy, rad, col, a=1.0):
    for y in range(max(0, int(cy - rad)), min(H, int(cy + rad) + 1)):
        for x in range(max(0, int(cx - rad)), min(W, int(cx + rad) + 1)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= rad * rad:
                if a >= 1.0:
                    put(x, y, *col)
                else:
                    blend(x, y, *col, a)


def line(x1, y1, x2, y2, col):
    n = int(max(abs(x2 - x1), abs(y2 - y1))) + 1
    for k in range(n + 1):
        t = k / n
        put(int(x1 + (x2 - x1) * t), int(y1 + (y2 - y1) * t), *col)


def fill_poly(pts, col, a=1.0):
    ys = [p[1] for p in pts]
    for y in range(max(0, int(min(ys))), min(H, int(max(ys)) + 1)):
        xs = []
        n = len(pts)
        for k in range(n):
            x1, y1 = pts[k]
            x2, y2 = pts[(k + 1) % n]
            if (y1 <= y < y2) or (y2 <= y < y1):
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            for x in range(max(0, int(xs[k])), min(W, int(xs[k + 1]) + 1)):
                if a >= 1.0:
                    put(x, y, *col)
                else:
                    blend(x, y, *col, a)


def ellipse(cx, cy, rx, ry, angle_deg, col, a=1.0):
    th = math.radians(angle_deg)
    co, si = math.cos(th), math.sin(th)
    r = int(max(rx, ry)) + 2
    for y in range(max(0, int(cy - r)), min(H, int(cy + r) + 1)):
        for x in range(max(0, int(cx - r)), min(W, int(cx + r) + 1)):
            dx, dy = x - cx, y - cy
            u = dx * co + dy * si
            v = -dx * si + dy * co
            if (u / rx) ** 2 + (v / ry) ** 2 <= 1.0:
                if a >= 1.0:
                    put(x, y, *col)
                else:
                    blend(x, y, *col, a)


def ridge(x, base, amps):
    y = base
    for amp, freq, phase in amps:
        y += amp * math.sin(x * freq + phase)
    return y


# ---- sky: deep indigo at the top, warm coral at the horizon ----
for y in range(HORIZON):
    t = y / HORIZON
    if t < 0.55:
        s = t / 0.55
        col = (int(lerp(24, 122, s)), int(lerp(14, 54, s)), int(lerp(66, 132, s)))
    else:
        s = (t - 0.55) / 0.45
        col = (int(lerp(122, 255, s)), int(lerp(54, 128, s)), int(lerp(132, 92, s)))
    for x in range(W):
        put(x, y, *col)

# ---- stars in the upper sky ----
for _ in range(240):
    sx = int(rnd() * W)
    sy = int(rnd() * HORIZON * 0.55)
    bright = 0.35 + rnd() * 0.65
    rad = 1 if rnd() < 0.8 else 2
    disc(sx, sy, rad, (255, 246, 230), bright)

# ---- sun and its glow ----
for rad, a in ((150, 0.05), (110, 0.09), (75, 0.15), (52, 0.22)):
    disc(700, 402, rad, (255, 150, 80), a)
disc(700, 402, 46, (255, 216, 132))
disc(700, 402, 34, (255, 236, 180))

# ---- mountain ridges ----
for x in range(W):
    y0 = ridge(x, HORIZON - 62, ((40, 0.008, 1.7), (18, 0.021, 0.4)))
    for y in range(int(y0), HORIZON):
        put(x, y, 58, 32, 86)
for x in range(W):
    y0 = ridge(x, HORIZON - 18, ((26, 0.011, 4.0), (12, 0.03, 1.2)))
    for y in range(int(y0), HORIZON):
        put(x, y, 34, 18, 58)

# ---- sea: sunset colours at the top, deep water below ----
for y in range(HORIZON, H):
    t = (y - HORIZON) / (H - HORIZON)
    col = (int(lerp(196, 20, t)), int(lerp(84, 12, t)), int(lerp(94, 44, t)))
    for x in range(W):
        put(x, y, *col)

# ---- sun reflection on the water ----
for y in range(HORIZON, H):
    t = (y - HORIZON) / (H - HORIZON)
    w = 26 + int(90 * t)
    for x in range(700 - w, 700 + w + 1):
        a = 0.30 * (1.0 - t) * (0.5 + 0.5 * math.sin(x * 0.35 + y * 0.6))
        blend(x, y, 255, 170, 100, a)

# ---- whale reflection ----
ellipse(430, 560, 200, 42, 18, (52, 36, 88), 0.35)

# ---- breaching whale (dark navy silhouette) ----
ellipse(430, 380, 210, 78, -18, (18, 22, 52))
ellipse(610, 336, 62, 26, -18, (18, 22, 52))  # tail stalk
fill_poly([(648, 330), (732, 284), (706, 332)], (18, 22, 52))  # upper fluke
fill_poly([(648, 336), (726, 376), (700, 342)], (18, 22, 52))  # lower fluke
ellipse(430, 398, 186, 56, -18, (96, 84, 128), 0.35)  # belly sheen
disc(288, 392, 5, (255, 240, 220))  # eye
# spout above the blowhole
disc(322, 316, 4, (255, 230, 210), 0.85)
disc(310, 300, 3, (255, 230, 210), 0.8)
disc(332, 298, 3, (255, 230, 210), 0.8)
disc(320, 282, 2, (255, 230, 210), 0.7)

# ---- birds ----
for bx, by in ((150, 150), (210, 120), (262, 172), (822, 142), (882, 182), (762, 202), (120, 222)):
    line(bx, by, bx - 10, by - 7, (30, 20, 50))
    line(bx, by, bx + 10, by - 7, (30, 20, 50))

# ---- wave streaks ----
for k in range(42):
    y = HORIZON + 8 + k * 7
    for x in range(W):
        if math.sin(x * 0.02 + k * 1.3) > 0.86:
            blend(x, y, 255, 190, 150, 0.22)


# ---- PNG writer (standard library only) ----
def _chunk(tag, data):
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def write_png(path):
    raw = b"".join(b"\x00" + bytes(buf[y * W * 3:(y + 1) * W * 3]) for y in range(H))
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    data = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(raw, 9))
        + _chunk(b"IEND", b"")
    )
    with open(path, "wb") as f:
        f.write(data)


def main():
    os.makedirs("/output", exist_ok=True)
    write_png("/output/entry.png")


if __name__ == "__main__":
    main()
