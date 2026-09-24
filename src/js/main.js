/* ADALIGHT — vanilla JS, без зависимостей */
(function () {
  'use strict';
  var d = document, w = window, C = w.ADA || {};
  d.documentElement.classList.remove('no-js');
  var $ = function (s, r) { return (r || d).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || d).querySelectorAll(s)); };
  var reduce = w.matchMedia && w.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var fmt = function (n) { return Math.round(n).toLocaleString('ru-RU').replace(/,/g, ' ') + ' ₽'; };
  w.ADAfmt = fmt;

  /* ---------- storage (с защитой: приватный режим/заблокированные куки) ---------- */
  var store = {
    get: function (k, def) { try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : def; } catch (e) { return def; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  };

  /* ---------- UTM / источник заявки ---------- */
  (function () {
    var q = new URLSearchParams(location.search), utm = {};
    ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'yclid', 'gclid'].forEach(function (k) { if (q.get(k)) utm[k] = q.get(k); });
    if (Object.keys(utm).length) { utm.landing = location.pathname; store.set('ada-utm', utm); }
    if (!store.get('ada-ref', null) && d.referrer && d.referrer.indexOf(location.host) < 0) store.set('ada-ref', d.referrer);
  })();

  function goal(name) { try { if (C.metrika && w.ym) w.ym(C.metrika, 'reachGoal', name); } catch (e) {} }
  w.ADAgoal = goal;

  /* ---------- header: mega menu + drawer ---------- */
  var megaBtn = $('[data-mega]'), mega = $('#mega');
  if (megaBtn && mega) {
    var closeT;
    var open = function (v) { mega.classList.toggle('open', v); megaBtn.setAttribute('aria-expanded', v); };
    megaBtn.addEventListener('click', function () { open(!mega.classList.contains('open')); });
    [megaBtn, mega].forEach(function (el) {
      el.addEventListener('mouseenter', function () { if (w.innerWidth > 980) { clearTimeout(closeT); open(true); } });
      el.addEventListener('mouseleave', function () { closeT = setTimeout(function () { open(false); }, 200); });
    });
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape') open(false); });
  }
  var drawer = $('#drawer');
  $$('[data-drawer]').forEach(function (b) {
    b.addEventListener('click', function () {
      var o = !drawer.classList.contains('open');
      drawer.classList.toggle('open', o); d.body.style.overflow = o ? 'hidden' : '';
      $$('[data-drawer]').forEach(function (x) { x.setAttribute('aria-expanded', o); });
      if (o) { var f = $('a', drawer); f && f.focus(); }
    });
  });

  /* ---------- reveal on scroll ---------- */
  if ('IntersectionObserver' in w && !reduce) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -8% 0px' });
    $$('.rv').forEach(function (el) { io.observe(el); });
  } else { $$('.rv').forEach(function (el) { el.classList.add('in'); }); }

  /* ---------- HERO: свет за курсором + цветовая температура ---------- */
  var hero = $('.hero');
  if (hero) {
    var lit = $('.hero-lit', hero), hint = $('.hint', hero), tx = 62, ty = 38, cx = 62, cy = 38, raf = null, auto = true, t0 = performance.now();
    var paint = function () {
      cx += (tx - cx) * 0.12; cy += (ty - cy) * 0.12;
      lit.style.setProperty('--x', cx + '%'); lit.style.setProperty('--y', cy + '%');
      if (hint) { hint.style.setProperty('--x', cx + '%'); hint.style.setProperty('--y', cy + '%'); }
      if (Math.abs(tx - cx) > 0.05 || Math.abs(ty - cy) > 0.05 || auto) raf = requestAnimationFrame(tick); else raf = null;
    };
    var tick = function (t) {
      if (auto && !reduce) { var k = (t - t0) / 1000; tx = 55 + Math.sin(k * 0.45) * 22; ty = 42 + Math.sin(k * 0.8) * 14; }
      paint();
    };
    var visible = true;
    if ('IntersectionObserver' in w) new IntersectionObserver(function (es) { visible = es[0].isIntersecting; if (visible && !raf) raf = requestAnimationFrame(tick); }).observe(hero);
    var move = function (x, y) {
      var r = hero.getBoundingClientRect();
      tx = (x - r.left) / r.width * 100; ty = (y - r.top) / r.height * 100; auto = false; hero.classList.add('moved');
      if (!raf && visible) raf = requestAnimationFrame(tick);
    };
    hero.addEventListener('pointermove', function (e) { if (e.pointerType === 'mouse' || e.pressure > 0) move(e.clientX, e.clientY); }, { passive: true });
    hero.addEventListener('touchmove', function (e) { var t = e.touches[0]; move(t.clientX, t.clientY); }, { passive: true });
    if (!reduce) raf = requestAnimationFrame(tick); else hero.classList.add('on');
    $$('[data-cct]', hero).forEach(function (b) {
      b.addEventListener('click', function () {
        hero.setAttribute('data-cct', b.getAttribute('data-cct'));
        $$('[data-cct]', hero).forEach(function (x) { x.setAttribute('aria-pressed', x === b); });
        var o = $('[data-cct-out]', hero); if (o) o.textContent = b.getAttribute('data-cct') + ' K';
      });
    });
    var sw = $('.switch', hero);
    sw && sw.addEventListener('click', function () {
      var on = !hero.classList.contains('on'); hero.classList.toggle('on', on); sw.setAttribute('aria-pressed', on);
      $('b', sw).textContent = on ? 'Свет включён' : 'Включить весь свет';
    });
  }

  /* ---------- спецификация (корзина проекта) ---------- */
  var SPEC_KEY = 'ada-spec';
  var Spec = {
    all: function () { return store.get(SPEC_KEY, []); },
    save: function (a) { store.set(SPEC_KEY, a); Spec.badge(); d.dispatchEvent(new CustomEvent('spec:change')); },
    add: function (item, qty) {
      var a = Spec.all(), key = item.sku + '|' + (item.opt || ''), f = a.filter(function (x) { return x.key === key; })[0];
      if (f) f.qty += qty; else { item.key = key; item.qty = qty; a.push(item); }
      Spec.save(a); goal('spec_add');
    },
    count: function () { return Spec.all().reduce(function (s, x) { return s + (x.qty || 0); }, 0); },
    badge: function () { var n = Spec.all().length; $$('[data-spec-count]').forEach(function (b) { b.textContent = n; b.setAttribute('data-n', n); }); }
  };
  w.ADASpec = Spec; Spec.badge();

  var toastEl;
  function toast(html) {
    if (!toastEl) { toastEl = d.createElement('div'); toastEl.className = 'toast'; toastEl.setAttribute('role', 'status'); d.body.appendChild(toastEl); }
    toastEl.innerHTML = html; toastEl.classList.add('show');
    clearTimeout(toastEl._t); toastEl._t = setTimeout(function () { toastEl.classList.remove('show'); }, 4200);
  }
  w.ADAtoast = toast;

  d.addEventListener('click', function (e) {
    var b = e.target.closest('[data-add]');
    if (!b) return;
    e.preventDefault();
    var item = JSON.parse(b.getAttribute('data-add'));
    var qEl = b.getAttribute('data-qty-from') ? $(b.getAttribute('data-qty-from')) : null;
    var qty = Math.max(1, parseInt(qEl ? qEl.value : 1, 10) || 1);
    var optEl = b.getAttribute('data-opt-from') ? $(b.getAttribute('data-opt-from')) : null;
    if (optEl) { item.opt = optEl.getAttribute('data-label'); if (optEl.getAttribute('data-price')) item.price = +optEl.getAttribute('data-price'); }
    Spec.add(item, qty);
    toast('<span>Добавлено в спецификацию: <b>' + item.sku + '</b> × ' + qty + '</span><a href="' + C.base + '/spec/">Открыть</a>');
  });

  /* ---------- формы ---------- */
  function collect(form) {
    var data = {}, fd = new FormData(form);
    fd.forEach(function (v, k) { if (v instanceof File) return; data[k] = data[k] ? data[k] + ', ' + v : v; });
    data.page = location.href; data.utm = store.get('ada-utm', null); data.referrer = store.get('ada-ref', '');
    if (form.hasAttribute('data-with-spec')) data.spec = Spec.all().map(function (x) { return x.sku + (x.opt ? ' [' + x.opt + ']' : '') + ' × ' + x.qty; }).join('; ');
    return data;
  }
  function validate(form) {
    var ok = true;
    $$('[required]', form).forEach(function (el) {
      var f = el.closest('.field') || el.parentNode, bad = false;
      if (el.type === 'checkbox') bad = !el.checked;
      else if (el.type === 'tel') bad = (el.value.replace(/\D/g, '').length < 10);
      else if (el.type === 'email') bad = !/^\S+@\S+\.\S+$/.test(el.value);
      else bad = !el.value.trim();
      f.classList.toggle('invalid', bad); if (bad && ok) { el.focus(); ok = false; }
    });
    return ok;
  }
  $$('input[type=tel]').forEach(function (el) {
    el.addEventListener('input', function () {
      var v = el.value.replace(/\D/g, ''); if (!v) { el.value = ''; return; }
      if (v[0] === '8') v = '7' + v.slice(1); if (v[0] !== '7') v = '7' + v; v = v.slice(0, 11);
      var o = '+7'; if (v.length > 1) o += ' (' + v.slice(1, 4); if (v.length >= 4) o += ') ' + v.slice(4, 7); if (v.length >= 7) o += '-' + v.slice(7, 9); if (v.length >= 9) o += '-' + v.slice(9, 11);
      el.value = o;
    });
  });
  $$('form[data-lead]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!validate(form)) return;
      var data = collect(form), btn = $('[type=submit]', form);
      var label = form.getAttribute('data-lead') || 'Заявка с сайта';
      var done = function (viaMail) {
        form.classList.add('sent'); goal('lead'); goal('lead_' + (form.getAttribute('data-goal') || 'form'));
        var m = $('.form-ok .via', form); if (m) m.hidden = !viaMail;
      };
      if (C.endpoint) {
        btn.disabled = true; btn.textContent = 'Отправляем…';
        fetch(C.endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify({ form: label, data: data }) })
          .then(function (r) { if (!r.ok) throw 0; done(false); })
          .catch(function () { btn.disabled = false; btn.textContent = 'Отправить ещё раз'; toast('Не удалось отправить. Позвоните: <a href="tel:' + C.phoneRaw + '">' + C.phone + '</a>'); });
      } else {
        var body = Object.keys(data).filter(function (k) { return data[k] && k !== 'consent'; }).map(function (k) {
          var v = typeof data[k] === 'object' ? JSON.stringify(data[k]) : data[k]; return k + ': ' + v;
        }).join('\n');
        location.href = 'mailto:' + C.email + '?subject=' + encodeURIComponent(label + ' — adalight') + '&body=' + encodeURIComponent(body);
        done(true);
      }
    });
    $$('input,select,textarea', form).forEach(function (el) { el.addEventListener('input', function () { var f = el.closest('.field'); f && f.classList.remove('invalid'); }); });
  });

  /* ---------- вкладки ---------- */
  $$('[role=tablist]').forEach(function (tl) {
    var tabs = $$('[role=tab]', tl);
    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () {
        tabs.forEach(function (x) { var on = x === t; x.setAttribute('aria-selected', on); x.tabIndex = on ? 0 : -1; d.getElementById(x.getAttribute('aria-controls')).hidden = !on; });
      });
      t.addEventListener('keydown', function (e) {
        var n = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0; if (!n) return;
        var nx = tabs[(i + n + tabs.length) % tabs.length]; nx.focus(); nx.click();
      });
    });
  });

  /* ---------- галерея + lightbox ---------- */
  var lb, lbImgs = [], lbI = 0;
  function lbShow(list, i) {
    if (!lb) {
      lb = d.createElement('div'); lb.className = 'lb'; lb.setAttribute('role', 'dialog'); lb.setAttribute('aria-modal', 'true');
      lb.innerHTML = '<img alt=""><button class="x" aria-label="Закрыть">×</button><button class="pv" aria-label="Назад">‹</button><button class="nx" aria-label="Вперёд">›</button>';
      d.body.appendChild(lb);
      lb.addEventListener('click', function (e) { if (e.target === lb || e.target.classList.contains('x')) lbClose(); });
      $('.pv', lb).onclick = function () { lbGo(-1); }; $('.nx', lb).onclick = function () { lbGo(1); };
      d.addEventListener('keydown', function (e) { if (!lb.classList.contains('open')) return; if (e.key === 'Escape') lbClose(); if (e.key === 'ArrowLeft') lbGo(-1); if (e.key === 'ArrowRight') lbGo(1); });
    }
    lbImgs = list; lbI = i; lbGo(0); lb.classList.add('open'); d.body.style.overflow = 'hidden'; $('.x', lb).focus();
  }
  function lbGo(n) { lbI = (lbI + n + lbImgs.length) % lbImgs.length; $('img', lb).src = lbImgs[lbI]; var one = lbImgs.length < 2; $('.pv', lb).hidden = one; $('.nx', lb).hidden = one; }
  function lbClose() { lb.classList.remove('open'); d.body.style.overflow = ''; }
  $$('[data-lightbox]').forEach(function (g) {
    var links = $$('a[data-lg]', g), list = links.map(function (a) { return a.getAttribute('data-lg'); });
    links.forEach(function (a, i) { a.addEventListener('click', function (e) { e.preventDefault(); lbShow(list, i); }); });
  });
  var gal = $('.gallery');
  if (gal) {
    var main = $('.gmain img', gal), thumbs = $$('.gthumbs button', gal), cur = 0;
    var list = thumbs.length ? thumbs.map(function (b) { return b.getAttribute('data-lg'); }) : [main.getAttribute('data-lg')];
    thumbs.forEach(function (b, i) {
      b.addEventListener('click', function () {
        cur = i; main.src = b.getAttribute('data-src'); main.srcset = b.getAttribute('data-srcset') || '';
        thumbs.forEach(function (x) { x.setAttribute('aria-current', x === b); });
      });
    });
    $('.gmain', gal).addEventListener('click', function () { lbShow(list, cur); });
  }

  /* ---------- калькулятор освещённости по углу луча ---------- */
  $$('[data-beam]').forEach(function (root) {
    var P = JSON.parse(root.getAttribute('data-beam'));
    var hEl = $('[name=h]', root), aEl = $('[name=a]', root), fEl = $('[name=f]', root);
    var svg = $('svg', root);
    var draw = function () {
      var h = +hEl.value, a = +aEl.value, lm = +fEl.value;
      var half = a / 2 * Math.PI / 180;
      var sr = 2 * Math.PI * (1 - Math.cos(half));
      var I = lm * 0.85 / sr; // кд, упрощённо с учётом потерь
      var E = I / (h * h);
      var D = 2 * h * Math.tan(half);
      $('[data-o=h]', root).textContent = h.toFixed(1) + ' м';
      $('[data-o=a]', root).textContent = a + '°';
      $('[data-o=f]', root).textContent = lm + ' лм';
      $('[data-o=E]', root).innerHTML = Math.round(E) + ' лк<small>в центре пятна на высоте ' + h.toFixed(1) + ' м · Ø пятна ' + D.toFixed(2) + ' м</small>';
      var W = 400, H = 300, top = 30, scale = (H - top - 30) / Math.max(h, 1.5);
      var y = top + h * scale, dx = Math.min(D / 2 * scale, W / 2 - 4);
      var cone = $('[data-el=cone]', svg); cone.setAttribute('d', 'M' + (W / 2 - 6) + ' ' + top + ' L' + (W / 2 - dx) + ' ' + y + ' L' + (W / 2 + dx) + ' ' + y + ' L' + (W / 2 + 6) + ' ' + top + 'Z');
      var fl = $('[data-el=floor]', svg); fl.setAttribute('y1', y); fl.setAttribute('y2', y);
      var sp = $('[data-el=spot]', svg); sp.setAttribute('cy', y); sp.setAttribute('rx', dx);
      var lab = $('[data-el=lab]', svg); lab.setAttribute('y', y + 20); lab.textContent = 'Ø ' + D.toFixed(2) + ' м';
      var op = Math.max(0.12, Math.min(0.9, E / 900)); cone.setAttribute('fill-opacity', op.toFixed(2)); sp.setAttribute('fill-opacity', Math.min(1, op + 0.1).toFixed(2));
    };
    [hEl, aEl, fEl].forEach(function (el) { el.addEventListener('input', draw); });
    $$('[data-angle]', root).forEach(function (b) { b.addEventListener('click', function () { aEl.value = b.getAttribute('data-angle'); draw(); }); });
    draw();
  });

  /* ---------- калькулятор партнёра ---------- */
  var pc = $('[data-partner-calc]');
  if (pc) {
    var ins = $$('input[type=range]', pc);
    var run = function () {
      var bud = +$('[name=bud]', pc).value, n = +$('[name=n]', pc).value, m = +$('[name=m]', pc).value;
      $('[data-v=bud]', pc).textContent = fmt(bud); $('[data-v=n]', pc).textContent = n; $('[data-v=m]', pc).textContent = m + '%';
      var buy = bud / (1 + m / 100), prof = bud - buy;
      $('[data-o=buy]', pc).textContent = fmt(buy); $('[data-o=prof]', pc).textContent = fmt(prof);
      $('[data-o=month]', pc).textContent = fmt(prof * n); $('[data-o=year]', pc).textContent = fmt(prof * n * 12);
    };
    ins.forEach(function (i) { i.addEventListener('input', run); }); run();
  }

  /* ---------- калькулятор количества светильников (метод коэффициента использования) ---------- */
  var rc = $('[data-room-calc]');
  if (rc) {
    var rr = function () {
      var L = +$('[name=L]', rc).value || 0, B = +$('[name=B]', rc).value || 0, H = +$('[name=H]', rc).value || 2.7;
      var E = +$('[name=E]', rc).value, F = +$('[name=F]', rc).value || 1, refl = +$('[name=rf]', rc).value;
      var S = L * B; if (!S) return;
      var hc = Math.max(H - 0.8, 0.5), i = S / (hc * (L + B)); // индекс помещения
      var u = Math.min(0.95, (refl ? 0.42 : 0.34) + 0.19 * Math.log(1 + i)); // аппроксимация КИ
      var k = 1.25, N = Math.ceil(E * S * k / (F * u));
      var cols = Math.max(1, Math.round(Math.sqrt(N * L / B))), rows = Math.max(1, Math.ceil(N / cols));
      $('[data-o=S]', rc).textContent = S.toFixed(1) + ' м²';
      $('[data-o=N]', rc).textContent = N;
      $('[data-o=grid]', rc).textContent = rows + ' × ' + cols + ' (шаг ~' + (L / cols).toFixed(2) + ' × ' + (B / rows).toFixed(2) + ' м)';
      $('[data-o=W]', rc).textContent = Math.round(N * (+$('[name=P]', rc).value || 0)) + ' Вт · ' + (N * (+$('[name=P]', rc).value || 0) / S).toFixed(1) + ' Вт/м²';
      var g = $('[data-o=plan]', rc);
      if (g) {
        var s = '', vw = 300, vh = Math.max(120, Math.min(300, 300 * B / L));
        s += '<rect x="1" y="1" width="' + (vw - 2) + '" height="' + (vh - 2) + '" fill="none" stroke="#555" stroke-width="2" rx="4"/>';
        for (var r = 0; r < rows; r++) for (var c = 0; c < cols; c++) {
          if (r * cols + c >= N) continue;
          var x = (c + .5) * vw / cols, y = (r + .5) * vh / rows;
          s += '<circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="14" fill="url(#glow)"/><circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="3.5" fill="#ffc603"/>';
        }
        g.setAttribute('viewBox', '0 0 ' + vw + ' ' + vh);
        g.innerHTML = '<defs><radialGradient id="glow"><stop offset="0" stop-color="#ffc603" stop-opacity=".55"/><stop offset="1" stop-color="#ffc603" stop-opacity="0"/></radialGradient></defs>' + s;
      }
    };
    $$('input,select', rc).forEach(function (el) { el.addEventListener('input', rr); }); rr();
  }

  /* ---------- копирование ссылки ---------- */
  $$('[data-copy]').forEach(function (b) {
    b.addEventListener('click', function () {
      var t = b.getAttribute('data-copy');
      (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(function () { toast('Ссылка скопирована'); }, function () { prompt('Скопируйте ссылку', t); });
    });
  });

  /* ---------- метрика целей на кликах ---------- */
  d.addEventListener('click', function (e) {
    var a = e.target.closest('a'); if (!a) return;
    var h = a.getAttribute('href') || '';
    if (h.indexOf('tel:') === 0) goal('click_phone'); else if (h.indexOf('mailto:') === 0) goal('click_email'); else if (h.indexOf('wa.me') > -1) goal('click_whatsapp');
  });
})();
