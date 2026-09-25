# -*- coding: utf-8 -*-
"""Сборка статического сайта ADALIGHT -> docs/ (GitHub Pages)."""
import json, os, re, shutil, datetime, io, html
from jinja2 import Environment, FileSystemLoader, select_autoescape
import content as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs')
CFG = json.load(open(os.path.join(ROOT, 'site.config.json'), encoding='utf-8'))
BASE = CFG['base'].rstrip('/')
SITE_URL = CFG['site_url'].rstrip('/')
VER = datetime.datetime.now().strftime('%y%m%d%H%M')

env = Environment(loader=FileSystemLoader(os.path.join(ROOT, 'templates')), autoescape=select_autoescape(['html']), trim_blocks=True, lstrip_blocks=True)
env.filters['rub'] = lambda n: ('{:,}'.format(int(n)).replace(',', ' ') + ' ₽') if n else ''

products = json.load(open(os.path.join(ROOT, 'data', 'products.json'), encoding='utf-8'))
media_raw = json.load(open(os.path.join(ROOT, 'data', 'media.json'), encoding='utf-8'))


def pref(e):
    """Добавить base к путям картинок."""
    if not e:
        return e
    e = dict(e)
    e['src'] = BASE + e['src']
    e['lg'] = BASE + e['lg']
    e['srcset'] = re.sub(r'(^|, )/', lambda m: m.group(1) + BASE + '/', e['srcset'])
    return e


class Media(dict):
    def __missing__(self, k):
        return None


media = Media({k: pref(v) for k, v in media_raw.items()})
for p in products:
    p['images'] = [pref(i) for i in p['images']]
    p['schemes'] = [pref(i) for i in p['schemes']]


# ---------------------------------------------------------------- обогащение товаров
def num(s):
    m = re.findall(r'\d+(?:[.,]\d+)?', str(s or ''))
    return [float(x.replace(',', '.')) for x in m]


def rng(a, b, unit):
    if a is None:
        return None
    fa = ('%g' % a)
    fb = ('%g' % b)
    return f'{fa} {unit}' if a == b else f'{fa}–{fb} {unit}'


def lumens(v):
    f = v.get('flux', '') or ''
    w = num(v.get('power', ''))
    watts = None
    if w:
        mm = re.findall(r'(\d+)\s*[xх×]\s*(\d+)', v.get('power', '').lower())
        watts = int(mm[0][0]) * int(mm[0][1]) if mm else w[-1]
    if 'лм/Вт' in f and watts:
        return int(num(f)[0] * watts)
    if 'лм' in f and num(f):
        return int(num(f)[0])
    if watts and v.get('led') or (watts and v.get('voltage')):
        return int(watts * 90)
    return None


MOUNT = {'Встраиваемый': 'Встраиваемый', 'Накладной': 'Накладной', 'Накладной / подвесной': 'Накладной', 'Подвесной': 'Подвесной',
         'Трековый магнитный': 'Трековый', 'Шинопровод': 'Шинопровод', 'Настенный': 'Настенный'}
COLS = [('sku', 'Артикул', True), ('model', 'Наименование', False), ('power', 'Мощность', True), ('flux', 'Поток', True),
        ('cutout', 'Врезка', True), ('size', 'Размер', True), ('beam', 'Угол', True), ('ip', 'IP', True), ('cct', 'CCT', True),
        ('color', 'Цвет', False), ('switch', 'Выключатель', False), ('led', 'Светодиоды', True), ('driver', 'Драйвер', False)]
SPEC_NAMES = {'power': 'Мощность', 'flux': 'Световой поток / эффективность', 'cutout': 'Монтажное отверстие', 'size': 'Габариты',
              'cct': 'Цветовая температура', 'ip': 'Степень защиты', 'ik': 'Ударопрочность', 'beam': 'Угол луча', 'cri': 'Цветопередача',
              'driver': 'Драйвер', 'color': 'Цвет', 'material': 'Материал корпуса', 'warranty': 'Гарантия', 'voltage': 'Напряжение',
              'led': 'Светодиоды', 'diffuser': 'Рассеиватель', 'switch': 'Выключатель'}
SPEC_ORDER = ['power', 'flux', 'cct', 'cri', 'beam', 'ip', 'ik', 'cutout', 'size', 'voltage', 'led', 'driver', 'material', 'diffuser', 'color', 'switch', 'warranty']

cat_names = {k: v['name'] for k, v in C.CATEGORIES.items()}

def view_index(p, v):
    """Кадр галереи (фото + чертежи) для модификации: своё фото, если оно уникально;
    иначе — свой размерный чертёж; иначе — общее фото."""
    ni = len(p['images'])
    ii = v.get('img_i') if v.get('img_i') is not None and v['img_i'] < ni else None
    si = v.get('sch_i') if v.get('sch_i') is not None and v['sch_i'] < len(p['schemes']) else None
    shared = ii is not None and sum(1 for x in p['variants'] if x.get('img_i') == ii) > 1
    if ii is not None and not shared:
        return ii
    if si is not None:
        return ni + si
    return ii


for i, p in enumerate(products):
    vs = p['variants']
    p['mount_key'] = MOUNT.get(p['mounting'], p['mounting'])
    L = C.LINES.get(p['line'], C.LINES['PRM'])
    pr = rng(p['power_min'], p['power_max'], 'Вт')
    ip_txt = ', '.join('IP%d' % x for x in p['ip_list'])
    cct_txt = ' / '.join(str(x) for x in p['cct_list'])
    cri = vs[0].get('cri', '')
    beams = [b for b in p['beam_list'] if 8 <= b <= 120]
    # короткий подзаголовок карточки и lead
    auto = {
        'ECO': f"{'Встраиваемый' if p['category'] == 'vstraivaemye' else 'Накладной'} светильник линейки ECO с переключаемой цветовой температурой 3CCT",
        'CLASS A': f"Премиальный встраиваемый светильник: {cri}, 90 лм/Вт, внешний драйвер",
        'SOFI': 'Тонкая накладная панель с DIP-переключателем цветовой температуры',
        'LINE': 'Линейный светильник в алюминиевом профиле, окраска по RAL',
        'DESIGN': 'Дизайнерский накладной / подвесной светильник',
    }
    lead = p.get('lead') or auto.get(p['line'], '')
    if p['slug'] == 'ada-ring':
        lead = 'Подвесное световое кольцо Ø500–800 мм — акцент над ресепшн, столом или в двусветном пространстве'
    if p['slug'] == 'ravol':
        lead = 'Крупный накладной или подвесной светильник-кольцо Ø300–1000 мм, 120 лм/Вт, версия с Triac-диммированием'
    p['card_sub'] = lead
    facts = []
    if pr:
        facts.append(pr)
    if cct_txt:
        facts.append(cct_txt + ' K')
    if ip_txt:
        facts.append(ip_txt)
    if beams:
        facts.append('угол ' + ', '.join('%d°' % b for b in beams[:5]))
    p['lead_text'] = lead + ('. ' + '; '.join(facts) + '.' if facts else '.') + f" {len(vs)} {'модификация' if len(vs) == 1 else 'модификации' if len(vs) < 5 else 'модификаций'} в наличии и под заказ."
    chips = []
    if pr:
        chips.append(pr)
    if ip_txt:
        chips.append(ip_txt.split(', ')[-1] if len(p['ip_list']) > 2 else ip_txt)
    if cri:
        chips.append(cri)
    if p['category'] in ('trekovye-s20', 'shinoprovod-s20'):
        chips.append('48 В')
    p['chips'] = chips[:4]
    # ключевые характеристики
    ks = []
    if pr:
        ks.append(('Мощность', pr))
    lms = [lumens(v) for v in vs]
    lms = [x for x in lms if x]
    if lms:
        ks.append(('Поток', rng(min(lms), max(lms), 'лм')))
    if cct_txt:
        ks.append(('Цвет. температура', cct_txt + ' K'))
    if cri:
        ks.append(('Цветопередача', cri))
    if ip_txt:
        ks.append(('Защита', ip_txt))
    if beams:
        ks.append(('Угол луча', ', '.join('%d°' % b for b in beams[:4])))
    if p['category'] in ('trekovye-s20', 'shinoprovod-s20'):
        ks.append(('Напряжение', 'DC 48 В'))
    if p['category'] == 'shinoprovod-s20':
        lens = sorted({int(m) for v in vs for m in re.findall(r'\.(1000|1500|2000|3000)$', v['sku'])})
        if lens:
            ks.append(('Длины', ' / '.join(('%g' % (x / 1000)).replace('.', ',') for x in lens) + ' м'))
        cols = sorted({c.strip() for v in vs for c in (v.get('color') or '').split('/') if c.strip()})
        if cols:
            ks.append(('Цвет', ' / '.join(cols)))
        ks.append(('Система', 'S20, магнитная'))
        ks.append(('Позиций', str(len(vs))))
    w = vs[0].get('warranty')
    if w:
        ks.append(('Гарантия', w.replace('YEARS', 'лет').replace('5 лет', '5 лет')))
    if p['category'] == 'bra':
        ks.append(('Выключатель', vs[0].get('switch', '—')[:28]))
        ks.append(('Материал', vs[0].get('material', '—')))
    p['key_specs'] = ks[:6]
    # общие характеристики
    common = []
    for k in SPEC_ORDER:
        vals = [str(v.get(k) or '').strip() for v in vs]
        vals = [x for x in vals if x]
        if not vals:
            continue
        uniq = list(dict.fromkeys(vals))
        val = uniq[0] if len(uniq) == 1 else (' · '.join(uniq) if len(uniq) <= 3 and k not in ('size', 'cutout', 'power', 'flux') else 'см. таблицу артикулов')
        common.append((SPEC_NAMES[k], val.replace('YEARS', 'лет')))
    common.append(('Линейка', p['line']))
    common.append(('Тип монтажа', p['mounting']))
    p['common_specs'] = common
    # столбцы таблицы
    cols = []
    for key, title, mono in COLS:
        vals = [str(v.get(key) or '') for v in vs]
        if not any(vals):
            continue
        if key in ('sku', 'power', 'size') or len(set(vals)) > 1:
            if key == 'model' and len(set(vals)) == 1:
                continue
            cols.append((key, title, mono))
    p['table_cols'] = cols
    # опции исполнения
    opts = []
    if any(v.get('price_dip') or v.get('price_zigbee') for v in vs):
        opts = [{'key': 'base', 'label': 'Без управления'}, {'key': 'dip', 'label': 'DIM 3CCT'}, {'key': 'zigbee', 'label': 'Tuya ZigBee'}]
    elif any(v.get('price_dim') for v in vs):
        opts = [{'key': 'base', 'label': 'Без диммирования'}, {'key': 'dim', 'label': 'Triac DIM'}]
    p['options'] = opts
    # цвет корпуса: только там, где цвет есть в прайсе и есть фото обоих цветов (правки 25.09)
    COLORS = {'ravol': [('Чёрный', 0), ('Белый', 1)], 'ada-ring': [('Чёрный', 0), ('Белый', 1)],
              'sofi-x7-ip54': [('Белый', 0), ('Чёрный', 1)], 'sofi-x7-ip20': [('Белый', 0), ('Чёрный', 1)]}
    p['colors'] = [{'label': l, 'img': i} for l, i in COLORS.get(p['slug'], []) if i < len(p['images'])]
    img0 = p['images'][0]['src'] if p['images'] else (p['schemes'][0]['src'] if p['schemes'] else '')
    vjs = []
    for v in vs:
        parts = [v['sku']]
        if v.get('power'):
            parts.append(v['power'])
        sz_ok = v.get('size') and any(ch.isdigit() for ch in v['size'])
        if sz_ok and p['category'] not in ('vstraivaemye',):
            parts.append(v['size'])
        elif p['category'] == 'shinoprovod-s20' and v.get('model'):
            parts.append(v['model'][:60])
        elif v.get('cutout'):
            parts.append('врезка ' + v['cutout'])
        if p['category'] == 'bra' and v.get('color'):
            parts.append(v['color'][:40])
        v['label'] = ' · '.join(parts)
        params = ', '.join(x for x in [v.get('power'), v.get('cct'), v.get('ip') if v.get('ip') and v.get('ip') != 'IP' else '', v.get('beam')] if x)
        vi = v.get('img_i')
        vimg = p['images'][vi]['src'] if vi is not None and vi < len(p['images']) else img0
        add = {'sku': v['sku'], 'slug': p['slug'], 'name': p['name'], 'price': v.get('price'), 'img': vimg, 'params': params}
        v['add_json'] = json.dumps(add, ensure_ascii=False)
        o = {}
        if opts:
            o['base'] = {'price': v.get('price'), 'label': opts[0]['label']}
            for ok, pk in (('dip', 'price_dip'), ('zigbee', 'price_zigbee'), ('dim', 'price_dim')):
                if any(x['key'] == ok for x in opts):
                    o[ok] = {'price': v.get(pk), 'label': next(x['label'] for x in opts if x['key'] == ok)}
        vjs.append({'price': v.get('price'), 'add': add, 'opts': o, 'lm': lumens(v), 'img': view_index(p, v)})
    p['variants_js'] = vjs
    # калькулятор луча
    if beams and lms and p['category'] not in ('shinoprovod-s20', 'bra'):
        a = sorted(beams, key=lambda b: abs(b - 36))[0]
        p['beam'] = {'h': 2.7 if p['category'] != 'lineynye' else 2.2, 'a': a, 'f': lms[0], 'fmax': max(2000, int(max(lms) * 1.3 // 100 * 100)), 'angles': beams[:6]}
    bk = []
    if any(b <= 24 for b in beams): bk.append('narrow')
    if any(24 < b <= 45 for b in beams): bk.append('mid')
    if any(b > 45 for b in beams): bk.append('wide')
    p['beam_buckets'] = bk
    # форма
    shp = set()
    if p['category'] in ('vstraivaemye', 'nakladnye'):
        for v in vs:
            geo = (v.get('cutout') or '') + ' ' + (v.get('size') or '')
            if re.search(r'2x|2х|2X', v.get('power', '')) or re.search(r'\d+\s*[x×*]\s*\d+', geo.replace('H', '')) and not re.search(r'[ØφD]', geo):
                nums = [int(x) for x in re.findall(r'(\d+)\s*[x×*]\s*(\d+)', geo)[0]] if re.findall(r'(\d+)\s*[x×*]\s*(\d+)', geo) else []
                shp.add('Квадратный' if nums and abs(nums[0] - nums[1]) <= 3 else 'Прямоугольный')
            else:
                shp.add('Круглый')
    p['shape_list'] = sorted(shp)
    # тип модуля (S20) / группа комплектующих
    KIND = {'grill': 'Линейные модули', 'flood': 'Линейные модули', 'wallwasher': 'Линейные модули', 'stick': 'Линейные модули', 'silicone': 'Линейные модули',
            'spot': 'Споты и акценты', 'zoom': 'Споты и акценты', 'folding-spot': 'Споты и акценты', 'convex': 'Споты и акценты', 'reading': 'Споты и акценты',
            'wide': 'Споты и акценты', 'disc': 'Споты и акценты', 'bowl': 'Споты и акценты', 'pendant': 'Подвесные и декоративные', 'glass': 'Подвесные и декоративные',
            'lunar': 'Подвесные и декоративные'}
    kind = ''
    if p['category'] == 'trekovye-s20':
        fam = p['slug'][4:]
        kind = next((val for key, val in KIND.items() if fam.startswith(key)), 'Споты и акценты')
    elif p['category'] == 'shinoprovod-s20':
        kind = 'Питание и управление' if p['slug'] in ('s20-track-power', 's20-track-smart') else ('Соединители' if p['slug'] == 's20-track-connectors' else 'Шинопровод')
    if p['category'] == 'bra':
        sw = ' '.join(v.get('switch', '') for v in vs).lower()
        kind = ('С USB / Type-C' if 'usb' in sw or 'type-c' in sw else 'Для чтения' if 'чтени' in (p.get('lead') or '').lower() or 'изголов' in (p.get('lead') or '').lower()
                else 'Линейные' if p['slug'] in ('wall-210', 'wall-211') else 'Уличное IP65' if p['slug'] == 'wall-600' else 'Декоративные')
    p['kind'] = kind
    p['apps'] = C.applications(p)
    kw = {'trekovye-s20': 'трек трековый магнитный 48v s20 шинопровод', 'shinoprovod-s20': 'шинопровод трек 48v s20 блок питания tuya zigbee',
          'bra': 'бра настенный', 'lineynye': 'линейный профиль ral подвесной', 'nakladnye': 'накладной цилиндр панель потолочный',
          'vstraivaemye': 'встраиваемый даунлайт точечный спот downlight'}[p['category']]
    p['search'] = ' '.join([p['name'], p['slug'], p['line'], cat_names[p['category']], p['mounting'], kw, lead,
                            ' '.join('ip%d' % x for x in p['ip_list']), ' '.join('%dk' % x for x in p['cct_list']),
                            ' '.join(v['sku'] for v in vs), ' '.join(v.get('switch', '') for v in vs), ' '.join(v.get('model', '') for v in vs)]).lower()
    p['order'] = i

by_cat = {c: [p for p in products if p['category'] == c] for c in C.CAT_ORDER}
cats = []
for c in C.CAT_ORDER:
    ps = by_cat[c]
    cc = dict(C.CATEGORIES[c])
    cc['slug'] = c
    cc['n_series'] = len(ps)
    cc['n_sku'] = sum(len(p['variants']) for p in ps)
    cc['price_min'] = min([p['price_min'] for p in ps if p['price_min']] or [0])
    cc['img'] = media[cc['img']] or (ps[0]['images'][0] if ps and ps[0]['images'] else None)
    cats.append(cc)
TOTAL_SKU = sum(len(p['variants']) for p in products)
TOTAL_SERIES = len(products)

# ---------------------------------------------------------------- рендер
pages = []  # (path, priority)
ORG = {'@context': 'https://schema.org', '@type': 'Organization', 'name': 'ADALIGHT', 'legalName': C.SITE['legal'], 'url': SITE_URL + '/',
       'logo': SITE_URL + '/assets/logo-dark.png', 'email': C.SITE['email'], 'telephone': C.SITE['phone_raw'], 'foundingDate': '2024-02',
       'taxID': C.SITE['inn'], 'address': {'@type': 'PostalAddress', 'streetAddress': 'ул. 40 лет Октября, д. 3А, офис 410', 'addressLocality': 'Москва, Щербинка', 'postalCode': '108851', 'addressCountry': 'RU'}}


def crumbs_ld(items):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE_URL + u.replace(BASE, '', 1) if u.startswith(BASE) else SITE_URL + u} for i, (n, u) in enumerate(items)]}


def faq_ld(items):
    return {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': re.sub('<[^>]+>', '', a)}} for q, a in items]}


COMMON = dict(base=BASE, site_url=SITE_URL + '', S=C.SITE, cats=cats, services=C.SERVICES, total_sku=TOTAL_SKU, total_series=TOTAL_SERIES,
              media=media, year=datetime.date.today().year, ver=VER, endpoint=CFG.get('form_endpoint', ''), metrika=CFG.get('metrika', ''),
              stats=C.STATS, trust=C.TRUST, devs=C.DEVELOPERS, words=C.WORDMARKS, projects=C.PROJECTS, articles=C.ARTICLES, stages=C.STAGES)


def render(tpl, path, prio=0.6, **ctx):
    data = dict(COMMON)
    data.update(ctx)
    data['path'] = path
    data.setdefault('jsonld', [])
    if data.get('crumbs'):
        data['jsonld'] = data['jsonld'] + [crumbs_ld(data['crumbs'])]
    html_out = env.get_template(tpl).render(**data)
    html_out = re.sub(r'\n\s*\n+', '\n', html_out)
    fp = os.path.join(OUT, path.strip('/'), 'index.html') if not path.endswith('.html') else os.path.join(OUT, path.strip('/'))
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    open(fp, 'w', encoding='utf-8').write(html_out)
    if not path.endswith('404.html'):
        pages.append((path, prio))


H = ('Главная', BASE + '/')

render('home.html', '/', 1.0, title='ADALIGHT — проектирование, поставка и монтаж освещения для объектов',
       desc='Светотехнический расчёт, производство светильников по ТЗ, проектные аналоги и поставка для ЖК, офисов, ритейла и HoReCa. 2500+ моделей, гарантия до 5 лет. Москва.',
       faq=C.FAQ_HOME, preload=media['ilinka-5'], og_image='/assets/og.jpg', jsonld=[ORG, faq_ld(C.FAQ_HOME)], section='home')

# каталог
all_lines = []
for p in products:
    if p['line'] not in all_lines:
        all_lines.append(p['line'])


def facets(ps):
    """Фасеты показываем только со значениями, которые реально отсеивают серии
    (значение есть не у всех серий на странице). Иначе кнопка «ничего не меняет»."""
    n = len(ps)

    def useful(vals_of):
        cnt = {}
        for p in ps:
            for v in set(vals_of(p)):
                cnt[v] = cnt.get(v, 0) + 1
        return {v for v, c in cnt.items() if c < n}

    lines = [l for l in all_lines if l in useful(lambda p: [p['line']])]
    mounts = [m for m in dict.fromkeys(p['mount_key'] for p in ps) if m in useful(lambda p: [p['mount_key']])]
    cct = sorted(useful(lambda p: p['cct_list']))
    ip = sorted(useful(lambda p: p['ip_list']))
    bu = useful(lambda p: p['beam_buckets'])
    bm = [(k, nm) for k, nm in [('narrow', 'Узкий ≤24°'), ('mid', 'Средний 30–45°'), ('wide', 'Широкий ≥50°')] if k in bu]
    sh = [x for x in ['Круглый', 'Квадратный', 'Прямоугольный'] if x in useful(lambda p: p['shape_list'])]
    kinds = [x for x in dict.fromkeys(p['kind'] for p in ps if p['kind']) if x in useful(lambda p: [p['kind']] if p['kind'] else [])]
    ctrl = [x for x in ['DIM 3CCT', 'Tuya ZigBee', 'Triac DIM'] if x in useful(lambda p: [o['label'] for o in p['options'][1:]])]
    powers = sorted({p['power_min'] for p in ps if p['power_min']} | {p['power_max'] for p in ps if p['power_max']})
    return dict(facet_lines=lines, facet_mounts=mounts, facet_cct=cct, facet_ip=ip, facet_beam=bm, facet_shape=sh, facet_kind=kinds,
                facet_ctrl=ctrl, has_power=len(powers) > 1, has_price=len({p['price_min'] for p in ps if p['price_min']}) > 1)


render('catalog.html', '/catalog/', 0.9, title=f'Каталог светильников ADALIGHT 2026 — {TOTAL_SKU} артикулов с ценами',
       desc=f'Каталог профессиональных светодиодных светильников: встраиваемые, накладные, линейные, магнитная трековая система S20 48V, бра. {TOTAL_SERIES} серий, фильтры по мощности, CCT, IP.',
       h1='Каталог светильников', intro=f'{TOTAL_SERIES} серий и {TOTAL_SKU} артикулов с характеристиками и ценами РРЦ 2026. Фильтруйте по линейке, типу монтажа, цветовой температуре, защите IP и мощности.',
       items=products, cat=None, hero_img=media['scene-14'], crumbs=[H, ('Каталог', BASE + '/catalog/')], section='catalog', **facets(products))
for cc in cats:
    ps = by_cat[cc['slug']]
    lines_here = [C.LINES[l] for l in ['ECO', 'PRM', 'CLASS A'] if any(p['line'] == l for p in ps)] if cc['slug'] in ('vstraivaemye', 'nakladnye') else []
    render('catalog.html', f"/catalog/{cc['slug']}/", 0.9, title=cc['title'], desc=cc['desc'], h1=cc['name'], intro=cc['intro'], seo=cc['seo'],
           items=ps, cat=cc['slug'], cat_stats=cc, hero_img=media[cc.get('hero_scene', cc['img'] if isinstance(cc['img'], str) else '')] or cc['img'],
           lines_here=lines_here, crumbs=[H, ('Каталог', BASE + '/catalog/'), (cc['short'], BASE + f"/catalog/{cc['slug']}/")], section='catalog', **facets(ps))

# товары
for p in products:
    cc = next(c for c in cats if c['slug'] == p['category'])
    rel = [r for r in by_cat[p['category']] if r['slug'] != p['slug']]
    same = [r for r in rel if r['line'] == p['line']]
    related = (same + [r for r in rel if r not in same])[:4]
    prices = [v['price'] for v in p['variants'] if v.get('price')]
    ld = {'@context': 'https://schema.org', '@type': 'Product', 'name': f"{p['name']} — {cc['name'].lower()}", 'brand': {'@type': 'Brand', 'name': 'ADALIGHT'},
          'sku': p['variants'][0]['sku'], 'description': p['lead_text'], 'category': cc['name'],
          'image': [SITE_URL + i['lg'].replace(BASE, '', 1) for i in p['images'][:3]]}
    if prices:
        ld['offers'] = {'@type': 'AggregateOffer', 'priceCurrency': 'RUB', 'lowPrice': min(prices), 'highPrice': max(prices), 'offerCount': len(prices), 'availability': 'https://schema.org/InStock'}
    title = f"{p['name']} — {cc['short'].lower()} светильник{'и' if cc['slug'] != 'shinoprovod-s20' else ''} {p['line']}".replace('шинопровод s20 светильник', 'шинопровод S20')
    if cc['slug'] == 'shinoprovod-s20':
        title = f"{p['name']} — купить, цены | ADALIGHT"
    elif cc['slug'] == 'bra':
        title = f"Бра {p['name']} — цены, характеристики | ADALIGHT"
    else:
        ln = '' if p['line'].split()[0] in p['name'] else ' ' + p['line']
        title = f"{p['name']}{ln} — {cc['short'].lower()} светильник, цены | ADALIGHT".replace('трековые s20 48v светильник', 'трековый светильник 48V').replace('встраиваемые светильник', 'встраиваемый светильник').replace('накладные светильник', 'накладной светильник').replace('линейные светильник', 'линейный светильник')
    render('product.html', f"/product/{p['slug']}/", 0.7, title=title,
           desc=(p['lead_text'] + (f" Цена от {min(prices)} ₽." if prices else ''))[:300],
           p=p, cat=cc, line=C.LINES.get(p['line'], C.LINES['PRM']), related=related, og_type='product',
           og_image=(p['images'][0]['lg'].replace(BASE, '', 1) if p['images'] else '/assets/og.jpg'),
           crumbs=[H, ('Каталог', BASE + '/catalog/'), (cc['short'], BASE + f"/catalog/{cc['slug']}/"), (p['name'], BASE + f"/product/{p['slug']}/")],
           jsonld=[ld], section='catalog')

render('spec.html', '/spec/', 0.3, title='Спецификация проекта — ADALIGHT', desc='Соберите спецификацию освещения из каталога ADALIGHT, выгрузите CSV и отправьте на расчёт.',
       crumbs=[H, ('Спецификация', BASE + '/spec/')], section='spec')

# проекты
render('projects.html', '/projects/', 0.8, title='Проекты ADALIGHT — освещение жилых комплексов и коммерческих объектов',
       desc='Реализованные проекты: внутреннее освещение МОП, архитектурная подсветка фасадов, освещение благоустройства. ЖК «Ильинка 3/8», Will Towers, «Павелецкая Сити» и другие.',
       crumbs=[H, ('Проекты', BASE + '/projects/')], section='projects')
from PIL import Image as _Im


def _dhash(e):
    im = _Im.open(os.path.join(OUT, e['src'][len(BASE) + 1:])).convert('L').resize((9, 8))
    px = list(im.tobytes())
    return [px[r * 9 + c] > px[r * 9 + c + 1] for r in range(8) for c in range(8)]


def dedupe_imgs(lst):
    out, hs = [], []
    for e in lst:
        h = _dhash(e)
        if any(sum(a != b for a, b in zip(h, o)) <= 10 for o in hs):
            continue
        hs.append(h)
        out.append(e)
    return out


for pr in C.PROJECTS:
    gal = [media[f"{pr['slug']}-{k}"] for k in range(pr['n'])]
    gal = dedupe_imgs([g for g in gal if g])
    others = [o for o in C.PROJECTS if o['slug'] != pr['slug']][:3]
    render('project.html', f"/projects/{pr['slug']}/", 0.7, title=f"{pr['name']} — {pr['type'].lower()} | Проекты ADALIGHT",
           desc=pr['lead'], pr=pr, gallery=gal, others=others, og_image=gal[0]['lg'].replace(BASE, '', 1) if gal else None,
           crumbs=[H, ('Проекты', BASE + '/projects/'), (pr['name'], BASE + f"/projects/{pr['slug']}/")], section='projects')

# услуги
render('services.html', '/services/', 0.8, title='Услуги ADALIGHT — расчёт, оптимизация сметы, производство, поставка, монтаж',
       desc='Полный цикл освещения объекта: светотехнический расчёт, оптимизация сметы и проектные аналоги, производство по ТЗ, комплектация и поставка, монтаж и сервис.',
       crumbs=[H, ('Услуги', BASE + '/services/')], section='services')
for s in C.SERVICES:
    render('service.html', f"/services/{s['slug']}/", 0.8, title=f"{s['name']} — ADALIGHT", desc=s['lead'][:250], s=s,
           crumbs=[H, ('Услуги', BASE + '/services/'), (s['name'], BASE + f"/services/{s['slug']}/")], jsonld=[faq_ld(s['faq'])], section='services')

render('developers.html', '/developers/', 0.9, title='Освещение для девелоперов и генподрядчиков — ADALIGHT',
       desc='Комплектация объектов освещением: проработка сметы, проектные аналоги с проверкой параметров, производство по ТЗ, сроки по позициям до заказа, один ответственный.',
       crumbs=[H, ('Девелоперам', BASE + '/developers/')], section='developers')
render('designers.html', '/designers/', 0.9, title='Освещение для дизайнеров интерьера и архитекторов — ADALIGHT',
       desc='Подбор света по дизайн-проекту, производство по ТЗ, замены без разрушения концепции, Ra ≥ 90, партнёрская программа для дизайн-студий.',
       crumbs=[H, ('Дизайнерам', BASE + '/designers/')], section='designers')
PARTNER_FAQ = [
    ('Кто может стать партнёром?', 'Дизайн-студии, архитектурные бюро, ремонтные и отделочные компании, прорабы и электромонтажные организации, которые комплектуют объекты освещением.'),
    ('Есть ли обязательства по объёму?', 'Нет. Начинаем с одного пилотного объекта — вы оцениваете качество подбора, скорость коммуникации и экономику.'),
    ('Как формируется партнёрская цена?', 'Под объект: зависит от состава спецификации, объёма и условий поставки. Клиентскую наценку вы определяете сами.'),
    ('Как происходят выплаты?', 'По договору, точно в срок. Условия фиксируются до старта работы по объекту.'),
    ('Что если нужной модели нет?', 'Подберём технический аналог по ТТХ, геометрии и визуальному образу и согласуем с вами и клиентом — либо изготовим по ТЗ.'),
    ('Кто отвечает за гарантию?', 'ADALIGHT: замена, обслуживание и ремонт света в одном месте. Гарантия — до 5 лет в зависимости от оборудования.'),
]
render('partners.html', '/partners/', 0.9, title='Партнёрская программа ADALIGHT — для дизайн-студий, ремонтных компаний и архитекторов',
       desc='Освещение, которое увеличивает прибыль: партнёрская цена под объект, ваша наценка, выплаты по договору, производство по ТЗ, замена импорта, один ответственный. Начните с одного объекта.',
       partner_faq=PARTNER_FAQ, jsonld=[faq_ld(PARTNER_FAQ)], og_image='/assets/og-partners.jpg', section='partners',
       preload=media['interior-hero'])
render('engineers.html', '/engineers/', 0.7, title='Проектировщикам — IES, чертежи, паспорта светильников ADALIGHT',
       desc='Материалы для проектирования освещения: IES-файлы, паспорта, габаритные чертежи, каталог с параметрами, калькуляторы освещённости.',
       crumbs=[H, ('Проектировщикам', BASE + '/engineers/')], section='engineers')
render('tools.html', '/tools/', 0.7, title='Калькулятор освещённости и количества светильников — ADALIGHT',
       desc='Онлайн-калькуляторы: сколько светильников нужно на помещение и какую освещённость даёт светильник с заданным углом луча и потоком.',
       crumbs=[H, ('Калькуляторы', BASE + '/tools/')], section='tools')
render('journal.html', '/journal/', 0.6, title='Журнал ADALIGHT — статьи об освещении', desc='Практические статьи об освещении: цветовая температура, IP, угол луча, магнитные трековые системы, оптимизация сметы.',
       crumbs=[H, ('Журнал', BASE + '/journal/')], section='journal')
for a in C.ARTICLES:
    others = [o for o in C.ARTICLES if o['slug'] != a['slug']][:4]
    ld = {'@context': 'https://schema.org', '@type': 'Article', 'headline': a['title'], 'description': a['desc'], 'author': {'@type': 'Organization', 'name': 'ADALIGHT'},
          'publisher': {'@type': 'Organization', 'name': 'ADALIGHT'}, 'datePublished': '2026-09-20'}
    render('article.html', f"/journal/{a['slug']}/", 0.6, title=f"{a['title']} | ADALIGHT", desc=a['desc'], a=a, body=a['body'].replace('{base}', BASE), others=others,
           og_type='article', crumbs=[H, ('Журнал', BASE + '/journal/'), (a['title'][:40] + '…', BASE + f"/journal/{a['slug']}/")], jsonld=[ld], section='journal')
render('about.html', '/about/', 0.6, title='О компании ADALIGHT — ООО «АДАЛАЙТ»', desc='ADALIGHT — российская компания, основанная в 2024 году профессионалами с 15-летним опытом в светодиодном освещении. Проектируем, поставляем и монтируем свет.',
       crumbs=[H, ('О компании', BASE + '/about/')], jsonld=[ORG], section='about')
render('contacts.html', '/contacts/', 0.7, title='Контакты ADALIGHT — телефон, адрес, реквизиты', desc=f"Телефон {C.SITE['phone']}, e-mail {C.SITE['email']}. {C.SITE['address']}. Реквизиты ООО «АДАЛАЙТ».",
       crumbs=[H, ('Контакты', BASE + '/contacts/')], jsonld=[ORG], section='contacts')
render('privacy.html', '/privacy/', 0.1, title='Политика конфиденциальности — ADALIGHT', desc='Политика обработки персональных данных ООО «АДАЛАЙТ».',
       crumbs=[H, ('Политика конфиденциальности', BASE + '/privacy/')])
render('404.html', '/404.html', 0, title='Страница не найдена — ADALIGHT', desc='Страница не найдена.')

# ---------------------------------------------------------------- статика
os.makedirs(os.path.join(OUT, 'assets', 'css'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'assets', 'js'), exist_ok=True)


def min_css(s):
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\s*([{}:;,>])\s*', r'\1', s)
    return s.replace(';}', '}').strip()


def min_js(s):
    # безопасная минимизация: только комментарии-строки в начале и ведущие пробелы
    s = re.sub(r'^\s*/\*.*?\*/\s*', '', s, flags=re.S)
    s = '\n'.join(l.strip() for l in s.split('\n') if l.strip() and not l.strip().startswith('//'))
    return s


open(os.path.join(OUT, 'assets', 'css', 'main.css'), 'w', encoding='utf-8').write(min_css(open(os.path.join(ROOT, 'src', 'css', 'main.css'), encoding='utf-8').read()))
for f in os.listdir(os.path.join(ROOT, 'src', 'js')):
    open(os.path.join(OUT, 'assets', 'js', f), 'w', encoding='utf-8').write(min_js(open(os.path.join(ROOT, 'src', 'js', f), encoding='utf-8').read()))

today = datetime.date.today().isoformat()
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for path, prio in pages:
    sm.append(f'<url><loc>{SITE_URL}{path}</loc><lastmod>{today}</lastmod><priority>{prio:.1f}</priority></url>')
sm.append('</urlset>')
open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8').write('\n'.join(sm))
open(os.path.join(OUT, 'robots.txt'), 'w', encoding='utf-8').write(f"User-agent: *\nAllow: /\nDisallow: {BASE}/spec/\n\nSitemap: {SITE_URL}/sitemap.xml\n")
open(os.path.join(OUT, 'site.webmanifest'), 'w', encoding='utf-8').write(json.dumps({'name': 'ADALIGHT', 'short_name': 'ADALIGHT', 'start_url': BASE + '/', 'display': 'standalone',
    'background_color': '#0d0d0e', 'theme_color': '#0d0d0e', 'icons': [{'src': BASE + '/assets/icon-192.png', 'sizes': '192x192', 'type': 'image/png'}, {'src': BASE + '/assets/icon-512.png', 'sizes': '512x512', 'type': 'image/png'}]}, ensure_ascii=False))
open(os.path.join(OUT, '.nojekyll'), 'w').write('')
if CFG.get('cname'):
    open(os.path.join(OUT, 'CNAME'), 'w').write(CFG['cname'])
print('pages:', len(pages) + 1, 'sku:', TOTAL_SKU, 'series:', TOTAL_SERIES)

# проверка синтаксиса JS после сборки (защита от поломки при минификации)
import subprocess
for f in os.listdir(os.path.join(OUT, 'assets', 'js')):
    r = subprocess.run(['node', '--check', os.path.join(OUT, 'assets', 'js', f)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        raise SystemExit('JS syntax error in ' + f + '\n' + r.stderr)
print('js ok')

# проверка CSS: баланс скобок и отсутствие «висящих» селекторов
_css = re.sub(r'/\*.*?\*/', '', open(os.path.join(ROOT, 'src', 'css', 'main.css'), encoding='utf-8').read(), flags=re.S)
_d = 0
for _i, _l in enumerate(_css.split('\n'), 1):
    _d += _l.count('{') - _l.count('}')
    if _d < 0 or (_d == 0 and _l.strip() and not _l.strip().endswith('}')):
        raise SystemExit(f'CSS error near line {_i}: {_l[:80]}')
print('css ok')
