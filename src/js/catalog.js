/* Фильтры каталога: карточки отрендерены на сервере (SEO), здесь только показ/скрытие + URL-состояние */
(function () {
  'use strict';
  var d = document, root = d.querySelector('[data-catalog]');
  if (!root) return;
  var $$ = function (s, r) { return Array.prototype.slice.call((r || d).querySelectorAll(s)); };
  var cards = $$('.pcard', root).map(function (el) {
    return { el: el, cat: el.dataset.cat, line: el.dataset.line, mount: el.dataset.mount, cct: (el.dataset.cct || '').split(' ').filter(Boolean),
      ip: (el.dataset.ip || '').split(' ').filter(Boolean), pmin: +el.dataset.pmin || 0, pmax: +el.dataset.pmax || 0,
      price: +el.dataset.price || 0, q: (el.dataset.q || '').toLowerCase(), order: +el.dataset.order };
  });
  var grid = d.querySelector('.pgrid', root), count = d.querySelector('[data-count]'), empty = d.querySelector('[data-empty]');
  var state = { cat: [], line: [], mount: [], cct: [], ip: [], wmin: '', wmax: '', q: '', sort: 'default' };
  var keys = ['cat', 'line', 'mount', 'cct', 'ip'];

  function fromURL() {
    var p = new URLSearchParams(location.search);
    keys.forEach(function (k) { state[k] = p.get(k) ? p.get(k).split(',') : state[k]; });
    state.q = p.get('q') || ''; state.wmin = p.get('wmin') || ''; state.wmax = p.get('wmax') || ''; state.sort = p.get('sort') || 'default';
  }
  function toURL() {
    var p = new URLSearchParams();
    keys.forEach(function (k) { if (state[k].length) p.set(k, state[k].join(',')); });
    if (state.q) p.set('q', state.q); if (state.wmin) p.set('wmin', state.wmin); if (state.wmax) p.set('wmax', state.wmax);
    if (state.sort !== 'default') p.set('sort', state.sort);
    var s = p.toString(); history.replaceState(null, '', location.pathname + (s ? '?' + s : ''));
  }
  function match(c, skip) {
    if (skip !== 'cat' && state.cat.length && state.cat.indexOf(c.cat) < 0) return false;
    if (skip !== 'line' && state.line.length && state.line.indexOf(c.line) < 0) return false;
    if (skip !== 'mount' && state.mount.length && state.mount.indexOf(c.mount) < 0) return false;
    if (skip !== 'cct' && state.cct.length && !state.cct.some(function (x) { return c.cct.indexOf(x) > -1; })) return false;
    if (skip !== 'ip' && state.ip.length && !state.ip.some(function (x) { return c.ip.indexOf(x) > -1; })) return false;
    if (state.wmin && c.pmax && c.pmax < +state.wmin) return false;
    if (state.wmax && c.pmin && c.pmin > +state.wmax) return false;
    if (state.q) { var words = state.q.toLowerCase().split(/\s+/); if (!words.every(function (w) { return c.q.indexOf(w) > -1; })) return false; }
    return true;
  }
  function apply() {
    var vis = cards.filter(function (c) { return match(c); });
    cards.forEach(function (c) { c.el.hidden = vis.indexOf(c) < 0; });
    var sorted = cards.slice().sort(function (a, b) {
      if (state.sort === 'price') return (a.price || 1e9) - (b.price || 1e9);
      if (state.sort === 'price-d') return (b.price || 0) - (a.price || 0);
      if (state.sort === 'power') return a.pmin - b.pmin;
      return a.order - b.order;
    });
    sorted.forEach(function (c) { grid.appendChild(c.el); });
    count.textContent = vis.length + ' ' + plural(vis.length, ['серия', 'серии', 'серий']) + ' · ' + (function (n) { return n + ' ' + plural(n, ['артикул', 'артикула', 'артикулов']); })(vis.reduce(function (s, c) { return s + (+c.el.dataset.skus || 0); }, 0));
    empty.hidden = vis.length > 0;
    // счётчики на чипах (фасеты)
    $$('[data-f]', root).forEach(function (b) {
      var k = b.dataset.f, v = b.dataset.v;
      var n = cards.filter(function (c) {
        if (!match(c, k)) return false;
        if (k === 'cct' || k === 'ip') return c[k].indexOf(v) > -1;
        return c[k] === v;
      }).length;
      var sm = b.querySelector('small'); if (sm) sm.textContent = n;
      b.setAttribute('aria-pressed', state[k].indexOf(v) > -1);
      b.disabled = n === 0 && state[k].indexOf(v) < 0;
      b.style.opacity = b.disabled ? .4 : '';
    });
    var fb = d.querySelector('[data-fcount]');
    if (fb) { var n = keys.reduce(function (s, k) { return s + state[k].length; }, 0) + (state.wmin ? 1 : 0) + (state.wmax ? 1 : 0); fb.textContent = n ? '(' + n + ')' : ''; }
    toURL();
  }
  function plural(n, f) { var m10 = n % 10, m100 = n % 100; return f[(m10 === 1 && m100 !== 11) ? 0 : (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) ? 1 : 2]; }

  $$('[data-f]', root).forEach(function (b) {
    b.addEventListener('click', function () {
      var k = b.dataset.f, v = b.dataset.v, i = state[k].indexOf(v);
      if (i > -1) state[k].splice(i, 1); else state[k].push(v);
      apply();
    });
  });
  var q = d.querySelector('[data-q]'), t;
  if (q) q.addEventListener('input', function () { clearTimeout(t); t = setTimeout(function () { state.q = q.value.trim(); apply(); }, 120); });
  var wmin = d.querySelector('[data-wmin]'), wmax = d.querySelector('[data-wmax]');
  [wmin, wmax].forEach(function (el) { el && el.addEventListener('input', function () { state.wmin = wmin.value; state.wmax = wmax.value; apply(); }); });
  var sort = d.querySelector('[data-sort]');
  sort && sort.addEventListener('change', function () { state.sort = sort.value; apply(); });
  $$('[data-reset]').forEach(function (b) {
    b.addEventListener('click', function () {
      keys.forEach(function (k) { state[k] = []; }); state.q = ''; state.wmin = state.wmax = '';
      if (q) q.value = ''; if (wmin) wmin.value = ''; if (wmax) wmax.value = ''; apply();
    });
  });
  var fp = d.querySelector('.filters');
  $$('[data-filters-toggle]').forEach(function (b) { b.addEventListener('click', function () { var o = !fp.classList.contains('open'); fp.classList.toggle('open', o); d.body.style.overflow = o ? 'hidden' : ''; }); });

  fromURL();
  if (root.dataset.preset) { var pr = root.dataset.preset.split(':'); if (!state[pr[0]].length) state[pr[0]] = [pr[1]]; }
  if (q) q.value = state.q; if (wmin) wmin.value = state.wmin; if (wmax) wmax.value = state.wmax; if (sort) sort.value = state.sort;
  apply();
})();
