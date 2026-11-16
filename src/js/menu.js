  /* menu.js: Mobile menu and body scroll lock (shared with the lightbox). */
  // Mobile menu with a reliable background scroll lock (iOS Safari + Android Chrome)
  var root = document.documentElement, body = document.body, savedY = 0, locked = false;
  function lock() {
    if (locked) return; locked = true;
    savedY = window.scrollY || window.pageYOffset || 0;
    if (savedY < 1 && lastY > 0) savedY = lastY;
    root.style.scrollBehavior = 'auto';
    body.style.top = (-savedY) + 'px';
    root.classList.add('nav-locked');
    if (typeof updateChrome === 'function') updateChrome();
  }
  function unlock() {
    if (!locked) return; locked = false;
    root.classList.remove('nav-locked');
    body.style.top = '';
    try { window.scrollTo({ top: savedY, left: 0, behavior: 'instant' }); } catch (err) { window.scrollTo(0, savedY); }
    if (Math.abs((window.scrollY || 0) - savedY) > 1) window.scrollTo(0, savedY);
    requestAnimationFrame(function () { root.style.scrollBehavior = ''; updateChrome(); });
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

