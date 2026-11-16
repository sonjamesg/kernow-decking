/* Kernow Decking Co. — site behaviour (no dependencies) */
(function () {
  'use strict';
  var header = document.querySelector('.site-header');
  var nav = document.getElementById('main-nav');
  var toggle = document.querySelector('.nav-toggle');
  var mobileBar = document.querySelector('.mobile-bar');

  // Year in footer
  var y = document.getElementById('year');
  if (y) y.textContent = new Date().getFullYear();

  // Mobile nav
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) { nav.classList.remove('open'); toggle.setAttribute('aria-expanded', 'false'); }
    });
  }

  // Header shadow + mobile quick bar
  function onScroll() {
    var s = window.scrollY;
    if (header) header.classList.toggle('scrolled', s > 10);
    if (mobileBar) mobileBar.classList.toggle('show', s > window.innerHeight * 0.6);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Reveal on scroll
  if ('IntersectionObserver' in window) {
    var els = document.querySelectorAll('.service-card, .step, .g-item, .review, .why-media, .why-copy, .areas-card, .faq-list details, .quote-form');
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -8% 0px' });
    els.forEach(function (el) { el.classList.add('reveal'); io.observe(el); });
  }

  // Gallery lightbox
  var lb = document.getElementById('lightbox');
  if (lb) {
    var lbImg = lb.querySelector('img');
    document.querySelectorAll('.g-item a').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        var img = a.querySelector('img');
        lbImg.src = a.getAttribute('href'); lbImg.alt = img ? img.alt : '';
        lb.hidden = false; document.body.style.overflow = 'hidden';
        lb.querySelector('.lb-close').focus();
      });
    });
    function closeLb() { lb.hidden = true; lbImg.src = ''; document.body.style.overflow = ''; }
    lb.addEventListener('click', function (e) { if (e.target === lb || e.target.classList.contains('lb-close')) closeLb(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !lb.hidden) closeLb(); });
  }

  // Quote form: validate, POST to contact.php (Hostinger), fall back to mailto
  var form = document.getElementById('quote-form');
  if (!form) return;
  var status = form.querySelector('.form-status');
  var btn = form.querySelector('button[type="submit"]');
  var ts = form.querySelector('input[name="ts"]');
  if (ts) ts.value = String(Math.floor(Date.now() / 1000));

  function setStatus(msg, type) { status.textContent = msg; status.className = 'form-status ' + (type || ''); }

  function validate() {
    var ok = true, first = null;
    form.querySelectorAll('[required]').forEach(function (f) {
      var v = f.type === 'checkbox' ? f.checked : f.value.trim() !== '';
      if (v && f.type === 'email') v = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.value.trim());
      if (v && f.name === 'phone') v = f.value.replace(/[^\d]/g, '').length >= 10;
      if (v && f.name === 'postcode') v = /^[A-Za-z]{1,2}\d[A-Za-z\d]?\s*\d[A-Za-z]{2}$/.test(f.value.trim());
      f.classList.toggle('invalid', !v);
      if (!v) { ok = false; if (!first) first = f; }
    });
    if (first) first.focus();
    return ok;
  }

  function mailtoFallback(data) {
    var to = form.getAttribute('data-email') || '';
    if (!to || to.indexOf('[') === 0) {
      setStatus('Sorry, our online form isn\'t available right now. Please call or email us directly.', 'err');
      return;
    }
    var body = 'Name: ' + data.get('name') + '\nPhone: ' + data.get('phone') + '\nEmail: ' + data.get('email') +
      '\nPostcode: ' + data.get('postcode') + '\nProject type: ' + data.get('project_type') + '\n\n' + data.get('message');
    var href = 'mailto:' + to + '?subject=' + encodeURIComponent('Quote request: ' + data.get('project_type') + ' (' + data.get('postcode') + ')') +
      '&body=' + encodeURIComponent(body);
    setStatus('Opening your email app so you can send your enquiry… If nothing happens, email us at ' + to + '.', 'ok');
    window.location.href = href;
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    setStatus('');
    if (!validate()) { setStatus('Please check the highlighted fields.', 'err'); return; }
    var data = new FormData(form);
    if (data.get('company')) return; // bot
    btn.disabled = true; var label = btn.textContent; btn.textContent = 'Sending…';

    var ctrl = 'AbortController' in window ? new AbortController() : null;
    var timer = setTimeout(function () { if (ctrl) ctrl.abort(); }, 15000);
    fetch(form.getAttribute('action'), { method: 'POST', body: data, headers: { 'Accept': 'application/json' }, signal: ctrl ? ctrl.signal : undefined })
      .then(function (r) {
        var ct = r.headers.get('content-type') || '';
        if (!r.ok || ct.indexOf('application/json') === -1) throw new Error('no-php');
        return r.json();
      })
      .then(function (j) {
        if (j && j.ok) {
          form.reset(); if (ts) ts.value = String(Math.floor(Date.now() / 1000));
          setStatus('Thank you! Your enquiry has been sent. We\'ll be in touch soon.', 'ok');
        } else {
          setStatus((j && j.error) || 'Sorry, something went wrong. Please try again or call us.', 'err');
        }
      })
      .catch(function () { mailtoFallback(data); })
      .finally(function () { clearTimeout(timer); btn.disabled = false; btn.textContent = label; });
  });

  form.addEventListener('input', function (e) { if (e.target.classList) e.target.classList.remove('invalid'); });
})();
