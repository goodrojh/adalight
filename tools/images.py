# -*- coding: utf-8 -*-
"""Оптимизация изображений: товары, проекты, сцены -> WebP (2 размера).
Пишет data/products.json (с веб-путями) и data/media.json."""
import json, os, sys
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs')
WORK = os.path.join(os.path.dirname(ROOT), '_work')
SRC = 'C:/Users/Владос/OneDrive/Рабочий стол/Дамир сайт/'
Image.MAX_IMAGE_PIXELS = None
MAX_PER_PRODUCT = 16


def job(args):
    src, dst_base, sizes, quality, crop = args
    res = []
    try:
        im = Image.open(src)
        im.draft('RGB', (max(sizes) * 2, max(sizes) * 2))
        im = ImageOps.exif_transpose(im)
        if im.mode in ('P', 'LA', 'RGBA'):
            im = im.convert('RGBA')
            bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
            bg.alpha_composite(im)
            im = bg
        im = im.convert('RGB')
        if crop:  # crop to aspect (w/h)
            w, h = im.size
            tr = crop
            if w / h > tr:
                nw = int(h * tr); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
            else:
                nh = int(w / tr); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
        w, h = im.size
        done = set()
        for sz in sizes:
            tw = min(sz, w)
            if tw in done:
                continue
            done.add(tw)
            r = im if tw == w else im.resize((tw, round(h * tw / w)), Image.LANCZOS)
            p = f'{dst_base}-{sz}.webp'
            os.makedirs(os.path.dirname(p), exist_ok=True)
            r.save(p, 'WEBP', quality=quality, method=6)
            res.append((sz, tw, r.size[1]))
        return src, res, (w, h)
    except Exception as e:
        return src, [], str(e)


def rel(p):
    return '/' + os.path.relpath(p, OUT).replace('\\', '/')


def main():
    products = json.load(open(os.path.join(ROOT, 'data', 'products_raw.json'), encoding='utf-8'))
    jobs, mapping = [], {}
    for p in products:
        for kind in ('images', 'schemes'):
            for i, src in enumerate(p[kind][:MAX_PER_PRODUCT]):
                base = os.path.join(OUT, 'img', 'p', f"{p['slug']}-{'s' if kind == 'schemes' else ''}{i + 1}")
                jobs.append((src, base, (480, 1100), 80, None))
                mapping[(p['slug'], kind, i)] = base
    # проекты и сцены
    media = json.load(open(os.path.join(ROOT, 'data', 'media_src.json'), encoding='utf-8'))
    for key, item in media.items():
        base = os.path.join(OUT, 'img', item['dir'], key)
        jobs.append((item['src'], base, tuple(item.get('sizes', (800, 1600))), item.get('q', 78), item.get('crop')))
        mapping[('media', key)] = base
    print('jobs', len(jobs), flush=True)
    results = {}
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
        for n, (src, res, info) in enumerate(ex.map(job, jobs, chunksize=2)):
            results[src] = (res, info)
            if n % 50 == 0:
                print(n, flush=True)
    bad = [s for s, (r, i) in results.items() if not r]
    print('failed:', bad)

    def entry(base, src):
        res, info = results[src]
        if not res:
            return None
        return {'src': rel(base + f'-{res[0][0]}.webp'), 'srcset': ', '.join(f"{rel(base + f'-{sz}.webp')} {tw}w" for sz, tw, th in res),
                'w': res[-1][1], 'h': res[-1][2], 'lg': rel(base + f'-{res[-1][0]}.webp'),
                'ow': info[0], 'oh': info[1], 'orig': src}

    for p in products:
        for kind in ('images', 'schemes'):
            out = []
            for i, src in enumerate(p[kind][:MAX_PER_PRODUCT]):
                e = entry(mapping[(p['slug'], kind, i)], src)
                if e:
                    out.append(e)
            p[kind] = out
    json.dump(products, open(os.path.join(ROOT, 'data', 'products.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    mout = {}
    for key, item in media.items():
        e = entry(mapping[('media', key)], item['src'])
        if e:
            mout[key] = e
    json.dump(mout, open(os.path.join(ROOT, 'data', 'media.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
