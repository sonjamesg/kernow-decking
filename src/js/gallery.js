  /* gallery.js: Gallery lightbox: swipe, arrows, keyboard, preload, shared scroll lock. */
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

