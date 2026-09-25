# -*- coding: utf-8 -*-
"""Читает файл «карта фото» с отметками заказчика и печатает сводку решений.
python read_decisions.py <файл.html>  -> data/decisions.json"""
import json, os, re, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
h = open(sys.argv[1], encoding='utf-8').read()
dec = json.loads(re.search(r'<script id="decisions" type="application/json">(.*?)</script>', h, re.S).group(1) or '{}')
meta = json.loads(re.search(r'<script id="meta" type="application/json">(.*?)</script>', h, re.S).group(1))
out = {'saved': dec.get('saved'), 'drop': dec.get('drop', []), 'comments': dec.get('comments', {}), 'photos': []}
for fid, v in dec.get('photos', {}).items():
    if v in ('keep', 'skip', ''):
        continue
    out['photos'].append(dict(meta.get(fid, {}), id=fid, action=v))
json.dump(out, open(os.path.join(ROOT, 'data', 'decisions.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('сохранено', out['saved'], '| действия по фото:', dict(Counter(p['action'] for p in out['photos'])),
      '| убрать товары:', out['drop'], '| комментарии:', len(out['comments']))
