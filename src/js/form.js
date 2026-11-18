  /* form.js: Quote form validation, POST to contact.php, mailto fallback. */
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
          if (j && j.ok) {
            form.reset();
            if (ts) ts.value = String(Math.floor(Date.now() / 1000));
            setStatus('Thank you! Your enquiry has been sent. We\'ll be in touch soon.', 'ok');
            window.dataLayer = window.dataLayer || [];
            window.dataLayer.push({ event: 'generate_lead' });
          }
          else setStatus((j && j.error) || 'Sorry, something went wrong. Please try again or call us.', 'err');
        })
        .catch(function () { mailtoFallback(data); })
        .finally(function () { clearTimeout(timer); btn.disabled = false; btn.textContent = label; });
    });
    form.addEventListener('input', function (e) { if (e.target.classList) e.target.classList.remove('invalid'); });
  });
})();
