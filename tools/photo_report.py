# -*- coding: utf-8 -*-
"""Карта фото: какое исходное фото на какой странице сайта, в каком разрешении, откуда взято.
Результат: Отчёты/Карта фото сайта.html (открывается в браузере, превью встроены)."""
import json, os, re, io, base64, glob, html
from PIL import Image, ImageOps
import content as C

Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = 'C:/Users/Владос/OneDrive/Рабочий стол/Дамир сайт/'
OUT = os.path.join(os.path.dirname(ROOT), 'Отчёты', 'Карта фото сайта.html')
URL = 'https://goodrojh.github.io/adalight'
P = json.load(open(os.path.join(ROOT, 'data', 'products_raw.json'), encoding='utf-8'))
W = json.load(open(os.path.join(ROOT, 'data', 'products.json'), encoding='utf-8'))
WB = {p['slug']: p for p in W}
SHEET_COL = {1: 'колонка «Фото»', 2: 'колонка «Схема»', 0: 'колонка «Изображение»', 3: 'колонка «Фото»', 11: 'колонка «Изображение»'}


def describe(path):
    p = path.replace('\\', '/')
    m = re.search(r'xlimg/(.+?)__r(\d+)_c(\d+)_', p)
    if m:
        return ('Прайс 2026 ADALight — РРЦ.xls', f'лист «{m.group(1)}», строка {int(m.group(2)) + 1}, {SHEET_COL.get(int(m.group(3)), "колонка " + m.group(3))}')
    if '/_work/edits/' in p:
        rel = p.split('/_work/edits/')[1]
        arc = {'alpha': 'Alpha (1).rar', 'ravol': 'RAVOL.rar', 'ring': 'Ringo.rar'}[rel.split('/')[0]]
        names = {'ravol/1-black.jpg': 'черный.jpg', 'ravol/2-white.png': 'белый.png', 'ring/1-black.png': 'ч.png', 'ring/2-white.png': 'б.png'}
        inner = names.get(rel, rel.split('/', 1)[1])
        return ('Правки нового Сайта / ' + arc, 'файл в архиве: ' + inner)
    if p.startswith(SRC):
        rel = p[len(SRC):]
        return (os.path.dirname(rel), os.path.basename(rel))
    return (os.path.dirname(p), os.path.basename(p))


def thumb(path, size=150):
    try:
        im = Image.open(path)
        im.draft('RGB', (size * 2, size * 2))
        im = ImageOps.exif_transpose(im)
        if im.mode in ('P', 'LA', 'RGBA'):
            im = im.convert('RGBA'); bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg
        im = im.convert('RGB'); im.thumbnail((size, size))
        b = io.BytesIO(); im.save(b, 'JPEG', quality=72)
        return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()
    except Exception:
        return ''


def verdict(w, h):
    m = max(w, h)
    if m < 800:
        return 'low', 'Низкое — исходник маленький'
    if m < 1500:
        return 'mid', 'Среднее'
    return 'good', 'Хорошее'


RULES = [
    ('Встраиваемые / накладные ECO (TANGO, NANO, CUVY, DOTO, OCEAN, REVO, UKKIE, EMO, VEVO)', 'Папка «Фото для серии ECO …/‹СЕРИЯ›» + картинки из прайса (листы «Встраиваемые ECO», «Накладные ECO»). TENK — только 5 фото из «Правки нового Сайта/TENK».'),
    ('CLASS A (ADA-IB.xxxx)', 'Папка «Фото для серии A/ALDLxxxx» → серия CLASS A xxxx + картинки прайса (лист «Встраиваемые Class A»). Для 0789, 0792, 1519, 1521 — фото из Alpha (1).rar. Фото с логотипом поставщика ALPHALUCE у 1518 не используется.'),
    ('PRM (TUBE, TD, X, GRID, M15, M17, M1810, M1015)', 'Только картинки из прайса (листы «Встраиваемые PRM», «Накладные PRM»): фото и размерный чертёж из строки каждой модификации. Отдельных папок с фото PRM в материалах нет.'),
    ('SOFI', 'Только картинки из прайса (лист «Накладные SOFI»). Других фото SOFI в материалах нет.'),
    ('RAVOL, ADA RING', 'Фото из RAVOL.rar и Ringo.rar (правки 25.09).'),
    ('Линейные ADA-LINE', 'Папка «Фото для линейных»: 3535 → профиль 35×35, 5050 → 50×50, 4075 → 40×75, 4050 → IP54 40×50, 5080 → IP65 50×80 + картинки из прайса.'),
    ('Трековые светильники S20', 'Папка «S20 фото для сайта/1-…Lamps/‹артикул›»: HS26-12T → AL-TR.48.HS26-12T, HS-CX035 → AL-TR.48.HS26-CX035 и т.д.'),
    ('Шинопровод и комплектующие S20', 'Папка «S20 фото для сайта/2-…Track & Accessories/‹артикул›» + картинки прайса (лист «Шинопровод S20 48V»). RC智能遥控器 = пульт, 2.4G-Gateway = шлюз → серия «Шлюз и пульт Tuya ZigBee».'),
    ('Бра', 'Только картинки из прайса (лист «Бра»).'),
    ('Фото интерьеров S20 (сцены)', 'Папка «S20 фото для сайта/3-…scene picture» — фоны разделов каталога.'),
]


def main():
    cats = {k: v['short'] for k, v in C.CATEGORIES.items()}
    used = set()
    rows_html, n_all, n_low = [], 0, 0
    for cat in C.CAT_ORDER:
        ps = [p for p in P if p['category'] == cat]
        rows_html.append(f'<h2 id="{cat}">{html.escape(cats[cat])} <small>{len(ps)} серий</small></h2>')
        for p in ps:
            wp = WB[p['slug']]
            cards = []
            for kind, lst, wlist in (('Фото', p['images'], wp['images']), ('Чертёж', p['schemes'], wp['schemes'])):
                for i, src in enumerate(lst):
                    used.add(os.path.normcase(os.path.abspath(src)))
                    on_site = i < len(wlist)
                    try:
                        w, h = Image.open(src).size
                    except Exception:
                        w = h = 0
                    cls, vtxt = verdict(w, h)
                    n_all += 1; n_low += cls == 'low'
                    where, name = describe(src)
                    site = (f'{wlist[i]["w"]}×{wlist[i]["h"]}' + (' (уменьшено для скорости)' if wlist[i]['w'] < w else ' (как исходник)')) if on_site else 'не показывается (лимит 16 фото на серию)'
                    link = 'file:///' + os.path.abspath(src).replace('\\', '/') if not src.startswith(os.path.join(os.path.dirname(ROOT), '_work')) or '/_work/edits/' in src.replace('\\', '/') else ''
                    cards.append(f'<figure class="{cls}"><img src="{thumb(src)}" alt=""><figcaption><b>{kind} {i + 1}</b> · <span class="q">{vtxt}</span><br>'
                                 f'Исходник: {w}×{h}<br>На сайте: {site}<br><span class="src">{html.escape(where)}<br><i>{html.escape(name)}</i></span>'
                                 + (f'<br><a href="{link}">открыть исходный файл</a>' if link else '') + '</figcaption></figure>')
            vtxt = ', '.join(v['sku'] for v in p['variants'][:6]) + (' …' if len(p['variants']) > 6 else '')
            rows_html.append(f'<section class="ser"><h3>{html.escape(p["name"])} <a href="{URL}/product/{p["slug"]}/" target="_blank">страница на сайте ↗</a></h3>'
                             f'<p class="sku">{len(p["variants"])} арт.: {html.escape(vtxt)}</p><div class="grid">{"".join(cards)}</div></section>')
    # неиспользованные фото из материалов
    def eligible(f):
        g = f.replace(os.sep, '/')
        if not g.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) or '3-场景图' in g:
            return False
        if 'Правки нового Сайта' in g:
            return '/TENK/' in g
        return True
    all_src = [f for f in glob.glob(SRC + '**/*', recursive=True) if eligible(f)]
    unused = [f for f in all_src if os.path.normcase(os.path.abspath(f)) not in used]
    import hashlib
    usedh = {hashlib.md5(open(x, 'rb').read()).hexdigest() for p in P for x in p['images'] + p['schemes'] if os.path.exists(x)}

    def reason(f):
        g = f.replace(os.sep, '/')
        if hashlib.md5(open(f, 'rb').read()).hexdigest() in usedh:
            return 'Точная копия файла, который уже стоит на сайте'
        if re.search(r'HS26-(24|30|60)TP', g):
            return 'Wallwasher этого размера нет в прайсе (в прайсе только 6TP, 12TP, 18TP)'
        if 'GJ4000' in g:
            return 'Трубки 4 м (GJ4000) нет в прайсе (в прайсе GJ500–GJ3000)'
        if 'MB智能面板器' in g:
            return 'Панель управления MB — такого артикула нет в прайсе'
        if '/TENK/' in g and 'Правки' not in g:
            return 'Старое фото TENK — заменено новыми по ТЗ 25.09'
        if 'ALDL1518' in g:
            return 'На фото логотип поставщика ALPHALUCE'
        if re.search(r'ALDL(0789|0792|1519|1521)', g):
            return 'Заменено фото из Alpha (1).rar (правки 25.09)'
        return 'Не сопоставлено с артикулом'
    un_html = ''.join(f'<figure class="low"><img src="{thumb(f, 110)}" alt=""><figcaption><b>{html.escape(reason(f))}</b><br><span class="src">{html.escape(os.path.relpath(f, SRC))}</span></figcaption></figure>' for f in unused)
    rules = ''.join(f'<tr><td><b>{html.escape(a)}</b></td><td>{html.escape(b)}</td></tr>' for a, b in RULES)
    page = f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Карта фото сайта ADALIGHT</title>
<style>body{{font:14px/1.45 Segoe UI,Arial,sans-serif;margin:0;color:#141416;background:#f4f4f2}}header{{background:#0d0d0e;color:#fff;padding:28px 32px}}
header h1{{margin:0 0 6px;font-size:26px}}main{{padding:20px 32px 60px;max-width:1500px}}h2{{margin:36px 0 12px;font-size:22px;border-bottom:3px solid #ffc603;padding-bottom:6px}}
h2 small{{font-size:14px;color:#777;font-weight:400}}.ser{{background:#fff;border-radius:12px;padding:16px 18px;margin:12px 0}}.ser h3{{margin:0 0 4px}}.ser h3 a{{font-size:13px;font-weight:400;margin-left:8px}}
.sku{{margin:0 0 10px;color:#666;font-size:12.5px}}.grid{{display:flex;flex-wrap:wrap;gap:10px}}figure{{margin:0;width:230px;border:1px solid #e3e3df;border-radius:10px;overflow:hidden;background:#fff}}
figure img{{width:100%;height:150px;object-fit:contain;background:#f7f7f5;display:block}}figcaption{{padding:8px 10px;font-size:12px}}.src{{color:#666}}
figure.low{{border-color:#e8836f}}figure.low .q{{color:#c0392b;font-weight:600}}figure.mid .q{{color:#b7791f;font-weight:600}}figure.good .q{{color:#2f855a;font-weight:600}}
table{{border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden}}td{{padding:8px 12px;border-bottom:1px solid #eee;vertical-align:top}}nav a{{margin-right:14px}}.note{{background:#fff8dc;border-left:4px solid #ffc603;padding:12px 16px;border-radius:8px}}</style></head><body>
<header><h1>Карта фото сайта ADALIGHT</h1><div>Каждое фото на странице товара: откуда взято, размер исходника и размер на сайте. Всего фото: {n_all}, низкого качества: {n_low}.</div></header><main>
<p class="note"><b>Как читать.</b> Сайт <u>не ухудшает</u> фото: большие исходники уменьшаются до 1100 px по ширине (этого достаточно для экрана и ускоряет загрузку), маленькие показываются как есть и не растягиваются. Если в карточке написано «Низкое — исходник маленький», значит таким фото пришло в материалах (обычно это картинки, вставленные в прайс). Строка «Исходник» — где лежит файл: папка на рабочем столе «Дамир сайт» или лист/строка прайса.</p>
<nav>{"".join(f'<a href="#{c}">{html.escape(cats[c])}</a>' for c in C.CAT_ORDER)}<a href="#unused">Не использованы</a></nav>
<h2>Правила: откуда берутся фото каждой серии</h2><table>{rules}</table>
{"".join(rows_html)}
<h2 id="unused">Фото из материалов, которые не попали на сайт <small>{len(unused)} шт.</small></h2>
<p>У каждого файла указана причина.</p><div class="grid">{un_html}</div>
</main></body></html>'''
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w', encoding='utf-8').write(page)
    print('photos', n_all, 'low', n_low, 'unused', len(unused), 'size MB', round(os.path.getsize(OUT) / 1e6, 1))


if __name__ == '__main__':
    main()
