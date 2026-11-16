/* Kernow Decking Co. — site behaviour (no dependencies) */
(function () {
  'use strict';
  document.documentElement.classList.add('js');
  var nav = document.getElementById('main-nav');
  var toggle = document.querySelector('.nav-toggle');
  var mobileBar = document.querySelector('.mobile-bar');

  document.querySelectorAll('.year').forEach(function (y) { y.textContent = new Date().getFullYear(); });

  // Mobile menu with a reliable background scroll lock (iOS Safari + Android Chrome)
  var root = document.documentElement, body = document.body, savedY = 0, locked = false;
  function lock() {
    if (locked) return; locked = true;
    savedY = window.scrollY || window.pageYOffset || 0;
    root.style.scrollBehavior = 'auto';
    body.style.top = (-savedY) + 'px';
    root.classList.add('nav-locked');
  }
  function unlock() {
    if (!locked) return; locked = false;
    root.classList.remove('nav-locked');
    body.style.top = '';
    try { window.scrollTo({ top: savedY, left: 0, behavior: 'instant' }); } catch (err) { window.scrollTo(0, savedY); }
    if (Math.abs((window.scrollY || 0) - savedY) > 1) window.scrollTo(0, savedY);
    requestAnimationFrame(function () { root.style.scrollBehavior = ''; });
  }
  function setMenu(open) {
    if (!toggle || !nav) return;
    nav.classList.toggle('open', open);
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    if (open) lock(); else unlock();
  }
  if (toggle && nav) {
    toggle.addEventListener('click', function () { setMenu(!nav.classList.contains('open')); });
    nav.addEventListener('click', function (e) {
      var a = e.target.closest('a');
      if (!a || !nav.classList.contains('open')) return;
      var href = a.getAttribute('href') || '', hash = href.indexOf('#') > -1 ? href.slice(href.indexOf('#')) : '';
      var samePage = hash && (href.charAt(0) === '#' || href.split('#')[0] === '' || location.pathname.split('/').pop() === href.split('#')[0] || (href.split('#')[0] === 'index.html' && /(^|\/)(index\.html)?$/.test(location.pathname)));
      setMenu(false);
      if (samePage) {
        var t = document.querySelector(hash);
        if (t) { e.preventDefault(); t.scrollIntoView({ behavior: 'smooth' }); history.replaceState(null, '', hash); }
      }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('open')) { setMenu(false); try { toggle.focus({ preventScroll: true }); } catch (err) {} }
    });
    var mq = window.matchMedia('(min-width:1080px)');
    var onMq = function () { if (mq.matches && nav.classList.contains('open')) setMenu(false); };
    if (mq.addEventListener) mq.addEventListener('change', onMq); else if (mq.addListener) mq.addListener(onMq);
    window.addEventListener('resize', onMq);
  }

  function onScroll() { if (mobileBar) mobileBar.classList.toggle('show', window.scrollY > window.innerHeight * 0.6); }
  window.addEventListener('scroll', onScroll, { passive: true }); onScroll();

  // Boards "laying down" as they scroll into view
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -10% 0px' });
    document.querySelectorAll('.planks, .step-board').forEach(function (el) { el.classList.add('reveal'); io.observe(el); });
    document.querySelectorAll('.board-card, .g-item, .review, .framed, .cond, .sign, .usp li').forEach(function (el) { el.classList.add('reveal-up'); io.observe(el); });
  }

  // Gallery lightbox: swipe, arrows, keyboard, preloads, shared scroll lock
  var items = Array.prototype.slice.call(document.querySelectorAll('.g-item a'));
  if (items.length) {
    var lb = document.createElement('div');
    lb.className = 'lightbox';
    lb.hidden = true;
    lb.setAttribute('role', 'dialog');
    lb.setAttribute('aria-modal', 'true');
    lb.setAttribute('aria-label', 'Decking gallery');
    lb.innerHTML = '<button type="button" class="lb-close" aria-label="Close gallery">&times;</button>' +
      '<button type="button" class="lb-prev" aria-label="Previous image"></button>' +
      '<div class="lb-stage"><img class="lb-img" src="" alt="" draggable="false"></div>' +
      '<button type="button" class="lb-next" aria-label="Next image"></button>' +
      '<p class="lb-count" aria-live="polite"></p>';
    document.body.appendChild(lb);
    var lbImg = lb.querySelector('.lb-img');
    var lbCount = lb.querySelector('.lb-count');
    var index = 0, target = 0, sliding = false, lastFocus = null;
    var reduceMotion = false;
    try { reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (err) {}

    function preload(i) {
      var a = items[(i + items.length) % items.length];
      if (!a) return;
      var im = new Image();
      im.src = a.getAttribute('href');
    }
    function setTransform(x, y, animate) {
      lbImg.classList.toggle('is-animating', !!animate && !reduceMotion);
      lbImg.style.transform = 'translate(' + x + 'px,' + (y || 0) + 'px)';
    }
    function show(i) {
      index = (i + items.length) % items.length;
      target = index;
      var a = items[index];
      var thumb = a.querySelector('img');
      lbImg.src = a.getAttribute('href');
      lbImg.alt = thumb ? thumb.alt : '';
      lbCount.textContent = (index + 1) + ' / ' + items.length;
      preload(index + 1);
      preload(index - 1);
    }
    var goTid = 0, finishGo = null;
    function go(dir) {
      if (lb.hidden) return;
      target = (target + dir + items.length) % items.length;
      if (reduceMotion) { show(target); setTransform(0, 0, false); return; }
      if (finishGo) {
        lbImg.removeEventListener('transitionend', finishGo);
        finishGo = null;
      }
      if (goTid) { clearTimeout(goTid); goTid = 0; }
      // Mid-slide: skip the outbound animation and swap immediately so rapid
      // swipes, arrows and keys stay responsive.
      if (sliding) {
        show(target);
        setTransform(dir * 40, 0, false);
        requestAnimationFrame(function () {
          requestAnimationFrame(function () {
            setTransform(0, 0, true);
            goTid = setTimeout(function () {
              sliding = false;
              lbImg.classList.remove('is-animating');
              goTid = 0;
            }, 240);
          });
        });
        return;
      }
      sliding = true;
      var w = Math.max(lb.clientWidth, 1);
      setTransform(-dir * w * 0.8, 0, true);
      var done = false;
      finishGo = function () {
        if (done) return; done = true;
        lbImg.removeEventListener('transitionend', finishGo);
        finishGo = null;
        if (goTid) { clearTimeout(goTid); goTid = 0; }
        show(target);
        setTransform(dir * 48, 0, false);
        requestAnimationFrame(function () {
          requestAnimationFrame(function () {
            setTransform(0, 0, true);
            sliding = false;
            goTid = setTimeout(function () { lbImg.classList.remove('is-animating'); goTid = 0; }, 240);
          });
        });
      };
      lbImg.addEventListener('transitionend', finishGo);
      goTid = setTimeout(finishGo, 300);
    }
    function openLb(i) {
      lastFocus = document.activeElement;
      show(i);
      setTransform(0, 0, false);
      lb.hidden = false;
      lock();
      try { lb.querySelector('.lb-close').focus({ preventScroll: true }); } catch (err) {}
    }
    function closeLb() {
      if (lb.hidden) return;
      lb.hidden = true;
      lbImg.src = '';
      setTransform(0, 0, false);
      sliding = false;
      if (!nav || !nav.classList.contains('open')) unlock();
      if (lastFocus && lastFocus.focus) { try { lastFocus.focus({ preventScroll: true }); } catch (err) { lastFocus.focus(); } }
    }

    items.forEach(function (a, i) {
      a.addEventListener('click', function (e) { e.preventDefault(); openLb(i); });
    });
    lb.querySelector('.lb-prev').addEventListener('click', function (e) { e.stopPropagation(); go(-1); });
    lb.querySelector('.lb-next').addEventListener('click', function (e) { e.stopPropagation(); go(1); });
    lb.addEventListener('click', function (e) {
      if (e.target === lb || e.target.classList.contains('lb-close')) closeLb();
    });
    document.addEventListener('keydown', function (e) {
      if (lb.hidden) return;
      if (e.key === 'Escape') { e.preventDefault(); closeLb(); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); go(-1); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); go(1); }
    });

    // Pointer swipe: horizontal next/prev, downward close. Ignores mostly-vertical flicks for paging.
    var tracking = false, axis = null, startX = 0, startY = 0, dx = 0, dy = 0;
    var stage = lb.querySelector('.lb-stage');
    function onDown(e) {
      if (e.pointerType === 'mouse' && e.button !== 0) return;
      if (finishGo) { lbImg.removeEventListener('transitionend', finishGo); finishGo = null; }
      if (goTid) { clearTimeout(goTid); goTid = 0; }
      sliding = false;
      target = index;
      tracking = true; axis = null; dx = 0; dy = 0;
      startX = e.clientX; startY = e.clientY;
      setTransform(0, 0, false);
      if (stage.setPointerCapture) { try { stage.setPointerCapture(e.pointerId); } catch (err) {} }
    }
    function onMove(e) {
      if (!tracking) return;
      dx = e.clientX - startX; dy = e.clientY - startY;
      if (!axis) {
        if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
        axis = Math.abs(dx) > Math.abs(dy) * 1.15 ? 'h' : 'v';
      }
      if (reduceMotion) return;
      if (axis === 'h') setTransform(dx, 0, false);
      else if (axis === 'v' && dy > 0) setTransform(0, dy, false);
    }
    function onUp() {
      if (!tracking) return;
      tracking = false;
      if (axis === 'h' && Math.abs(dx) >= 40) go(dx < 0 ? 1 : -1);
      else if (axis === 'v' && dy >= 80) closeLb();
      else setTransform(0, 0, !reduceMotion);
      axis = null; dx = 0; dy = 0;
    }
    stage.addEventListener('pointerdown', onDown);
    stage.addEventListener('pointermove', onMove);
    stage.addEventListener('pointerup', onUp);
    stage.addEventListener('pointercancel', onUp);
  }

  // Quote forms: validate, POST to contact.php (Hostinger), fall back to mailto
  document.querySelectorAll('.quote-form').forEach(function (form) {
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
      if (!to || to.charAt(0) === '[') { setStatus('Sorry, our online form isn\'t available right now. Please call or email us directly.', 'err'); return; }
      var body = 'Name: ' + data.get('name') + '\nPhone: ' + data.get('phone') + '\nEmail: ' + data.get('email') + '\nPostcode: ' + data.get('postcode') +
        '\nProject type: ' + data.get('project_type') + '\nPage: ' + data.get('source') + '\n\n' + data.get('message');
      setStatus('Opening your email app so you can send your enquiry… If nothing happens, email us at ' + to + '.', 'ok');
      window.location.href = 'mailto:' + to + '?subject=' + encodeURIComponent('Decking quote request: ' + data.get('project_type') + ' (' + data.get('postcode') + ')') + '&body=' + encodeURIComponent(body);
    }
    form.addEventListener('submit', function (e) {
      e.preventDefault(); setStatus('');
      if (!validate()) { setStatus('Please check the highlighted fields.', 'err'); return; }
      var data = new FormData(form);
      if (data.get('company')) return;
      btn.disabled = true; var label = btn.textContent; btn.textContent = 'Sending…';
      var ctrl = 'AbortController' in window ? new AbortController() : null;
      var timer = setTimeout(function () { if (ctrl) ctrl.abort(); }, 15000);
      fetch(form.getAttribute('action'), { method: 'POST', body: data, headers: { 'Accept': 'application/json' }, signal: ctrl ? ctrl.signal : undefined })
        .then(function (r) { var ct = r.headers.get('content-type') || ''; if (!r.ok && ct.indexOf('application/json') === -1) throw new Error('no-php'); if (ct.indexOf('application/json') === -1) throw new Error('no-php'); return r.json(); })
        .then(function (j) {
          if (j && j.ok) { form.reset(); if (ts) ts.value = String(Math.floor(Date.now() / 1000)); setStatus('Thank you! Your enquiry has been sent. We\'ll be in touch soon.', 'ok'); }
          else setStatus((j && j.error) || 'Sorry, something went wrong. Please try again or call us.', 'err');
        })
        .catch(function () { mailtoFallback(data); })
        .finally(function () { clearTimeout(timer); btn.disabled = false; btn.textContent = label; });
    });
    form.addEventListener('input', function (e) { if (e.target.classList) e.target.classList.remove('invalid'); });
  });
})();
