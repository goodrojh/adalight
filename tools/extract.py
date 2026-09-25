# -*- coding: utf-8 -*-
"""Парсит прайс ADALIGHT 2026 (xls) + папки с фото -> data/products.json
Каждый товар = серия (страница), внутри — артикулы-варианты."""
import json, os, re, glob, hashlib
import xlrd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = 'C:/Users/Владос/OneDrive/Рабочий стол/Дамир сайт/'
PRICE = SRC + 'Владиславу для Сайта/Прайс 2026 ADALight — РРЦ.xls'
XLIMG = os.path.join(os.path.dirname(ROOT), '_work', 'xlimg')
ECO_DIR = SRC + 'Владиславу для Сайта/Фото для серии ECO _TANGO  EMO  NANO  Cuvey  Doto  Ocean  Revo  Tenk  Vevo  Ukkie/'
A_DIR = SRC + 'Фото для серии A/'
LIN_DIR = SRC + 'Фото для линейных/Фото для линейных/'
S20_LAMPS = SRC + 'Владиславу для Сайта/S20 фото для сайта/1-产品高清图-灯具（Product Pictures Lamps）/'
S20_TRACK = SRC + 'Владиславу для Сайта/S20 фото для сайта/2-产品高清图-轨道及配件（Product pictures Track & Accessories）/'

IMG_EXT = ('.png', '.jpg', '.jpeg', '.webp')
# Правки 25.09.2026: новые фото (TENK — из папки правок, остальное — из архивов Alpha/RAVOL/Ringo)
EDITS = SRC + 'Правки нового Сайта/Правки нового Сайта/'
EDITS_WORK = os.path.join(os.path.dirname(ROOT), '_work', 'edits')
# фото с логотипами поставщика — не показываем на сайте
EXCLUDE = ('ALDL1518' + os.sep + 'Image_2026-09-18_101159_378', 'ALDL1518/Image_2026-09-18_101159_378')

wb = xlrd.open_workbook(PRICE)


def sheet(name):
    return wb.sheet_by_name(name)


def s(v):
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return ('%.2f' % v).rstrip('0').rstrip('.')
    return re.sub(r'\s+', ' ', str(v)).strip()


def price(v):
    try:
        return int(round(float(v)))
    except Exception:
        return None


def xl_images(sheet_name, row, col=None):
    out = []
    for f in sorted(os.listdir(XLIMG)):
        m = re.match(r'(.+)__r(\d+)_c(\d+)_\d+\.', f)
        if not m or m.group(1) != sheet_name or int(m.group(2)) != row:
            continue
        if col is not None and int(m.group(3)) != col:
            continue
        out.append(os.path.join(XLIMG, f))
    return out


def folder_images(path):
    if not os.path.isdir(path):
        return []
    fs = [os.path.join(path, f) for f in sorted(os.listdir(path)) if f.lower().endswith(IMG_EXT)]
    return fs


def dedupe(paths):
    seen, out = set(), []
    for p in paths:
        h = hashlib.md5(open(p, 'rb').read()).hexdigest()
        if h not in seen:
            seen.add(h)
            out.append(p)
    return out


def norm_cct(t):
    t = s(t).replace('30004000', '3000, 4000')
    nums = sorted(set(int(x) for x in re.findall(r'(2700|3000|4000|5700|6000|6500)', t)))
    return nums


def norm_ip(t):
    t = s(t)
    nums = [int(x) for x in re.findall(r'\d+', t)]
    return nums


def watt(t):
    t = s(t).lower().replace('вт', 'w')
    m = re.findall(r'(\d+)\s*x\s*(\d+)', t)
    if m:
        return int(m[-1][0]) * int(m[-1][1])
    n = re.findall(r'\d+(?:\.\d+)?', t)
    return float(n[-1]) if n else None


def beams(t):
    return sorted(set(int(x) for x in re.findall(r'(\d+)\s*°?', s(t).replace('°', ' ')) if int(x) <= 360))


products = []


def md5(pth):
    return hashlib.md5(open(pth, 'rb').read()).hexdigest()


def add(p):
    p.setdefault('images', [])
    p.setdefault('schemes', [])
    p['images'] = dedupe([i for i in p['images'] if os.path.exists(i) and not any(x in i for x in EXCLUDE)])
    p['schemes'] = dedupe([i for i in p['schemes'] if os.path.exists(i)])
    # фото конкретной модификации: индекс в общей галерее (для смены фото при выборе модификации)
    idx = {md5(x): n for n, x in enumerate(p['images'])}
    sidx = {md5(x): n for n, x in enumerate(p['schemes'])}
    for v in p['variants']:
        src = v.pop('_img', None)
        v['img_i'] = idx.get(md5(src)) if src and os.path.exists(src) else None
        sch = v.pop('_sch', None)
        v['sch_i'] = sidx.get(md5(sch)) if sch and os.path.exists(sch) else None
    products.append(p)
    return p


# ---------------------------------------------------------------- ECO встраиваемые
ECO_FOLDERS = {'TANGO': '561 563 TANGO', 'NANO': 'NANO', 'CUVY': 'CUVY', 'DOTO': 'DOTO', 'OCEAN': 'OCEAN',
               'REVO': 'REVO', 'TENK': 'TENK', 'UKKIE': 'Ukkie', 'EMO': 'EMO', 'VEVO': 'VEVO'}


def parse_eco(sheet_name, category, mounting):
    sh = sheet(sheet_name)
    cur = None
    hdr = None
    groups = []
    for r in range(1, sh.nrows):
        row = [s(v) for v in sh.row_values(r)]
        if row[0] and not any(row[1:]):
            cur = {'title': row[0], 'rows': [], 'hdr_row': r}
            groups.append(cur)
            continue
        if row[0].startswith('No'):
            hdr = row
            continue
        if cur is not None and row[2]:
            cur['rows'].append((r, dict(zip(hdr, row))))
    for g in groups:
        series = g['rows'][0][1]['Серия'].upper().split('-')[0]
        name = series
        if series == 'EMO':
            name = 'EMO'
        folder = ECO_FOLDERS.get(series)
        imgs = folder_images(ECO_DIR + folder) if folder else []
        if series == 'VEVO':
            imgs += folder_images(ECO_DIR + 'VEVO/Белый')
        xl = []
        for r, _ in g['rows']:
            xl += xl_images(sheet_name, r)
        xl += xl_images(sheet_name, g['hdr_row'])
        if series == 'TENK':  # правки: новые фото TENK
            imgs = folder_images(EDITS + 'TENK')
            xl = []
        variants = []
        for r, d in g['rows']:
            flux = d.get('Световой поток Lumen', '')
            v = {
                'sku': 'ADA-ECO.' + d['Серия'].upper() + '-' + s(d['Мощность']).upper().replace(' ', ''),
                'model': d['Серия'],
                'power': s(d['Мощность']).replace('w', ' Вт').replace('W', ' Вт'),
                'flux': flux.replace('lm', ' лм'),
                'cutout': d.get('Врезное отверстие', '').replace('Φ', 'Ø'),
                'size': d.get('Размер', '').replace('Φ', 'Ø'),
                'cct': '2700 / 3000 / 4000 K (3CCT)' if '3CCT' in d.get('Цветовая темп.', '') else d.get('Цветовая темп.', '') + ' K',
                'ip': d.get('IP', ''),
                'ik': d.get('IK', ''),
                'beam': d.get('Угол луча', ''),
                'driver': d.get('Блок питания', d.get('Driver', '')),
                'warranty': d.get('Гарантия', '').replace('3year', '3 года').replace('5year', '5 лет'),
                'material': 'Алюминий',
                'price': price(d.get('РРЦ')),
            }
            rowimg = xl_images(sheet_name, r)
            if xl and rowimg:
                v['_img'] = rowimg[0]
            if sheet_name.startswith('Накладные'):
                v['cutout'] = ''
                v['diffuser'] = 'PMMA'
            variants.append(v)
        # фото модификаций по данным из имён файлов (фото из папки приоритетнее картинки из прайса)
        def base(f):
            return os.path.basename(f).lower()
        for n, v in enumerate(variants):
            wv = re.match(r'(\d+)', v['power'].replace('2x', ''))
            wv = wv.group(1) if wv else None
            pick = None
            if series == 'DOTO':  # 1.jpg…5.jpg — те же 5 типоразмеров по возрастанию
                cand = [f for f in imgs if base(f) == f'{n + 1}.jpg']
                pick = cand[0] if cand else None
            elif series == 'OCEAN':  # 双 — двойной, 方-单 — квадратный, 圆 — круглый
                if '2x' in v['power'].lower():
                    key = '双'
                elif 'x' in v['cutout'].lower() or '×' in v['cutout']:
                    key = '方-单'
                else:
                    key = '圆'
                cand = [f for f in imgs if key in os.path.basename(f)]
                pick = cand[0] if cand else None
            elif wv:
                for f in imgs:
                    b = base(f)
                    if re.match(r'%s w?\.' % wv, b.replace(wv, wv + ' ', 1)) or re.search(r'(^|[-_ ])%sw([-_ .]|$)' % wv, b):
                        pick = f
                        break
            if pick:
                v['_img'] = pick
        # фикс явной опечатки в прайсе: DOTO 36W 360lm -> 3600 лм
        for v in variants:
            if v['model'].upper() == 'DOTO' and v['power'].startswith('36') and v['flux'].startswith('360 '):
                v['flux'] = '3600 лм'
        add({
            'slug': series.lower() if sheet_name.startswith('Встраиваемые') else series.lower() + '-surface',
            'name': name,
            'category': category,
            'line': 'ECO',
            'mounting': mounting,
            'images': imgs + xl,
            'variants': variants,
            'sheet': sheet_name,
        })


parse_eco('Встраиваемые ECO', 'vstraivaemye', 'Встраиваемый')
parse_eco('Накладные ECO', 'nakladnye', 'Накладной')

# ---------------------------------------------------------------- Class A
sh = sheet('Встраиваемые Class A')
hdr = [s(v) for v in sh.row_values(2)]
for r in range(3, sh.nrows):
    row = [s(v) for v in sh.row_values(r)]
    d = dict(zip(hdr, row))
    sku = d['Артикул']
    if not sku:
        continue
    base = re.match(r'ADA-IB\.(\d{4})', sku).group(1)
    pw = d['Мощность, W']
    if pw == '46302':  # Excel превратил "7/10" в дату
        pw = '7/10'
    v = {
        'sku': sku, 'model': sku,
        'power': pw + ' Вт', 'flux': '90 лм/Вт', 'cutout': d['Врезное отверстие'].replace('Ф', 'Ø').replace('mm', ' мм'),
        'size': d['Размер, mm'].replace('Ф', 'Ø').replace('*', '×'), 'cct': '2700 / 3000 / 4000 K',
        'ip': d['IP'], 'beam': d['Угол луча'].replace('/', '° / ') + '°', 'cri': 'Ra ' + d['Ra'],
        'driver': d['Блок питания'], 'color': d['Цвет'], 'warranty': d['Гарантия'], 'material': 'Алюминий',
        'price': price(d['РРЦ']),
    }
    existing = [p for p in products if p.get('slug') == 'a-' + base]
    if existing:
        existing[0]['variants'].append(v)
        continue
    add({
        'slug': 'a-' + base, 'name': 'CLASS A ' + base, 'category': 'vstraivaemye', 'line': 'CLASS A',
        'mounting': 'Встраиваемый', 'images': (folder_images(os.path.join(EDITS_WORK, 'alpha', 'CLASS A ' + base)) or folder_images(A_DIR + 'ALDL' + base)) + xl_images('Встраиваемые Class A', r),
        'variants': [v], 'sheet': 'Встраиваемые Class A',
    })

# ---------------------------------------------------------------- PRM (встраиваемые + накладные)
PRM_NAMES = {
    'ADA-SG.TH.7210A': ('TUBE A', 'Встраиваемый поворотный downlight с глубоким антибликовым отражателем'),
    'ADA-SG.TH.7210B': ('TUBE B', 'Компактный встраиваемый downlight с глубокой посадкой источника'),
    'ADA-SG.TH.7210T': ('TUBE T', 'Встраиваемый downlight с поворотным модулем и сменными отражателями'),
    'ADA-SG.TD.7269': ('TD 7269', 'Встраиваемый светильник с утопленным источником света'),
    'ADA-SG.TD.7267A': ('TD 7267A', 'Влагозащищённый встраиваемый светильник IP54/65'),
    'ADA-SG.TD.7267B': ('TD 7267B', 'Влагозащищённый встраиваемый светильник с широким диапазоном врезки'),
    'ADA-SG.TD.7272': ('TD 7272', 'Низкопрофильный встраиваемый светильник 120 лм/Вт'),
    'ADA-SG.TD.7244VY': ('TD 7244 Round', 'Круглый встраиваемый светильник 120 лм/Вт, IP44/54'),
    'ADA-SG.TD.7244VF': ('TD 7244 Square', 'Квадратный встраиваемый светильник 120 лм/Вт, IP44/54'),
    'ADA-SG.TD.7244VF2': ('TD 7244 Double', 'Двойной встраиваемый светильник, IP44'),
    'ADA-SG.TD.7239': ('TD 7239', 'Встраиваемый даунлайт общего освещения, IP44'),
    'ADA-SG.TD.7278S': ('TD 7278 Slim', 'Тонкий встраиваемый даунлайт с широким углом 60°'),
    'ADA-SG.GS.9002A': ('GRID 9002', 'Встраиваемый карданный светильник на 1–3 модуля'),
    'ADA-SG.X.7518FT': ('X 7518', 'Встраиваемый поворотный светильник под шпаклёвку'),
    'ADA-SG.X.7529F2': ('X 7529 Double', 'Двойной карданный светильник IP54/65'),
    'ADA-SG.X.7529FT2': ('X 7529 Double Trimless', 'Двойной карданный светильник под шпаклёвку IP54/65'),
    'ADA-SG.X.7525Y2': ('X 7525 Oval', 'Двойной овальный карданный светильник'),
    'ADA-SG.X.7525YT2': ('X 7525 Oval Trimless', 'Двойной овальный карданный светильник под шпаклёвку'),
    'ADA-OV.M1810Y': ('M1810 Round', 'Накладной цилиндр с поворотным модулем'),
    'ADA-OV.M1810F': ('M1810 Square', 'Накладной квадратный светильник с поворотным модулем'),
    'ADA-OV.M15Y': ('M15 Round', 'Накладной цилиндр 9–60 Вт со сменными отражателями'),
    'ADA-OV.M15F': ('M15 Square', 'Накладной квадратный светильник 10–40 Вт'),
    'ADA-OV.M17': ('M17 Disc', 'Низкий накладной даунлайт-диск'),
    'ADA-OV.M1015Y': ('M1015 Tube', 'Накладной светильник-труба с глубоким отражателем'),
}


def prm_base(sku):
    sku = sku.replace(' ', '')
    for pat, rep in [(r'^(ADA-SG\.TD\.7239)-\d+', r'\1'), (r'^(ADA-SG\.GS\.9002A)-\d', r'\1'),
                     (r'^(ADA-SG\.X\.7518FT)-.*', r'\1'), (r'^(ADA-SG\.X\.7529FT?2)-.*', r'\1'),
                     (r'^(ADA-SG\.X\.7525YT?2)-.*', r'\1'), (r'^(ADA-OV\.M1810[YF])-.*', r'\1'),
                     (r'^ADA-OV\.M15\d\dY.*', 'ADA-OV.M15Y'), (r'^ADA-OV\.M15\d\dF.*', 'ADA-OV.M15F'),
                     (r'^ADA-OV\.M17\d\d.*', 'ADA-OV.M17'), (r'^(ADA-OV\.M1015Y)-.*', r'\1')]:
        if re.match(pat, sku):
            return re.sub(pat, rep, sku)
    return sku


def parse_prm(sheet_name, hdr_row, category, mounting, photo_col, scheme_col, sku_key):
    sh = sheet(sheet_name)
    hdr = [s(v) for v in sh.row_values(hdr_row)]
    groups = {}
    order = []
    for r in range(hdr_row + 1, sh.nrows):
        row = [s(v) for v in sh.row_values(r)]
        d = dict(zip(hdr, row))
        sku = d.get(sku_key, '').replace(' ', '')
        if not sku:
            continue
        base = prm_base(sku)
        if base not in groups:
            groups[base] = {'rows': []}
            order.append(base)
        groups[base]['rows'].append((r, d, sku))
    for base in order:
        g = groups[base]
        nm, desc = PRM_NAMES.get(base, (base, ''))
        variants, imgs, schemes = [], [], []
        for r, d, sku in g['rows']:
            imgs += xl_images(sheet_name, r, photo_col)
            schemes += xl_images(sheet_name, r, scheme_col)
            ip = d.get('IP', '')
            color = d.get('Цвет', '').replace('Trim:', 'Корпус: ').replace('Reflector:', ' Отражатель: ') \
                .replace('White', 'белый').replace('Black', 'чёрный').replace('Gold', 'золотой')
            pw = d.get('Мощность', '')
            ph = xl_images(sheet_name, r, photo_col)
            sc = xl_images(sheet_name, r, scheme_col)
            variants.append({
                '_img': ph[0] if ph else None, '_sch': sc[0] if sc else None,
                'sku': sku + ('' if re.search(r'-\d+W?$|\d+W', sku) or sku.endswith(pw.upper().replace('W', '')) else '-' + pw.upper()),
                'model': sku, 'power': pw.upper().replace('/W', '').replace('W', ' Вт'),
                'flux': d.get('Световой поток', '').replace('lm/W', ' лм/Вт'),
                'cutout': d.get('Врез. Отверстие', '').replace('D', 'Ø').replace('mm', ' мм'),
                'size': d.get('Размер', '').replace('D', 'Ø').replace('*H', ' × H').replace('mm', ' мм'),
                'cct': '2700 / 3000 / 4000 / 6000 K', 'ip': 'IP' + ip.replace('/', '/IP'), 'cri': 'Ra ' + d.get('CRI', ''),
                'beam': d.get('Угол луча', '').replace(' ', ''), 'color': color, 'material': 'Алюминий',
                'warranty': '5 лет', 'price': price(d.get('РРЦ')),
            })
        add({'slug': re.sub(r'[^a-z0-9]+', '-', nm.lower()).strip('-'), 'name': nm, 'lead': desc,
             'article': base, 'category': category, 'line': 'PRM', 'mounting': mounting,
             'images': imgs, 'schemes': schemes, 'variants': variants, 'sheet': sheet_name})


parse_prm('Встраиваемые PRM', 2, 'vstraivaemye', 'Встраиваемый', 1, 2, 'Серия')
parse_prm('Накладные PRM', 1, 'nakladnye', 'Накладной', 0, 1, 'Серия')

# ---------------------------------------------------------------- SOFI
sh = sheet('Накладные SOFI')
cur = None
sofi = []
for r in range(1, sh.nrows):
    row = [s(v) for v in sh.row_values(r)]
    if row[0] and not any(row[1:]):
        cur = {'title': row[0], 'rows': []}
        sofi.append(cur)
        continue
    if row[0].startswith('№'):
        continue
    if row[2]:
        cur['rows'].append((r, row))
for g in sofi:
    # X7 делим на IP54 и IP20
    parts = {}
    for r, row in g['rows']:
        key = g['title'] if 'X7' not in g['title'] else 'X7 ' + ('IP54' if row[10] == 'IP54' else 'IP20')
        parts.setdefault(key, []).append((r, row))
    for title, rows in parts.items():
        variants, imgs = [], []
        for r, row in rows:
            ph = xl_images('Накладные SOFI', r, 11)
            imgs += ph
            variants.append({'_img': ph[0] if ph else None, 'sku': row[2].replace(' ', ''), 'model': row[2], 'power': row[5].replace('W', ' Вт'),
                             'flux': row[6].replace('lm/w', ' лм/Вт').replace('LM/W', ' лм/Вт').replace('lm', ' лм'),
                             'size': row[3].replace('φ', 'Ø').replace('*', ' × ').replace('mm', '') + ' мм',
                             'color': row[4], 'cri': 'Ra ' + row[7].replace('＞', '>'), 'cct': '3000 / 4000 / 6500 K (переключатель)',
                             'warranty': row[9], 'ip': row[10], 'material': 'Алюминий / PMMA', 'price': price(row[12])})
        nm = 'SOFI ' + title.replace('Round', 'Round').replace('Square', 'Square')
        add({'slug': re.sub(r'[^a-z0-9]+', '-', nm.lower()).strip('-'), 'name': nm, 'category': 'nakladnye', 'line': 'SOFI',
             'mounting': 'Накладной', 'images': imgs, 'variants': variants, 'sheet': 'Накладные SOFI'})

# ---------------------------------------------------------------- RAVOL + кольца
sh = sheet('Накладные RAVOL, Кольца')
rav, ring, rimgs, ringimgs = [], [], [], []
for r in range(3, sh.nrows):
    row = [s(v) for v in sh.row_values(r)]
    if not row[3]:
        continue
    v = {'sku': row[3] + '-' + row[4], 'model': row[3], 'power': row[4].replace('W', ' Вт'), 'flux': row[5].replace('LM/W', ' лм/Вт'),
         'ip': 'IP' + row[6], 'cct': row[7].replace('2CCT (3000,4000)', '3000 / 4000 K (2CCT)').replace('2700/3000/4000', '2700 / 3000 / 4000 K'),
         'size': row[8].replace('φ', 'Ø').replace('D', 'Ø').replace('*', ' × ') + ' мм', 'color': row[9], 'beam': row[10].replace('°', '') + '°',
         'cri': 'Ra ' + row[11], 'price': price(row[12]), 'price_dim': price(row[13]), 'warranty': row[14], 'material': 'Алюминий'}
    if row[3].startswith('RAVOL'):
        rav.append(v); rimgs += xl_images('Накладные RAVOL, Кольца', r, 1)
    else:
        v['sku'] = 'ADA-RING-' + row[8].split('*')[0].replace('D', 'D') + '-' + row[4]
        ring.append(v); ringimgs += xl_images('Накладные RAVOL, Кольца', r, 1)
add({'slug': 'ravol', 'name': 'RAVOL', 'category': 'nakladnye', 'line': 'DESIGN', 'mounting': 'Накладной / подвесной',
     'images': folder_images(os.path.join(EDITS_WORK, 'ravol')) or rimgs, 'variants': rav, 'sheet': 'RAVOL'})
add({'slug': 'ada-ring', 'name': 'ADA RING', 'category': 'lineynye', 'line': 'DESIGN', 'mounting': 'Подвесной',
     'images': folder_images(os.path.join(EDITS_WORK, 'ring')) or ringimgs, 'variants': ring, 'sheet': 'Кольца'})

# ---------------------------------------------------------------- Линейные
sh = sheet('Линейные светильники')
lin_groups = {}
cur_title = ''
lin_photos = folder_images(LIN_DIR)
for r in range(1, sh.nrows):
    row = [s(v) for v in sh.row_values(r)]
    if row[0] and not any(row[1:]):
        cur_title = row[0]
        continue
    if row[0].startswith('No') or not row[2]:
        continue
    size = row[8]
    prof = size.split('*', 1)[1] if '*' in size else size
    ip = row[6]
    key = ('IP' + ip + ' ' + prof) if ip != '20' else prof
    lin_groups.setdefault(key, []).append((r, row))
LIN_META = {
    '35*35': ('ADA-LINE 35', 'ada-line-35', ['3535.png', '3535_2.png']),
    '50*50': ('ADA-LINE 50', 'ada-line-50', ['5050_1.png', '5050_2.jpg']),
    '40*75': ('ADA-LINE 40×75', 'ada-line-4075', ['4075_1.jpg', '4075_2.jpg', '4075_3.jpg']),
    'IP54 40*50': ('ADA-LINE IP54', 'ada-line-ip54', ['4050_1.jpg', '4050_2.jpg']),
    'IP65 50*80': ('ADA-LINE IP65', 'ada-line-ip65', ['5080_1.jpg', '5080_2.jpg']),
}
for key, rows in lin_groups.items():
    nm, slug, ph = LIN_META[key]
    variants, imgs = [], [LIN_DIR + p for p in ph]
    for r, row in rows:
        ph = xl_images('Линейные светильники', r, 1)
        imgs += ph
        variants.append({'_img': ph[0] if ph else None, 'sku': 'ADA-LINE-' + row[8].replace('*', 'x'), 'model': 'ADA-LINE', 'power': row[3] + ' Вт',
                         'flux': row[4] + ' лм', 'cct': row[5].replace('/', ' / ') + ' K', 'ip': 'IP' + row[6],
                         'size': row[8].replace('*', ' × ') + ' мм', 'driver': row[9], 'beam': row[11] + '°',
                         'warranty': '3 года', 'material': 'Алюминий', 'color': 'Любой цвет по RAL', 'price': price(row[15])})
    add({'slug': slug, 'name': nm, 'category': 'lineynye', 'line': 'LINE', 'mounting': 'Накладной / подвесной',
         'images': imgs, 'variants': variants, 'sheet': 'Линейные'})

# ---------------------------------------------------------------- S20 светильники
S20_FAMILIES = [
    ('grill-mini', 'S20 Grill Mini', 'Мини-грильяж: ряд точечных линз в тонком корпусе 16 мм', r'HS26-\d+TA$'),
    ('flood-mini', 'S20 Flood Mini', 'Тонкий линейный модуль рассеянного света 16 мм', r'HS26-\d+FA$'),
    ('grill', 'S20 Grill', 'Линейный грильяж с линзами 36° — акцентный свет рядом точек', r'HS26-\d+T$'),
    ('wallwasher', 'S20 Wallwasher', 'Асимметричная оптика для равномерной заливки стен', r'HS26-\d+TP$'),
    ('flood', 'S20 Flood', 'Линейный модуль общего рассеянного света 120°', r'HS26-\d+F$'),
    ('flood-corner', 'S20 Flood Corner', 'Угловой линейный модуль 90° для непрерывных линий', r'HS26-300F-L$'),
    ('grill-rotate', 'S20 Grill Rotate', 'Поворотный грильяж: направляйте свет на объект', r'HS26-\d+TX$'),
    ('flood-rotate', 'S20 Flood Rotate', 'Поворотный линейный модуль рассеянного света', r'HS26-\d+FX$'),
    ('stick', 'S20 Stick', 'Светящийся профиль 180° — мягкая линия света', r'HS26-SS\d+F$'),
    ('folding-spot', 'S20 Folding Spot', 'Складной поворотный спот', r'CXM75N$'),
    ('grill-folding', 'S20 Grill Folding', 'Складной поворотный грильяж', r'CX003-(6|12)T$'),
    ('flood-folding', 'S20 Flood Folding', 'Складной поворотный модуль рассеянного света', r'CX003-(6|12)F$'),
    ('grill-folding-xl', 'S20 Grill Folding XL', 'Крупный складной грильяж 30°', r'CX003-(5|10)T$'),
    ('convex', 'S20 Convex', 'Миниатюрный акцентный светильник 3 Вт', r'HX0[12]$'),
    ('lunar', 'S20 Lunar', 'Акриловый светильник мягкого света «Лунное затмение»', r'CX100F$'),
    ('disc', 'S20 Disc', 'Плоский трековый диск: мягкий, заливающий и акцентный свет', r'CX[ZBG]90$'),
    ('wide', 'S20 Wide', 'Широкоугольный трековый светильник 18 Вт', r'DJD90$'),
    ('reading', 'S20 Reading', 'Миниатюрный светильник для чтения', r'YDL20$'),
    ('bowl', 'S20 Bowl', 'Трековый светильник-чаша', r'Q80$'),
    ('glass', 'S20 Glass', 'Декоративные плафоны: стекло и акрил', r'HS26-(B80|P95|BL150)$'),
    ('spot', 'S20 Spot', 'Трековые прожекторы 7–24 Вт, линза 24°', r'CX0\d\d$'),
    ('zoom', 'S20 Zoom', 'Прожекторы с фокусировкой луча 15–55°', r'CXT\d+N$'),
    ('pendant-sphere', 'S20 Pendant Sphere', 'Подвесные шары: акрил, стекло, «Земля» и «Луна»', r'(CXD100F|DP95|DBL150|CXD150-DQ|CXD150-YQ)$'),
    ('pendant-tube', 'S20 Pendant Tube', 'Подвесные цилиндры с регулировкой высоты', r'(CXD300|CXDSL300)$'),
    ('pendant-ring', 'S20 Pendant Ring', 'Подвесные круглые светильники', r'(CXDY100|CXDYT100)$'),
    ('silicone', 'S20 Silicone', 'Гибкая силиконовая световая трубка 360°', r'GJ\d+$'),
]


def s20_folder(code):
    # AL-TR.48.HS26-12T -> HS26-12T ; HS26-CX035 -> HS-CX035
    c = code.replace('AL-TR.48.', '')
    cands = [c, c.replace('HS26-CX', 'HS-CX')]
    for cnd in cands:
        if os.path.isdir(S20_LAMPS + cnd):
            return folder_images(S20_LAMPS + cnd)
    return []


sh = sheet('Светильники S20 48V')
hdr = [s(v) for v in sh.row_values(2)]
s20rows = []
for r in range(3, sh.nrows):
    row = [s(v) for v in sh.row_values(r)]
    if row[2]:
        s20rows.append((r, row))
for slug, nm, lead, pat in S20_FAMILIES:
    variants, imgs = [], []
    for r, row in s20rows:
        if not re.search(pat, row[2]):
            continue
        own = s20_folder(row[2])
        imgs += own
        name_ru = re.sub(r'\s*\(.*?\)|\s[A-Z][A-Za-z -]+$', '', row[1]).replace('свтелиьник', 'светильник').replace('свтелиьник', 'светильник').strip()
        v = {'sku': row[2], 'model': row[1].replace('свтелиьник', 'светильник').replace('свтелиьник', 'светильник'),
             'size': row[4].replace('*', ' × ').replace('Ø', 'Ø') + ' мм', 'led': row[5].replace('ORSAM', 'OSRAM'),
             'power': row[6].replace('W', ' Вт'), 'beam': row[7], 'voltage': 'DC 48 В', 'cri': 'Ra ' + row[9],
             'warranty': row[10], 'cct': row[11].replace(' ', ' / ').replace('K', ' K').replace('/ /', '/').replace('  ', ' '),
             'color': 'Чёрный', 'price': price(row[13]),
             'price_dip': price(row[14]) if row[14] not in ('нет', '15') else None,
             'price_zigbee': price(row[15]) if row[15] != 'нет' else None}
        v['cct'] = ' / '.join(re.findall(r'\d{4}', row[11])) + ' K'
        v['_img'] = own[0] if own else None
        variants.append(v)
    if not variants:
        print('!! empty family', slug)
        continue
    add({'slug': 's20-' + slug, 'name': nm, 'lead': lead, 'category': 'trekovye-s20', 'line': 'S20 48V', 'mounting': 'Трековый магнитный',
         'images': imgs, 'variants': variants, 'sheet': 'S20'})

# ---------------------------------------------------------------- Шинопровод S20
sh = sheet('Шинопровод S20 48V')
trows = []
last_name = ''
for r in range(3, sh.nrows):
    row = [s(v) for v in sh.row_values(r)]
    if not row[2]:
        continue
    if row[1]:
        last_name = row[1]
    trows.append((r, row, row[1] or last_name))
TRACK_GROUPS = [
    ('track-a', 'Шинопровод S20 A — накладной / подвесной', 'Тонкий накладной шинопровод 26×27 мм', r'HS26-A'),
    ('track-b', 'Шинопровод S20 B — встраиваемый', 'Встраиваемый шинопровод 53×20 мм для ГКЛ', r'HS26-B'),
    ('track-c', 'Шинопровод S20 C — накладной / подвесной', 'Шинопровод 27×55 мм с усиленным профилем', r'HS26-C(\.|-L|-LV|-MZKK)'),
    ('track-d', 'Шинопровод S20 D — встраиваемый', 'Встраиваемый шинопровод 65×55 мм', r'HS26-D'),
    ('track-e', 'Шинопровод S20 E — встраиваемый', 'Встраиваемый шинопровод 65×55 мм, вариант E', r'HS26-E'),
    ('track-stretch', 'Шинопровод S20 для натяжного потолка', 'Встраивание в натяжной потолок: профиль, углы, заглушки, крепёж', r'HS26-RM|HS-RM'),
    ('track-connectors', 'Соединители и токовводы S20', 'Токовводы, прямые и угловые соединители, подвесы', r'HS26-SRMK|HS26-I$|HS26-RJ|HS-PJ|HS-DX'),
    ('track-power', 'Блоки питания S20 48V', 'Встраиваемые драйверы 100/200 Вт, в т.ч. с управлением Tuya ZigBee', r'HS26-\d+W'),
    ('track-smart', 'Шлюз и пульт Tuya ZigBee', 'Шлюз (интегратор) и пульт для управления светом со смартфона и голосом', r'Gateway|RC-TUYA'),
]
TRACK_FOLDERS = {'HS26-A.': 'HS-26A', 'HS26-A-L': 'HS-26A-L', 'HS26-A-LV': 'HS-26A-LV', 'HS26-B.': 'HS-26B', 'HS26-B-L': 'HS-26B-L',
                 'HS26-B-LV': 'HS-26B-LV', 'HS26-C.': 'HS-26C', 'HS26-C-L': 'HS-26C-L', 'HS26-C-LV': 'HS-26C-LV', 'HS26-C-MZKK': 'HS26-C-MZKK',
                 'HS26-D.': 'HS-26D', 'HS26-D-L': 'HS-26D-L', 'HS26-D-LV': 'HS-26D-LV', 'HS26-E.': 'HS-26E', 'HS26-E-L': 'HS-26E-L',
                 'HS26-E-LV': 'HS-26E-LV', 'HS26-SRMK': 'HS26-SRMK输入模块', 'HS26-I': 'HS26-I双头  直接头', 'HS26-RJ': 'HS26-RJ双头 软接头',
                 'HS-PJ': 'HS26-PJ轨道连接加固件', 'HS-DX': 'HS26-DX', 'HS26-100W': 'HS26-100W', 'HS26-200W': 'HS26-200W',
                 'Gateway': '2.4G-Gateway', 'RC-TUYA': 'RC智能遥控器', 'HS26-RM-QRPC.': 'HS26-RM-QRPC', 'HS26-RM-QRPC-DT': 'HS26-RM-QRPC-DT',
                 'HS26-RM-QRPC-L': 'HS26-RM-QRPC-L', 'HS26-RM-MZ-C.': 'HS26-RM-MZ-C', 'HS26-RM-MZ-C-DT': 'HS26-RM-MZ-C-DT',
                 'HS26-RM-MZ-C-L': 'HS26-RM-MZ-C-L', 'HS-RM-SPJG': 'HS-RM-SPJG', 'HS-RM-CZJG': 'HS-RM-CZJG', 'HS-RM-JG': 'HS-RM-JG',
                 'HS-RM-JM': 'HS-RM-JM', 'HS-RM-GJT': 'HS-RM-GJT'}


def track_imgs(code):
    best = None
    for k, f in TRACK_FOLDERS.items():
        if k in code and (best is None or len(k) > len(best[0])):
            best = (k, f)
    return folder_images(S20_TRACK + best[1]) if best else []


used = set()
for slug, nm, lead, pat in TRACK_GROUPS:
    variants, imgs = [], []
    for r, row, name in trows:
        if row[2] in used or not re.search(pat, row[2]):
            continue
        used.add(row[2])
        own = track_imgs(row[2]) + xl_images('Шинопровод S20 48V', r, 3)
        imgs += own
        variants.append({'_img': own[0] if own else None, 'sku': row[2], 'model': name, 'color': row[4] or 'Чёрный / Белый',
                         'size': (row[5].replace('*', ' × ') + ' мм') if row[5] not in ('/', '') and 'Размер' not in row[5] else row[5].replace('Размер', 'Длина').replace('mm', ' мм').replace('/', '—'),
                         'voltage': 'DC 48 В', 'price': price(row[6])})
    add({'slug': 's20-' + slug, 'name': nm, 'lead': lead, 'category': 'shinoprovod-s20', 'line': 'S20 48V', 'mounting': 'Шинопровод',
         'images': imgs, 'variants': variants, 'sheet': 'Шинопровод'})
missing = [row[2] for r, row, n in trows if row[2] not in used]
if missing:
    print('!! track rows not grouped', missing)

# ---------------------------------------------------------------- Бра
sh = sheet('Бра')
bra = []
cur = None
for r in range(3, sh.nrows):
    row = [s(v) for v in sh.row_values(r)]
    if row[2]:
        cur = {'model': row[2], 'rows': [], 'r': r}
        bra.append(cur)
    if cur is not None:
        cur['rows'].append((r, row))
BRA_NAMES = {'1': ('WALL 01', 'Компактное поворотное бра-трубка для чтения'), '501': ('WALL 501', 'Встраиваемое бра-ниша с подсветкой для чтения'),
             '504': ('WALL 504', 'Встраиваемое бра со скрытой кнопкой и USB'), '505': ('WALL 505', 'Встраиваемое бра со скрытой кнопкой и USB'),
             '547': ('WALL 547', 'Встраиваемое бра с USB / Type-C'), '218': ('WALL 218', 'Квадратное бра для чтения с гибкой лампой'),
             '252': ('WALL 252', 'Настенный светильник 12 Вт с цепным выключателем'), '253': ('WALL 253', 'Декоративное бра металл + акрил'),
             '210': ('WALL 210', 'Линейное бра 600–1000 мм'), '211': ('WALL 211', 'Линейное бра 600–1000 мм, лаконичный профиль'),
             '319': ('WALL 319', 'Встраиваемое бра со скрытым выключателем'), '502': ('WALL 502', 'Встраиваемое бра-ниша с кнопкой'),
             '518': ('WALL 518', 'Бра с поворотной лампой для изголовья'), '600': ('WALL 600', 'Настенный светильник IP65 для улицы и влажных зон')}
for b in bra:
    nm, lead = BRA_NAMES.get(b['model'], ('WALL ' + b['model'], ''))
    variants, imgs = [], []
    base = dict(zip(['n', 'photo', 'model', 'material', 'size', 'color', 'power', 'switch', 'price'], b['rows'][0][1]))
    for r, row in b['rows']:
        d = dict(zip(['n', 'photo', 'model', 'material', 'size', 'color', 'power', 'switch', 'price'], row))
        ph = xl_images('Бра', r, 1)
        imgs += ph
        variants.append({'_img': ph[0] if ph else None, 'sku': 'ADA-WALL-' + b['model'] + '-' + str(len(variants) + 1), 'model': nm,
                         'material': d['material'] or base['material'], 'size': (d['size'] or base['size']).replace('*', ' × ').replace('"', ''),
                         'color': d['color'], 'power': (d['power'] or base['power']).upper().replace('W', ' Вт'),
                         'switch': (d['switch'] or base['switch']).replace('/', '—'), 'price': price(d['price'])})
    add({'slug': 'wall-' + b['model'], 'name': nm, 'lead': lead, 'category': 'bra', 'line': 'WALL', 'mounting': 'Настенный',
         'images': imgs, 'variants': variants, 'sheet': 'Бра'})

# ---------------------------------------------------------------- фильтровые атрибуты
for p in products:
    vs = p['variants']
    ws = [watt(v.get('power', '')) for v in vs if v.get('power')]
    ws = [w for w in ws if w]
    p['power_min'] = min(ws) if ws else None
    p['power_max'] = max(ws) if ws else None
    ps = [v['price'] for v in vs if v.get('price')]
    p['price_min'] = min(ps) if ps else None
    cct = set()
    ips = set()
    bm = set()
    for v in vs:
        cct |= set(norm_cct(v.get('cct', '')))
        ips |= set(norm_ip(v.get('ip', '')))
        for b in beams(v.get('beam', '')):
            bm.add(b)
    p['cct_list'] = sorted(cct)
    p['ip_list'] = sorted(i for i in ips if i in (20, 40, 44, 54, 65, 67))
    p['beam_list'] = sorted(bm)
    p['sku_count'] = len(vs)

os.makedirs(os.path.join(ROOT, 'data'), exist_ok=True)
json.dump(products, open(os.path.join(ROOT, 'data', 'products_raw.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('products:', len(products), 'skus:', sum(len(p['variants']) for p in products))
for p in products:
    print(f"{p['category']:16} {p['slug']:28} {p['name'][:34]:34} v={len(p['variants']):2} img={len(p['images']):2} sch={len(p['schemes'])} P={p['power_min']}-{p['power_max']} ip={p['ip_list']} cct={p['cct_list']} from={p['price_min']}")
