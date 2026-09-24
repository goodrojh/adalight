# ADALIGHT — сайт компании

Статический многостраничный сайт (157 страниц): каталог 115 серий / 419 артикулов, партнёрская программа, услуги, проекты, журнал.

## Структура
- `docs/` — готовый сайт (GitHub Pages публикует эту папку)
- `templates/` — шаблоны Jinja2, `src/` — CSS/JS, `tools/` — сборка
- `data/products.json` — база товаров (генерируется из прайса), `data/media.json` — изображения
- `site.config.json` — адрес сайта, endpoint форм, ID Яндекс.Метрики

## Сборка
```bash
pip install xlrd jinja2 pillow openpyxl resvg-py
python tools/extract.py   # прайс .xls + фото -> data/products_raw.json
python tools/images.py    # оптимизация фото -> docs/img (WebP)
python tools/brand.py     # иконки, OG-картинки
python tools/build.py     # HTML -> docs/
```

## Подключение заявок и аналитики
В `site.config.json`:
- `form_endpoint` — URL обработчика заявок (CRM/вебхук, принимает JSON). Пока пусто — формы открывают письмо на damir@adalight.ru.
- `metrika` — номер счётчика Яндекс.Метрики (цели: lead, lead_*, spec_add, spec_csv, click_phone, click_email, click_whatsapp).
- `base`/`site_url`/`cname` — при переезде на домен adalight.ru: `base: ""`, `site_url: "https://adalight.ru"`, `cname: "adalight.ru"`.
