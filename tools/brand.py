# -*- coding: utf-8 -*-
"""Favicon, иконки PWA и OG-изображения из оригинального SVG-логотипа."""
import io, os, json
import resvg_py
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, 'docs', 'assets')
W = os.path.join(os.path.dirname(ROOT), '_work')


def svg(path, width):
    return Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_path=path, width=width)))).convert('RGBA')


# знак «A с лучами» — вырезаем из логотипа (левая часть mark.svg)
mark = svg(os.path.join(A, 'logo-mark.svg'), 1200)
bbox = mark.getbbox()
a = mark.crop((bbox[0], bbox[1], bbox[0] + int(mark.width * 0.36), bbox[3]))
a = a.crop(a.getbbox())


def icon(size, pad=0.16, radius=0.22):
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=int(size * radius), fill=(13, 13, 14, 255))
    s = a.copy()
    s.thumbnail((int(size * (1 - 2 * pad)), int(size * (1 - 2 * pad))), Image.LANCZOS)
    im.alpha_composite(s, ((size - s.width) // 2, (size - s.height) // 2))
    return im


icon(32, .12).save(os.path.join(A, 'favicon-32.png'))
icon(180, .16, .0).convert('RGB').save(os.path.join(A, 'apple-touch-icon.png'))
icon(192).save(os.path.join(A, 'icon-192.png'))
icon(512).save(os.path.join(A, 'icon-512.png'))
icon(48, .12).save(os.path.join(os.path.dirname(A), 'favicon.ico'), sizes=[(48, 48), (32, 32), (16, 16)])
# svg favicon: тёмная плашка + знак (png внутри, чтобы не зависеть от путей)
import base64
buf = io.BytesIO(); icon(64, .12).save(buf, 'PNG')
open(os.path.join(A, 'favicon.svg'), 'w').write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><image width="64" height="64" href="data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode() + '"/></svg>')

dark_logo = svg(os.path.join(A, 'logo-dark.svg'), 600)
bg = Image.new('RGBA', dark_logo.size, (255, 255, 255, 255)); bg.alpha_composite(dark_logo); bg.convert('RGB').save(os.path.join(A, 'logo-dark.png'))


def og(photo, out, title):
    im = Image.open(photo).convert('RGB')
    w, h = im.size; tr = 1200 / 630
    if w / h > tr:
        nw = int(h * tr); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / tr); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    im = im.resize((1200, 630), Image.LANCZOS)
    im = ImageEnhance.Brightness(im).enhance(0.55).convert('RGBA')
    grad = Image.new('L', (1200, 630))
    gd = ImageDraw.Draw(grad)
    for x in range(1200):
        gd.line([(x, 0), (x, 630)], fill=int(220 * max(0, 1 - x / 900)))
    black = Image.new('RGBA', (1200, 630), (13, 13, 14, 255)); im = Image.composite(black, im, grad)
    lg = svg(os.path.join(A, 'logo-light.svg'), 460)
    im.alpha_composite(lg, (70, 70))
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 52)
        f2 = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 28)
    except Exception:
        f = f2 = None
    y = 330
    for line in title[0]:
        d.text((72, y), line, font=f, fill=(255, 255, 255)); y += 62
    d.rectangle((72, y + 18, 120, y + 22), fill=(255, 198, 3))
    d.text((72, y + 40), title[1], font=f2, fill=(200, 200, 205))
    im.convert('RGB').save(out, quality=86)


from PIL import ImageFont
og(os.path.join(W, 'siteimg', sorted(os.listdir(os.path.join(W, 'siteimg')))[6]), os.path.join(A, 'og.jpg'),
   (['Проектируем, поставляем', 'и монтируем свет'], 'Расчёт · производство по ТЗ · поставка · adalight.ru'))
og(os.path.join(W, 'pdfimg', '1_p1_1_1672x940.jpeg'), os.path.join(A, 'og-partners.jpg'),
   (['Партнёрская программа:', 'свет, который приносит прибыль'], 'Для дизайн-студий, ремонтных компаний и архитекторов'))
print('ok')
