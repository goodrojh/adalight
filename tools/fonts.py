# -*- coding: utf-8 -*-
"""Скачивает шрифты Geologica и Onest (woff2, кириллица+латиница) в src/fonts и пишет src/fonts/fonts.css.
Шрифты отдаются с нашего домена — без передачи IP посетителей в Google (152-ФЗ, трансграничная передача)."""
import os, re, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'src', 'fonts'); os.makedirs(OUT, exist_ok=True)
URL = 'https://fonts.googleapis.com/css2?family=Geologica:wght@300;400;500;600&family=Onest:wght@400;500;600;700&display=swap'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
css = urllib.request.urlopen(urllib.request.Request(URL, headers={'User-Agent': UA})).read().decode()
out = []
for sub, block in re.findall(r'/\* ([\w-]+) \*/\s*(@font-face \{.*?\})', css, re.S):
    if sub not in ('cyrillic', 'latin', 'cyrillic-ext', 'latin-ext'):
        continue
    fam = re.search(r"font-family: '([^']+)'", block).group(1)
    w = re.search(r'font-weight: (\d+)', block).group(1)
    url = re.search(r'url\((https://[^)]+\.woff2)\)', block).group(1)
    name = f'{fam.lower()}-{w}-{sub}.woff2'
    p = os.path.join(OUT, name)
    if not os.path.exists(p):
        open(p, 'wb').write(urllib.request.urlopen(url).read())
    out.append(block.replace(url, 'FONTBASE/' + name))
open(os.path.join(OUT, 'fonts.css'), 'w', encoding='utf-8').write('\n'.join(out))
print(len(out), 'faces')
