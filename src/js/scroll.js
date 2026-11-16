  /* scroll.js: Header logo shrink, mobile contact bar, and reveal-on-scroll. */
  // Header logo shrink and mobile bar: use the pre-lock scroll position while
  // the menu has body { position:fixed }, otherwise scrollY is 0 and the logo jumps back to full size.
  var headerBar = document.querySelector('.site-header.oakbar');
  var lastY = 0;
  function pageScrollY() {
    if (locked) {
      var top = parseFloat(body.style.top);
      if (!isNaN(top) && Math.abs(top) > 0) return Math.abs(top);
      return lastY || savedY || 0;
    }
    return window.scrollY || window.pageYOffset || 0;
  }
  function updateChrome() {
    var y = pageScrollY();
    if (!locked) lastY = y;
    if (headerBar) headerBar.classList.toggle('is-scrolled', y > 40);
    if (mobileBar) mobileBar.classList.toggle('show', y > window.innerHeight * 0.6);
  }
  var chromeTick = false;
  function onScroll() {
    if (chromeTick) return;
    chromeTick = true;
    requestAnimationFrame(function () { updateChrome(); chromeTick = false; });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  updateChrome();

  // Reveal-on-scroll for process steps and cards (plank dividers are static)
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -10% 0px' });
    document.querySelectorAll('.step-board').forEach(function (el) { el.classList.add('reveal'); io.observe(el); });
    document.querySelectorAll('.board-card, .g-item, .review, .framed, .cond, .sign, .usp li').forEach(function (el) { el.classList.add('reveal-up'); io.observe(el); });
  }

