# -*- coding: utf-8 -*-
"""Логотипы девелоперов: вырезаем из фона, делаем монохромные версии (белая — для тёмного фона)."""
import os
from PIL import Image, ImageFilter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(os.path.dirname(ROOT), '_work', 'siteimg')
fs = sorted(os.listdir(W))
SRC = {'samolet': 13, 'etalon': 82, 'sminex': 40, 'mr': 9, 'green': 71}
OUT = os.path.join(ROOT, 'docs', 'img', 'logos')
os.makedirs(OUT, exist_ok=True)
for key, idx in SRC.items():
    im = Image.open(os.path.join(W, fs[idx])).convert('RGB')
    w, h = im.size
    px = im.load()
    border = [px[x, 0] for x in range(w)] + [px[x, h - 1] for x in range(w)] + [px[0, y] for y in range(h)] + [px[w - 1, y] for y in range(h)]
    bg = tuple(sorted(c[i] for c in border)[len(border) // 2] for i in range(3))
    mask = Image.new('L', (w, h))
    mp = mask.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            d = ((r - bg[0]) ** 2 + (g - bg[1]) ** 2 + (b - bg[2]) ** 2) ** .5
            mp[x, y] = max(0, min(255, int((d - 25) * 4)))
    if key == 'green':  # ромб: берём только белое
        for y in range(h):
            for x in range(w):
                r, g, b = px[x, y]
                mp[x, y] = 255 if min(r, g, b) > 170 else 0
        mask = mask.filter(ImageFilter.SMOOTH)
    bb = mask.getbbox()
    mask = mask.crop(bb)
    for name, col in (('w', (255, 255, 255)), ('d', (20, 20, 22))):
        o = Image.new('RGBA', mask.size, col + (0,))
        o.putalpha(mask)
        o.thumbnail((520, 150), Image.LANCZOS)
        o.save(os.path.join(OUT, f'{key}-{name}.webp'), 'WEBP', quality=90)
    print(key, bg, mask.size)
