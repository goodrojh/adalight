/* Страница «Спецификация»: список из localStorage, количество, сумма РРЦ,
   фирменный документ для печати/PDF и Excel (.xlsx) с оформлением — без сторонних библиотек */
(function () {
  'use strict';
  var d = document, S = window.ADASpec, fmt = window.ADAfmt, root = d.querySelector('[data-spec]');
  if (!root || !S) return;
  var C = window.ADA || {}, base = C.base || '';
  var body = root.querySelector('tbody'), tot = root.querySelector('[data-total]'), n = root.querySelector('[data-lines]');
  var full = root.querySelector('[data-full]'), emptyEl = d.querySelector('[data-spec-empty]');
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function abs(u) { return u ? new URL(u, location.href).href : ''; }
  function docNo() { var t = new Date(), p = function (x) { return String(x).padStart(2, '0'); }; return 'ADA-' + String(t.getFullYear()).slice(2) + p(t.getMonth() + 1) + p(t.getDate()) + '-' + p(t.getHours()) + p(t.getMinutes()); }
  function today() { return new Date().toLocaleDateString('ru-RU', { day: '2-digit', month: 'long', year: 'numeric' }); }

  function render() {
    var a = S.all();
    full.hidden = !a.length; emptyEl.hidden = !!a.length;
    body.innerHTML = a.map(function (x, i) {
      return '<tr><td style="width:64px">' + (x.img ? '<img src="' + esc(x.img) + '" alt="" width="56" height="56" style="width:56px;height:56px;object-fit:contain;background:#f3f3f1;border-radius:8px;mix-blend-mode:multiply">' : '') + '</td>' +
        '<td><a href="' + base + '/product/' + esc(x.slug) + '/" style="font-weight:600;text-decoration:none">' + esc(x.name) + '</a><div class="muted" style="font-size:13px">' + esc(x.sku) + (x.opt ? ' · ' + esc(x.opt) : '') + '</div>' + (x.params ? '<div class="note">' + esc(x.params) + '</div>' : '') + '</td>' +
        '<td class="m">' + (x.price ? fmt(x.price) : 'по запросу') + '</td>' +
        '<td><div class="qty"><button type="button" data-d="-1" data-i="' + i + '" aria-label="Меньше">−</button><input type="number" min="1" value="' + x.qty + '" data-i="' + i + '" aria-label="Количество"><button type="button" data-d="1" data-i="' + i + '" aria-label="Больше">+</button></div></td>' +
        '<td class="m">' + (x.price ? fmt(x.price * x.qty) : '—') + '</td>' +
        '<td><button class="rm" type="button" data-rm="' + i + '" aria-label="Удалить">×</button></td></tr>';
    }).join('');
    var sum = a.reduce(function (s, x) { return s + (x.price || 0) * x.qty; }, 0);
    tot.textContent = fmt(sum); n.textContent = a.length + ' поз. · ' + S.count() + ' шт.';
    var ta = d.querySelector('[name=spec_text]'); if (ta) ta.value = a.map(function (x) { return x.sku + (x.opt ? ' [' + x.opt + ']' : '') + ' × ' + x.qty; }).join('\n');
  }
  root.addEventListener('click', function (e) {
    var a = S.all(), b = e.target.closest('button'); if (!b) return;
    if (b.dataset.rm != null) { a.splice(+b.dataset.rm, 1); S.save(a); render(); }
    if (b.dataset.d) { var x = a[+b.dataset.i]; x.qty = Math.max(1, x.qty + +b.dataset.d); S.save(a); render(); }
  });
  root.addEventListener('change', function (e) {
    if (e.target.matches('input[data-i]')) { var a = S.all(); a[+e.target.dataset.i].qty = Math.max(1, parseInt(e.target.value, 10) || 1); S.save(a); render(); }
  });
  d.querySelector('[data-clear]').addEventListener('click', function () { if (confirm('Очистить спецификацию?')) { S.save([]); render(); } });

  /* ---------- фирменный документ: печать / сохранить в PDF ---------- */
  function printDoc() {
    var a = S.all(); if (!a.length) return;
    var sum = a.reduce(function (s, x) { return s + (x.price || 0) * x.qty; }, 0), no = docNo();
    var rows = a.map(function (x, i) {
      return '<tr><td class="c">' + (i + 1) + '</td><td class="ph">' + (x.img ? '<img src="' + esc(abs(x.img)) + '" alt="">' : '') + '</td>' +
        '<td><b>' + esc(x.name) + '</b><div class="sku">' + esc(x.sku) + (x.opt ? ' · ' + esc(x.opt) : '') + '</div>' + (x.params ? '<div class="par">' + esc(x.params) + '</div>' : '') + '</td>' +
        '<td class="c">' + x.qty + '</td><td class="r">' + (x.price ? fmt(x.price) : 'по запросу') + '</td><td class="r"><b>' + (x.price ? fmt(x.price * x.qty) : '—') + '</b></td></tr>';
    }).join('');
    var html = '<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Спецификация ' + no + ' — ADALIGHT</title>' +
      '<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Geologica:wght@500;600&family=Onest:wght@400;500;600&display=swap" rel="stylesheet">' +
      '<style>@page{size:A4;margin:14mm 12mm 16mm}*{box-sizing:border-box}body{margin:0;font:400 12px/1.45 Onest,Arial,sans-serif;color:#141416;-webkit-print-color-adjust:exact;print-color-adjust:exact}' +
      '.top{display:flex;justify-content:space-between;align-items:flex-start;padding-bottom:14px;border-bottom:3px solid #ffc603}.top img{height:34px}.co{text-align:right;font-size:10.5px;color:#5d5d63;line-height:1.55}.co b{color:#141416;font-size:12px}' +
      'h1{font:600 22px/1.2 Geologica,Arial,sans-serif;margin:22px 0 4px}.meta{display:flex;gap:28px;color:#5d5d63;margin-bottom:18px}.meta b{color:#141416;font-weight:600}' +
      'table{width:100%;border-collapse:collapse}th{background:#0d0d0e;color:#fff;font-weight:500;font-size:10.5px;text-align:left;padding:8px}th.r,td.r{text-align:right}th.c,td.c{text-align:center}' +
      'td{padding:8px;border-bottom:1px solid #e3e3df;vertical-align:middle}tr:nth-child(even) td{background:#f7f7f5}td.ph{width:52px}td.ph img{width:44px;height:44px;object-fit:contain;display:block}.sku{color:#5d5d63;font-size:10.5px;margin-top:2px}.par{color:#8a8a90;font-size:10px}' +
      '.tot td{border:0;background:#fff!important;padding-top:12px}.tot .lab{text-align:right;color:#5d5d63}.tot .val{font:600 16px Geologica,Arial,sans-serif;text-align:right;white-space:nowrap}.tot .val span{background:#ffc603;padding:4px 10px;border-radius:4px}' +
      '.note{margin-top:18px;padding:12px 14px;border-left:3px solid #ffc603;background:#f7f7f5;font-size:11px;color:#3b3b40}.foot{position:fixed;bottom:0;left:0;right:0;display:flex;justify-content:space-between;font-size:9.5px;color:#8a8a90;border-top:1px solid #e3e3df;padding-top:6px}' +
      'thead{display:table-header-group}tr{page-break-inside:avoid}</style></head><body>' +
      '<div class="top"><img src="' + abs(base + '/assets/logo-dark.svg') + '" alt="ADALIGHT"><div class="co"><b>ООО «АДАЛАЙТ»</b><br>ИНН 9718249142 · ОГРН 1247700171762<br>Москва, Щербинка, ул. 40 лет Октября, д. 3А, офис 410<br>+7 (977) 109-39-10 · damir@adalight.ru · adalight.ru</div></div>' +
      '<h1>Спецификация оборудования</h1><div class="meta"><span>№ <b>' + no + '</b></span><span>Дата: <b>' + today() + '</b></span><span>Позиций: <b>' + a.length + '</b> · штук: <b>' + S.count() + '</b></span></div>' +
      '<table><thead><tr><th class="c">№</th><th></th><th>Наименование и артикул</th><th class="c">Кол-во</th><th class="r">Цена РРЦ</th><th class="r">Сумма</th></tr></thead><tbody>' + rows + '</tbody>' +
      '<tbody class="tot"><tr><td colspan="5" class="lab">Итого по РРЦ:</td><td class="val"><span>' + fmt(sum) + '</span></td></tr></tbody></table>' +
      '<div class="note">Цены указаны по рекомендованному розничному прайсу ADALIGHT 2026. Для проектных закупок и партнёров стоимость и сроки поставки рассчитываются под объект — отправьте спецификацию менеджеру.</div>' +
      '<div class="foot"><span>ADALIGHT — проектируем, поставляем и монтируем свет</span><span>' + no + '</span></div>' +
      '<script>window.onload=function(){setTimeout(function(){window.print()},400)}<\/script></body></html>';
    var w = window.open('', '_blank');
    if (!w) { window.print(); return; }
    w.document.open(); w.document.write(html); w.document.close();
    window.ADAgoal && window.ADAgoal('spec_print');
  }
  d.querySelector('[data-print]').addEventListener('click', printDoc);

  /* ---------- Excel .xlsx: минимальный генератор (ZIP без сжатия + SpreadsheetML) ---------- */
  var crcT = (function () { var t = [], c; for (var n = 0; n < 256; n++) { c = n; for (var k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
  function crc32(u8) { var c = 0xFFFFFFFF; for (var i = 0; i < u8.length; i++) c = crcT[(c ^ u8[i]) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
  function zip(files) {
    var enc = new TextEncoder(), parts = [], central = [], off = 0;
    files.forEach(function (f) {
      var name = enc.encode(f.name), data = enc.encode(f.data), crc = crc32(data);
      var h = new DataView(new ArrayBuffer(30));
      h.setUint32(0, 0x04034b50, true); h.setUint16(4, 20, true); h.setUint16(6, 0x0800, true); h.setUint16(8, 0, true);
      h.setUint32(14, crc, true); h.setUint32(18, data.length, true); h.setUint32(22, data.length, true); h.setUint16(26, name.length, true);
      parts.push(new Uint8Array(h.buffer), name, data);
      var c = new DataView(new ArrayBuffer(46));
      c.setUint32(0, 0x02014b50, true); c.setUint16(4, 20, true); c.setUint16(6, 20, true); c.setUint16(8, 0x0800, true);
      c.setUint32(16, crc, true); c.setUint32(20, data.length, true); c.setUint32(24, data.length, true); c.setUint16(28, name.length, true); c.setUint32(42, off, true);
      central.push(new Uint8Array(c.buffer), name);
      off += 30 + name.length + data.length;
    });
    var cl = central.reduce(function (s, x) { return s + x.length; }, 0);
    var e = new DataView(new ArrayBuffer(22));
    e.setUint32(0, 0x06054b50, true); e.setUint16(8, files.length, true); e.setUint16(10, files.length, true); e.setUint32(12, cl, true); e.setUint32(16, off, true);
    return new Blob(parts.concat(central, [new Uint8Array(e.buffer)]), { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  }
  function xesc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function xlsx() {
    var a = S.all(); if (!a.length) return;
    var no = docNo(), R = [], r = 0;
    function cell(col, row, v, st, f) {
      var ref = col + row;
      if (f) return '<c r="' + ref + '" s="' + st + '"><f>' + f + '</f><v>' + (v || 0) + '</v></c>';
      if (typeof v === 'number') return '<c r="' + ref + '" s="' + st + '"><v>' + v + '</v></c>';
      return '<c r="' + ref + '" s="' + st + '" t="inlineStr"><is><t xml:space="preserve">' + xesc(v) + '</t></is></c>';
    }
    R.push('<row r="1" ht="30" customHeight="1">' + cell('A', 1, 'ADALIGHT — спецификация оборудования', 1) + '</row>');
    R.push('<row r="2">' + cell('A', 2, '№ ' + no + ' от ' + today() + ' · ООО «АДАЛАЙТ», ИНН 9718249142 · +7 (977) 109-39-10 · damir@adalight.ru', 2) + '</row>');
    R.push('<row r="4" ht="24" customHeight="1">' + ['№', 'Артикул', 'Наименование', 'Параметры', 'Исполнение', 'Кол-во, шт.', 'Цена РРЦ, ₽', 'Сумма, ₽'].map(function (h, i) { return cell('ABCDEFGH'[i], 4, h, 3); }).join('') + '</row>');
    a.forEach(function (x, i) {
      r = 5 + i; var z = i % 2 ? 1 : 0;
      R.push('<row r="' + r + '" ht="22" customHeight="1">' + cell('A', r, i + 1, 6 + z * 10) + cell('B', r, x.sku, 4 + z * 10) + cell('C', r, x.name, 4 + z * 10) + cell('D', r, x.params || '', 4 + z * 10) +
        cell('E', r, x.opt || '—', 4 + z * 10) + cell('F', r, x.qty, 6 + z * 10) + (x.price ? cell('G', r, x.price, 5 + z * 10) : cell('G', r, 'по запросу', 4 + z * 10)) +
        cell('H', r, (x.price || 0) * x.qty, 5 + z * 10, x.price ? 'F' + r + '*G' + r : null) + '</row>');
    });
    var last = 4 + a.length, tr = last + 1, total = a.reduce(function (s, x) { return s + (x.price || 0) * x.qty; }, 0);
    R.push('<row r="' + tr + '" ht="24" customHeight="1">' + cell('G', tr, 'Итого:', 7) + cell('H', tr, total, 8, 'SUM(H5:H' + last + ')') + '</row>');
    R.push('<row r="' + (tr + 2) + '">' + cell('A', tr + 2, 'Цены — рекомендованные розничные ADALIGHT 2026. Партнёрская цена и сроки поставки рассчитываются под объект.', 9) + '</row>');
    var sheet = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">' +
      '<sheetPr><pageSetUpPr fitToPage="1"/></sheetPr><sheetViews><sheetView workbookViewId="0" showGridLines="0"><pane ySplit="4" topLeftCell="A5" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>' +
      '<cols><col min="1" max="1" width="6" customWidth="1"/><col min="2" max="2" width="30" customWidth="1"/><col min="3" max="3" width="28" customWidth="1"/><col min="4" max="4" width="38" customWidth="1"/><col min="5" max="5" width="16" customWidth="1"/><col min="6" max="6" width="12" customWidth="1"/><col min="7" max="8" width="16" customWidth="1"/></cols>' +
      '<sheetData>' + R.join('') + '</sheetData><mergeCells count="3"><mergeCell ref="A1:H1"/><mergeCell ref="A2:H2"/><mergeCell ref="A' + (tr + 2) + ':H' + (tr + 2) + '"/></mergeCells>' +
      '<pageMargins left="0.5" right="0.5" top="0.6" bottom="0.6" header="0.3" footer="0.3"/><pageSetup paperSize="9" orientation="landscape" fitToWidth="1" fitToHeight="0"/></worksheet>';
    var bord = '<border><left style="thin"><color rgb="FFDCDCD6"/></left><right style="thin"><color rgb="FFDCDCD6"/></right><top style="thin"><color rgb="FFDCDCD6"/></top><bottom style="thin"><color rgb="FFDCDCD6"/></bottom><diagonal/></border>';
    // стили: 0 обычный,1 заголовок,2 подзаголовок,3 шапка,4 текст,5 деньги,6 число по центру,7 «Итого»,8 сумма итого,9 примечание; 14-16 = 4-6 с заливкой зебры
    var xf = function (font, fill, border, numFmt, align) { return '<xf numFmtId="' + numFmt + '" fontId="' + font + '" fillId="' + fill + '" borderId="' + border + '" applyFont="1" applyFill="1" applyBorder="1"' + (numFmt ? ' applyNumberFormat="1"' : '') + ' applyAlignment="1"><alignment ' + align + '/></xf>'; };
    var cellXfs = [
      xf(0, 0, 0, 0, 'vertical="center"'), xf(1, 0, 0, 0, 'vertical="center"'), xf(2, 0, 0, 0, 'vertical="center"'),
      xf(3, 2, 1, 0, 'horizontal="center" vertical="center" wrapText="1"'), xf(0, 0, 1, 0, 'vertical="center" wrapText="1"'),
      xf(0, 0, 1, 164, 'horizontal="right" vertical="center"'), xf(0, 0, 1, 0, 'horizontal="center" vertical="center"'),
      xf(4, 0, 0, 0, 'horizontal="right" vertical="center"'), xf(4, 3, 1, 164, 'horizontal="right" vertical="center"'), xf(2, 0, 0, 0, 'vertical="center" wrapText="1"'),
      xf(0, 0, 0, 0, ''), xf(0, 0, 0, 0, ''), xf(0, 0, 0, 0, ''), xf(0, 0, 0, 0, ''),
      xf(0, 4, 1, 0, 'vertical="center" wrapText="1"'), xf(0, 4, 1, 164, 'horizontal="right" vertical="center"'), xf(0, 4, 1, 0, 'horizontal="center" vertical="center"')
    ];
    var styles = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">' +
      '<numFmts count="1"><numFmt numFmtId="164" formatCode="#,##0 &quot;₽&quot;"/></numFmts>' +
      '<fonts count="5"><font><sz val="11"/><name val="Arial"/></font><font><b/><sz val="16"/><color rgb="FF0D0D0E"/><name val="Arial"/></font><font><sz val="9"/><color rgb="FF5D5D63"/><name val="Arial"/></font><font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Arial"/></font><font><b/><sz val="12"/><name val="Arial"/></font></fonts>' +
      '<fills count="5"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF0D0D0E"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFFFC603"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFF7F7F5"/></patternFill></fill></fills>' +
      '<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border>' + bord + '</borders>' +
      '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="' + cellXfs.length + '">' + cellXfs.join('') + '</cellXfs></styleSheet>';
    var blob = zip([
      { name: '[Content_Types].xml', data: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>' },
      { name: '_rels/.rels', data: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>' },
      { name: 'xl/workbook.xml', data: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Спецификация" sheetId="1" r:id="rId1"/></sheets><definedNames><definedName name="_xlnm.Print_Titles" localSheetId="0">\'Спецификация\'!$4:$4</definedName></definedNames></workbook>' },
      { name: 'xl/_rels/workbook.xml.rels', data: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>' },
      { name: 'xl/styles.xml', data: styles },
      { name: 'xl/worksheets/sheet1.xml', data: sheet }
    ]);
    var url = URL.createObjectURL(blob), l = d.createElement('a');
    l.href = url; l.download = 'ADALIGHT-specifikaciya-' + no + '.xlsx'; d.body.appendChild(l); l.click(); l.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1500);
    window.ADAgoal && window.ADAgoal('spec_xlsx');
  }
  window.ADAxlsx = xlsx;
  d.querySelector('[data-xlsx]').addEventListener('click', xlsx);
  render();
})();
