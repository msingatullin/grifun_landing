(function () {
  'use strict';

  var keys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'yclid', 'gclid', 'gbraid', 'wbraid', 'fbclid'];
  var storageKey = 'grifun_attribution_v1';
  var path = window.location.pathname.replace(/\/+$/, '') || '/';
  var parts = path.split('/').filter(Boolean);
  var city = path === '/' ? 'ryazan' : parts[0] || 'ryazan';
  if (parts[0] === 'regions' && parts.length >= 3) city = parts[2];
  var cities = {
    kasimov: 'kasimov', sasovo: 'sasovo', skopin: 'skopin', shilovo: 'shilovo',
    mihaylov: 'mihaylov', rybnoe: 'rybnoe', ryazhsk: 'ryazhsk',
    'spassk-ryazansky': 'spassk-ryazansky', korablino: 'korablino', novomichurinsk: 'novomichurinsk'
  };
  var page = city === 'ryazan' ? 'home' : (cities[city] ? 'city' : 'other');
  var query = new URLSearchParams(window.location.search);
  var incoming = {};
  keys.forEach(function (key) { if (query.get(key)) incoming[key] = query.get(key); });

  function read() {
    try { return JSON.parse(localStorage.getItem(storageKey) || '{}'); } catch (_) { return {}; }
  }
  function write(data) {
    try { localStorage.setItem(storageKey, JSON.stringify(data)); } catch (_) {}
  }
  var saved = read();
  var now = new Date().toISOString();
  if (Object.keys(incoming).length) {
    if (!saved.first_touch) saved.first_touch = incoming;
    saved.last_touch = incoming;
    saved.first_touch_at = saved.first_touch_at || now;
    saved.last_touch_at = now;
    write(saved);
  }

  function get() {
    var data = read();
    var result = {};
    Object.keys(incoming).forEach(function (key) { result[key] = incoming[key]; });
    result.landing_path = path;
    result.page_type = page;
    result.city = city;
    result.first_touch = JSON.stringify(data.first_touch || {});
    result.last_touch = JSON.stringify(data.last_touch || {});
    result.first_touch_at = data.first_touch_at || '';
    result.last_touch_at = data.last_touch_at || '';
    result.last_cta = data.last_cta || '';
    return result;
  }

  window.grifunAttribution = { get: get, city: city, pageType: page };

  document.addEventListener('click', function (event) {
    var link = event.target.closest && event.target.closest('a[href],button');
    if (!link) return;
    var label = (link.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 80);
    var href = link.getAttribute('href') || '';
    var action = href.indexOf('tel:') === 0 ? 'phone' : href.indexOf('t.me/') !== -1 ? 'telegram' : href.indexOf('wa.me/') !== -1 ? 'whatsapp' : link.closest('.form') ? 'form' : 'cta';
    var cta = { action: action, label: label, href: href, hash: href.indexOf('#') === 0 ? href : '', at: new Date().toISOString() };
    saved.last_cta = JSON.stringify(cta);
    write(saved);
    if (typeof ym === 'function' && window.YM_COUNTER_ID) ym(window.YM_COUNTER_ID, 'reachGoal', 'cta_' + action, { city: city, page_type: page, label: label });
  });
})();
