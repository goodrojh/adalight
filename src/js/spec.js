/* Страница «Спецификация»: список из localStorage, количество, сумма РРЦ, CSV, печать */
(function () {
  'use strict';
  var d = document, S = window.ADASpec, fmt = window.ADAfmt, root = d.querySelector('[data-spec]');
  if (!root || !S) return;
  var body = root.querySelector('tbody'), tot = root.querySelector('[data-total]'), n = root.querySelector('[data-lines]');
  var full = root.querySelector('[data-full]'), emptyEl = d.querySelector('[data-spec-empty]'), base = (window.ADA || {}).base || '';
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function render() {
    var a = S.all();
    full.hidden = !a.length; emptyEl.hidden = !!a.length;
    body.innerHTML = a.map(function (x, i) {
      return '<tr><td style="width:64px">' + (x.img ? '<img src="' + esc(x.img) + '" alt="" width="56" height="56" style="width:56px;height:56px;object-fit:contain;background:#f3f3f1;border-radius:8px;mix-blend-mode:multiply">' : '') + '</td>' +
        '<td><a href="' + base + '/product/' + esc(x.slug) + '/" style="font-weight:600;text-decoration:none">' + esc(x.name) + '</a><div class="mono muted" style="font-size:12px">' + esc(x.sku) + (x.opt ? ' · ' + esc(x.opt) : '') + '</div>' + (x.params ? '<div class="note">' + esc(x.params) + '</div>' : '') + '</td>' +
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
  d.querySelector('[data-csv]').addEventListener('click', function () {
    var rows = [['Артикул', 'Наименование', 'Опция', 'Кол-во', 'РРЦ, ₽', 'Сумма, ₽']].concat(S.all().map(function (x) { return [x.sku, x.name, x.opt || '', x.qty, x.price || '', (x.price || 0) * x.qty]; }));
    var csv = '﻿' + rows.map(function (r) { return r.map(function (c) { return '"' + String(c).replace(/"/g, '""') + '"'; }).join(';'); }).join('\r\n');
    var url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    var l = d.createElement('a'); l.href = url; l.download = 'ADALIGHT-specifikaciya.csv'; d.body.appendChild(l); l.click(); l.remove(); setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    window.ADAgoal && window.ADAgoal('spec_csv');
  });
  d.querySelector('[data-print]').addEventListener('click', function () { window.print(); });
  render();
})();
