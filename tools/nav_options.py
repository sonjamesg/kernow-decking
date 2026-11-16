"""Builds nav-options.html: three header designs for James to compare (noindex, not linked)."""
from html import escape as e

def nav_markup(opt, services, phone='[PHONE]', phone_intl='[PHONE_INTL]'):
    drop = ''.join(f'<li><a href="{s["slug"]}.html">{e(s["short"])}</a></li>' for s in services)
    items = f'''<li class="nv-sub"><a href="index.html#services">Decking services</a><ul class="nv-drop">{drop}</ul></li>
        <li><a href="index.html#process">Process</a></li><li><a href="index.html#gallery">Gallery</a></li><li><a href="index.html#faq">FAQ</a></li>'''
    mob = ''.join(f'<li class="nv-m-sub"><a href="{s["slug"]}.html">{e(s["short"])}</a></li>' for s in services)
    return f'''<header class="nv nv-{opt}">
  <div class="nv-inner">
    <a class="nv-logo" href="index.html" aria-label="Kernow Decking Co. home"><picture><source srcset="assets/img/logo-360.webp 1x, assets/img/logo-720.webp 2x" type="image/webp"><img src="assets/img/logo-360.png" alt="Kernow Decking Co. – Design, Supply, Install decking in Cornwall" width="360" height="232"></picture></a>
    <nav class="nv-nav" aria-label="Option {opt.upper()} menu"><ul>{items}</ul></nav>
    <div class="nv-actions">
      <a class="nv-phone" href="tel:{phone_intl}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 10.8a15.5 15.5 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z"/></svg><span>{phone}</span></a>
      <a class="btn btn-brass nv-cta" href="index.html#quote">Free quote</a>
      <button class="nv-toggle" aria-expanded="false" aria-label="Open menu"><span></span><span></span><span></span></button>
    </div>
  </div>
  <div class="nv-mobile" hidden>
    <ul><li class="nv-m-head">Decking services</li>{mob}
      <li><a href="index.html#process">Process</a></li><li><a href="index.html#gallery">Gallery</a></li><li><a href="index.html#faq">FAQ</a></li></ul>
    <a class="btn btn-brass btn-block" href="index.html#quote">Get a free quote</a>
  </div>
</header>'''

OPTIONS = [
 ('a', 'Option A', 'Smoked-oak plank bar', 'A full-width dark smoked-oak bar with the logo on an inset white panel. Menu items are engraved brass lettering, with a fine brass rule that draws in on hover.'),
 ('b', 'Option B', 'Oak board tabs', 'Each menu item is its own small dark oak board with fine grain and brass screw heads, lifting slightly on hover. The logo sits on a clean white panel.'),
 ('c', 'Option C', 'Floating oak shelf', 'A clean white bar. The menu sits on a slim floating dark-oak shelf held by brass pins, and a thin oak grain strip slides in under the hovered item.'),
]

def page(head_html, services, hero_img):
    blocks = []
    for opt, label, name, desc in OPTIONS:
        blocks.append(f'''<section class="opt" id="option-{opt}" aria-labelledby="opt-{opt}-t">
  <div class="opt-label container"><p class="eyebrow">{label}</p><h2 id="opt-{opt}-t">{e(name)}</h2><p>{e(desc)}</p></div>
  <div class="opt-frame">
    {nav_markup(opt, services)}
    <div class="opt-hero" style="background-image:linear-gradient(90deg,rgba(4,30,55,.9),rgba(4,30,55,.45) 55%,rgba(4,30,55,.1)),url('{hero_img}')"><div class="container"><p class="eyebrow">Decking Newquay &amp; Cornwall</p><p class="opt-h">Decking in Cornwall, <em>built for sea, salt &amp; sunsets.</em></p></div></div>
  </div>
</section>''')
    js = '''<script>
document.querySelectorAll('.nv').forEach(function(h){
  var b=h.querySelector('.nv-toggle'),m=h.querySelector('.nv-mobile');
  b.addEventListener('click',function(){var o=b.getAttribute('aria-expanded')==='true';b.setAttribute('aria-expanded',String(!o));m.hidden=o;h.classList.toggle('open',!o);});
});
document.querySelectorAll('.nv a').forEach(function(a){a.addEventListener('click',function(ev){ev.preventDefault();});});
</script>'''
    return (head_html + '''<link rel="stylesheet" href="assets/css/nav-options.css">
<main id="main" class="opts">
  <div class="container opts-intro"><p class="eyebrow">For James · not linked from the site</p><h1>Navigation options</h1>
  <p>Three header designs. Each one is live: hover the menu, open “Decking services”, and narrow the window (or open on your phone) to see the mobile menu. Links are disabled on this page. Pick A, B or C and we’ll roll it out across the site.</p></div>
''' + '\n'.join(blocks) + '\n</main>\n' + js + '\n</body>\n</html>\n')
