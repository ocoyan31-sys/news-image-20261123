#!/usr/bin/env python3
"""THE WORLD TODAY - Monday 23 November 2026 in one image.

Renders a 1024x1024 newspaper front page of the day's world news as a PNG,
using only the Python standard library. Deterministic: the same bytes are
written on every run. Output: entry.png in $MAKEFUN_OUTPUT_DIR or /output.
"""

import os
import struct
import zlib
from math import isqrt

W = 1024
H = 1024

PAPER = (247, 243, 233)
INK = (22, 19, 14)
RED = (176, 32, 30)
GREEN = (18, 118, 58)
BLUE = (28, 66, 138)
GREY = (112, 106, 94)
WHITE = (252, 250, 244)

# ---------------------------------------------------------------- font ------
# 5x7 bitmap glyphs, rows top to bottom, '#' = ink.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": (".####", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "2": (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "'": (".##..", ".##..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#...", "#.##."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "..##.", "..#..", ".....", "..#.."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": (".##..", "..#..", "...#.", "...#.", "...#.", "..#..", ".##.."),
    "·": (".....", ".....", ".....", ".##..", ".##..", ".....", "....."),
}


# -------------------------------------------------------------- canvas ------
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def frame(self, x, y, w, h, color, t=2):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            for ox in range(t):
                for oy in range(t):
                    self.set(x0 + ox, y0 + oy, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = isqrt(r * r - dy * dy)
            for xx in range(cx - dx, cx + dx + 1):
                self.set(xx, cy + dy, color)

    def ring(self, cx, cy, r, color, t=2):
        for dy in range(-r, r + 1):
            dx = isqrt(r * r - dy * dy)
            for xx in (cx - dx, cx + dx):
                for o in range(t):
                    self.set(xx, cy + dy, color)
                    self.set(xx - o if xx < cx else xx + o, cy + dy, color)
        for dx in range(-r, r + 1):
            dy = isqrt(r * r - dx * dx)
            for yy in (cy - dy, cy + dy):
                for o in range(t):
                    self.set(cx + dx, yy, color)

    def png_bytes(self):
        raw = bytearray()
        stride = self.w * 3
        for y in range(self.h):
            raw.append(0)
            raw += self.px[y * stride:(y + 1) * stride]

        def chunk(tag, data):
            c = struct.pack(">I", len(data)) + tag + data
            c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            return c

        ihdr = struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
                + chunk(b"IEND", b""))


# ---------------------------------------------------------------- text ------
def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, s, scale, color):
    for ch in s.upper():
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            for col in range(5):
                if glyph[row][col] == "#":
                    cv.rect(x + col * scale, y + row * scale, scale, scale, color)
        x += 6 * scale
    return x


def draw_centered(cv, cx, y, s, scale, color):
    return draw_text(cv, cx - text_w(s, scale) // 2, y, s, scale, color)


def wrap(s, max_chars):
    lines = []
    cur = ""
    for word in s.split():
        trial = word if not cur else cur + " " + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_body(cv, x, y, s, scale, color, max_chars, line_h):
    for ln in wrap(s, max_chars):
        draw_text(cv, x, y, ln, scale, color)
        y += line_h
    return y


# --------------------------------------------------------------- icons ------
def icon_ship(cv, x, y, color):
    # warship: hull, deck house, mast, waves
    cv.rect(x + 2, y + 26, 40, 7, color)
    cv.line(x + 2, y + 26, x + 8, y + 33, color, 2)
    cv.line(x + 42, y + 26, x + 36, y + 33, color, 2)
    cv.rect(x + 15, y + 18, 13, 8, color)
    cv.line(x + 10, y + 6, x + 10, y + 26, color, 2)
    cv.line(x + 10, y + 6, x + 20, y + 6, color, 2)
    cv.line(x + 4, y + 40, x + 14, y + 40, color, 2)
    cv.line(x + 18, y + 40, x + 30, y + 40, color, 2)
    cv.line(x + 32, y + 40, x + 42, y + 40, color, 2)


def icon_plane(cv, x, y, color):
    # AWACS in side view: fuselage, tail fin, wing, radar dome
    cv.rect(x + 2, y + 22, 38, 5, color)
    cv.line(x + 40, y + 22, x + 45, y + 24, color, 2)
    cv.line(x + 3, y + 22, x + 9, y + 11, color, 3)
    cv.rect(x + 2, y + 11, 4, 4, color)
    for i in range(9):
        cv.line(x + 21 + i, y + 27, x + 27 + i, y + 37, color, 1)
    cv.rect(x + 23, y + 17, 3, 5, color)
    cv.disc(x + 24, y + 13, 6, color)


def icon_globe(cv, x, y, color):
    # globe split by a jagged crack
    cv.ring(x + 21, y + 21, 18, color, 2)
    cv.line(x + 3, y + 21, x + 39, y + 21, color, 1)
    pts = [(21, 3), (18, 12), (24, 20), (17, 29), (21, 39)]
    for i in range(len(pts) - 1):
        cv.line(x + pts[i][0], y + pts[i][1],
                x + pts[i + 1][0], y + pts[i + 1][1], RED, 2)


def icon_drop(cv, x, y, color):
    # oil drop
    cv.disc(x + 21, y + 28, 11, BLUE)
    for i in range(12):
        wdt = 11 - i
        cv.rect(x + 21 - wdt // 2, y + 6 + i, wdt, 1, BLUE)


# -------------------------------------------------------------- layout ------
MX = 36            # page margin
RIGHT = W - MX     # 988


def story(cv, x, y, w, kicker, headline, body, icon=None):
    if icon:
        icon(cv, x + w - 46, y - 2, INK)
    draw_text(cv, x, y, kicker, 2, RED)
    y += 24
    lines = headline if isinstance(headline, list) else wrap(headline, w // 24)
    for ln in lines:
        draw_text(cv, x, y, ln, 4, INK)
        y += 36
    y += 6
    draw_body(cv, x, y, body, 2, INK, w // 12, 20)


def build():
    cv = Canvas(W, H, PAPER)

    # masthead
    cv.rect(MX, 24, RIGHT - MX, 3, INK)
    cv.rect(MX, 32, RIGHT - MX, 1, INK)
    draw_centered(cv, W // 2, 42, "THE WORLD TODAY", 10, INK)
    draw_text(cv, MX, 124, "THE DAY IN ONE IMAGE", 2, GREY)
    draw_centered(cv, W // 2, 120, "MONDAY, 23 NOVEMBER 2026", 3, RED)
    draw_text(cv, RIGHT - text_w("GLOBAL EDITION", 2), 124,
              "GLOBAL EDITION", 2, GREY)
    cv.rect(MX, 150, RIGHT - MX, 6, INK)
    cv.rect(MX, 160, RIGHT - MX, 2, INK)

    # lead: Nvidia / Huang
    ly = 176
    draw_text(cv, MX, ly, "SILICON VALLEY · MARKETS", 3, RED)
    draw_text(cv, MX, ly + 34, "HUANG RETURNS,", 6, INK)
    draw_text(cv, MX, ly + 86, "NVIDIA LEAPS 31%", 6, INK)
    draw_body(cv, MX, ly + 144,
              "THE BOARD REINSTATED JENSEN HUANG AS CHIEF EXECUTIVE 11 DAYS "
              "AFTER HE QUIT IN SCANDAL, AFTER TRUMP ASSURED THE CHIPMAKER "
              "ITS FOUNDER WAS NO SECURITY THREAT. SHARES LEAPT 31%, THE "
              "NASDAQ JUMPED 6.5% AND THE S&P 500 ROSE 4.7%, ENDING THE "
              "AI SELL-OFF ROUT.",
              2, INK, 50, 21)

    # lead chart panel
    px, pw = 664, RIGHT - 664
    cv.frame(px, ly, pw, 252, INK, 2)
    draw_text(cv, px + 18, ly + 14, "THE REBOUND", 2, RED)
    pts = [(px + 22, ly + 128), (px + 70, ly + 140), (px + 118, ly + 118),
           (px + 160, ly + 132), (px + 205, ly + 84), (px + 252, ly + 52),
           (px + 296, ly + 30)]
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], GREEN, 4)
    cv.line(pts[-1][0], pts[-1][1], pts[-1][0] - 16, pts[-1][1] + 2, GREEN, 4)
    cv.line(pts[-1][0], pts[-1][1], pts[-1][0] - 4, pts[-1][1] + 15, GREEN, 4)
    cv.line(px + 22, ly + 152, px + pw - 22, ly + 152, GREY, 1)
    draw_text(cv, px + 18, ly + 164, "NASDAQ +6.5%", 3, GREEN)
    draw_text(cv, px + 18, ly + 200, "S&P 500 +4.7%", 3, GREEN)

    cv.rect(MX, 444, RIGHT - MX, 2, INK)

    # row 1
    ry = 458
    story(cv, MX, ry, 462, "LIBYA · THE MEDITERRANEAN",
          ["UKRAINE SINKS", "WARSHIP IN LIBYA"],
          "SEA DRONES SANK A RUSSIAN CORVETTE IN BENGHAZI PORT, PRESIDENT "
          "ZELENSKY CONFIRMED. A SECOND RUSSIAN SHIP BURNED IN THE BALTIC "
          "AFTER A DRONE STRIKE; MOSCOW WARNED OF ESCALATION.",
          icon_ship)
    cv.rect(512, ry, 1, 190, GREY)
    story(cv, 526, ry, 462, "POLAND · NATO",
          ["NATO SENDS AWACS", "TO POLAND"],
          "THREE RUSSIAN KH-101 MISSILES LANDED ON POLISH SOIL ON FRIDAY, "
          "PROSECUTORS SAID. THE ALLIANCE WILL DEPLOY AN AWACS "
          "EARLY-WARNING PLANE TO GUARD ITS EASTERN FLANK, WARSAW SAID.",
          icon_plane)
    cv.rect(MX, 664, RIGHT - MX, 2, INK)

    # row 2
    ry = 678
    story(cv, MX, ry, 462, "CLIMATE · ANTALYA, TURKEY",
          ["COP31 TALKS FAIL:", "BLAME AND DESPAIR"],
          "THE LONGEST UN CLIMATE TALKS EVER ENDED WITH NO DEAL ON FOSSIL "
          "FUELS. PACIFIC NATIONS SPOKE OF DESPAIR; THE AUSTRALIAN "
          "MINISTER FACED CALLS TO QUIT.",
          icon_globe)
    cv.rect(512, ry, 1, 184, GREY)
    story(cv, 526, ry, 462, "IRAN · STRAIT OF HORMUZ",
          ["IRAN VOWS TO DEFY", "US NAVAL BLOCKADE"],
          "TEHRAN SAID IT WOULD USE ALL ITS TOOLS AGAINST THE US BLOCKADE, "
          "AS WASHINGTON SANCTIONED DOZENS TIED TO IRAN'S SHADOW-BANKING "
          "NETWORKS.",
          icon_drop)
    cv.rect(MX, 882, RIGHT - MX, 2, INK)

    # Indonesia band
    cv.rect(MX, 894, RIGHT - MX, 40, RED)
    draw_centered(cv, W // 2, 904,
                  "INDONESIA FIRE TOLL: 24 DEAD, 30 MISSING", 3, WHITE)

    # bottom strip: four more of the day's stories
    strip = [
        ("EU UNVEILS 22ND", "RUSSIA SANCTIONS"),
        ("DRONES HIT UN", "BUILDING, KHARTOUM"),
        ("RUSSIAN STRIKES", "KILL 15 NEAR KYIV"),
        ("AI 'PROVES' THE", "RIEMANN HYPOTHESIS"),
    ]
    sx = MX
    for line1, line2 in strip:
        cv.rect(sx, 956, 8, 8, RED)
        draw_text(cv, sx + 14, 952, line1, 2, INK)
        draw_text(cv, sx + 14, 974, line2, 2, INK)
        sx += 240

    return cv.png_bytes()


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = build()
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)
    print("wrote entry.png:", len(data), "bytes")


if __name__ == "__main__":
    main()
