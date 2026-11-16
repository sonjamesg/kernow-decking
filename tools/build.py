# -*- coding: utf-8 -*-
"""Kernow Decking Co. static site generator.
Usage:  python3 tools/build.py
Regenerates every .html page in the site root, plus sitemap.xml, from tools/site_data.py and the
details in tools/site-config.json. No dependencies beyond Python 3. The generated HTML is committed,
so the site can be uploaded as-is without running this."""
import json, os, re
from html import escape as e
from site_data import SERVICES, HOME_FAQS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CFG = json.load(open(os.path.join(os.path.dirname(__file__), 'site-config.json')))
TODAY = '2026-11-16'
SITE = 'https://[DOMAIN]/'
HERO_NAME = 'decking-cornwall-newquay-sea-view-deck'
def _social_url(name, placeholder):
    """Prefer tools/site-config.json social.<name>; fall back to legacy [NAME_URL] keys."""
    soc = CFG.get('social') if isinstance(CFG.get('social'), dict) else {}
    u = (soc.get(name) or CFG.get('[%s_URL]' % name.upper()) or '').strip()
    return u or placeholder
FB_URL = _social_url('facebook', 'https://www.facebook.com/')
IG_URL = _social_url('instagram', 'https://www.instagram.com/')
_PLACEHOLDER_SOCIAL = {
    'https://www.facebook.com/', 'https://www.facebook.com', 'https://facebook.com/', 'https://facebook.com',
    'https://www.instagram.com/', 'https://www.instagram.com', 'https://instagram.com/', 'https://instagram.com',
}
HERO_PHOTO = os.path.exists(os.path.join(ROOT, 'assets', 'img', HERO_NAME + '-1920.webp'))
HERO_ALT = 'Decking in Cornwall: a deck beside a glass garden room looking out to the sea at sunset, with a lighthouse on the headland'
SVC = {s['slug']: s for s in SERVICES}

def url(slug):
    return SITE if slug == 'index' else SITE + slug + '.html'

def href(slug):
    return 'index.html' if slug == 'index' else slug + '.html'

def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, indent=1) + '</script>'

BUSINESS = {
 "@context": "https://schema.org", "@type": "HomeAndConstructionBusiness", "@id": SITE + "#business",
 "name": "Kernow Decking Co.", "slogan": "Design • Supply • Install",
 "description": "Decking design, supply and installation in Newquay and Cornwall: composite decking, hardwood and timber decking, glass and steel balustrades, deck repairs, restoration and maintenance.",
 "url": SITE, "logo": SITE + "assets/img/logo-720.png", "image": SITE + "assets/img/kernow-decking-cornwall-og.jpg",
 "telephone": "[PHONE_INTL]", "email": "[EMAIL]", "priceRange": "££",
 "address": {"@type": "PostalAddress", "addressLocality": "[BASE_TOWN]", "postalCode": "[POSTCODE]", "addressRegion": "Cornwall", "addressCountry": "GB"},
 "areaServed": [{"@type": "City", "name": "Newquay"}, {"@type": "AdministrativeArea", "name": "Cornwall"}],
 "knowsAbout": ["Decking", "Composite decking", "Hardwood decking", "Timber decking", "Garden decking", "Glass balustrades", "Deck repairs"],
 "sameAs": [u for u in (FB_URL, IG_URL) if u and u.rstrip('/') not in {x.rstrip('/') for x in _PLACEHOLDER_SOCIAL}],
 "openingHoursSpecification": [{"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "opens": "08:00", "closes": "17:30"}],
 "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Decking services in Cornwall", "itemListElement": [
   {"@type": "Offer", "itemOffered": {"@type": "Service", "name": s['h1'], "url": url(s['slug'])}} for s in SERVICES]}
}

if not BUSINESS['sameAs']:
    del BUSINESS['sameAs']

def faq_ld(faqs):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}

def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": url(s)} for i, (n, s) in enumerate(items)]}

def service_ld(name, stype, slug, area):
    a = {"@type": "City", "name": area} if area else {"@type": "AdministrativeArea", "name": "Cornwall"}
    return {"@context": "https://schema.org", "@type": "Service", "name": name, "serviceType": stype, "url": url(slug),
            "provider": {"@id": SITE + "#business"}, "areaServed": a}

# ---------------------------------------------------------------- shared fragments
ICONS = {
 'design': '<path d="M3 21h18M5 21V10l7-6 7 6v11"/><path d="M9 21v-6h6v6"/>',
 'composite': '<path d="M3 6h18M3 10h18M3 14h18M3 18h18"/>',
 'hardwood': '<path d="M12 3c4 4 6 7 6 10a6 6 0 0 1-12 0c0-3 2-6 6-10z"/><path d="M12 21V11"/>',
 'balustrade': '<path d="M3 20h18M5 20V8M19 20V8M3 8h18"/><path d="M9 11l3 5M13 11l3 5"/>',
 'repair': '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>',
 'supply': '<path d="M3 7h13v10H3zM16 10h3l2 3v4h-5"/><circle cx="7" cy="18" r="2"/><circle cx="18" cy="18" r="2"/>',
}
def icon(name):
    return f'<svg class="ico" viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'

PHONE_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 10.8a15.5 15.5 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z"/></svg>'

def head(title, desc, slug, extra_ld=(), robots='index, follow', preload_hero=False):
    lds = '\n'.join(ld(x) for x in [BUSINESS, *extra_ld])
    if preload_hero and HERO_PHOTO:
        pre = (f'<link rel="preload" as="image" type="image/webp" imagesrcset="assets/img/{HERO_NAME}-768.webp 768w, assets/img/{HERO_NAME}-1280.webp 1280w, assets/img/{HERO_NAME}-1920.webp 1920w" imagesizes="100vw">\n')
    elif preload_hero:
        pre = '<link rel="preload" as="image" href="assets/img/hero-deck-perspective-cornwall.webp">\n'
    else:
        pre = ''
    return f'''<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{url(slug)}">
<meta name="theme-color" content="#041E37">
<meta name="geo.region" content="GB-CON">
<meta name="geo.placename" content="Cornwall">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Kernow Decking Co.">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url(slug)}">
<meta property="og:image" content="{SITE}assets/img/kernow-decking-cornwall-og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Decking in Cornwall: a wooden deck looking out to a sunset sea and lighthouse">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="icon" href="favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="preload" href="assets/fonts/ibm-plex-sans-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="assets/fonts/roboto-slab-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
{pre}<link rel="stylesheet" href="assets/css/styles.css">
{lds}
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
'''

def oak_header(current='', nav_id='main-nav', extra_cls=''):
    """Live site header: smoked-oak plank bar + logo in a mitred plank frame (also used as Option A on nav-options.html)."""
    def cur(s): return ' aria-current="page"' if s == current else ''
    svc_items = ''.join(f'<li><a href="{href(s["slug"])}"{cur(s["slug"])}>{e(s["short"])}</a></li>' for s in SERVICES)
    return f'''<header class="site-header oakbar{extra_cls}">
  <div class="container header-inner">
    <a class="oak-frame" href="index.html" aria-label="Kernow Decking Co. – decking Cornwall, home">
      <span class="fr fr-t" aria-hidden="true"></span><span class="fr fr-r" aria-hidden="true"></span><span class="fr fr-b" aria-hidden="true"></span><span class="fr fr-l" aria-hidden="true"></span>
      <span class="oak-panel"><picture><source srcset="assets/img/logo-360.webp 1x, assets/img/logo-720.webp 2x" type="image/webp"><img src="assets/img/logo-360.png" alt="Kernow Decking Co. – Design, Supply, Install decking in Cornwall" width="360" height="232"></picture></span>
      <span class="oak-screws" aria-hidden="true"></span>
    </a>
    <nav class="main-nav" id="{nav_id}" aria-label="Main">
      <p class="m-head" aria-hidden="true">Menu</p>
      <ul>
        <li class="has-sub"><a href="index.html#services">Decking services</a>
          <ul class="sub">{svc_items}</ul></li>
        <li><a href="index.html#process">Process</a></li>
        <li><a href="index.html#gallery">Gallery</a></li>
        <li><a href="index.html#faq">FAQ</a></li>
      </ul>
      <a class="nav-phone" href="tel:[PHONE_INTL]" aria-label="Call Kernow Decking Co. on [PHONE]">{PHONE_SVG}<span>[PHONE]</span></a>
      <a class="btn btn-brass nav-cta" href="index.html#quote">Get a free quote</a>
    </nav>
    <div class="header-actions">
      <a class="header-phone" href="tel:[PHONE_INTL]" aria-label="Call Kernow Decking Co. on [PHONE]">{PHONE_SVG}</a>
      <button class="nav-toggle" type="button" aria-controls="{nav_id}" aria-expanded="false" aria-label="Open menu"><span class="nt-bars" aria-hidden="true"><span></span><span></span><span></span></span><span class="nt-label">Menu</span></button>
    </div>
  </div>
</header>
'''

def header(current):
    return oak_header(current)

def planks(cls=''):
    klass = 'planks ' + cls if cls else 'planks'
    board = '<span class="plank">' + ''.join(f'<i class="scr s{i}"></i>' for i in range(1, 5)) + '</span>'
    return f'<div class="{klass}" aria-hidden="true">{board}{board}<b class="planks-dust"></b></div>\n'


def photo_scene(content):
    p = 'assets/img/' + HERO_NAME
    return f'''<section class="hero scene scene-home scene-photo">
  <picture class="hero-photo">
    <source type="image/webp" srcset="{p}-768.webp 768w, {p}-1280.webp 1280w, {p}-1920.webp 1920w" sizes="100vw">
    <img src="{p}-1280.jpg" srcset="{p}-1280.jpg 1280w, {p}-1920.jpg 1920w" sizes="100vw" alt="{e(HERO_ALT)}" width="1920" height="1080" fetchpriority="high">
  </picture>
  <div class="container hero-content">{content}</div>
</section>
'''

def scene(content, cls=''):
    return f'''<section class="hero scene {cls}">
  <div class="sky" aria-hidden="true"></div>
  <div class="deck" aria-hidden="true"><img src="assets/img/hero-deck-perspective-cornwall.webp" alt="" width="1920" height="520" fetchpriority="high"></div>
  <div class="container hero-content">{content}</div>
</section>
'''

def breadcrumb_html(items):
    lis = []
    for i, (n, s) in enumerate(items):
        if i == len(items) - 1:
            lis.append(f'<li aria-current="page">{e(n)}</li>')
        else:
            lis.append(f'<li><a href="{href(s)}">{e(n)}</a></li>')
    return '<nav class="breadcrumbs" aria-label="Breadcrumb"><ol>' + ''.join(lis) + '</ol></nav>'

def page_hero(items, kicker, h1, lead, cta2=None):
    c2 = cta2 or ('Call [PHONE]', 'tel:[PHONE_INTL]')
    return scene(f'''{breadcrumb_html(items)}
    <p class="eyebrow">{e(kicker)}</p>
    <h1>{e(h1)}</h1>
    <p class="hero-lead">{e(lead)}</p>
    <div class="hero-ctas"><a class="btn btn-brass btn-lg" href="#quote">Get a free decking quote</a><a class="btn btn-glass btn-lg" href="{c2[1]}">{e(c2[0])}</a></div>''', 'scene-page')

def card_text(s):
    t = s['desc'].split('. ')[1] if '. ' in s['desc'] else s['desc']
    if len(t) < 40:
        t = s['desc'].split(': ', 1)[-1].split('. ')[0]
        t = t[0].upper() + t[1:] + '.'
    return t

def service_cards(exclude=None, town=None):
    out = []
    for s in SERVICES:
        if s['slug'] == exclude: continue
        label = f'{s["short"]} in {town}' if town else s['short']
        out.append(f'''<a class="board-card" href="{href(s["slug"])}">
  <span class="bc-icon">{icon(s["icon"])}</span>
  <h3>{e(label)}</h3>
  <p>{e(card_text(s))}</p>
  <span class="bc-more">Find out more <span aria-hidden="true">→</span></span>
</a>''')
    if not exclude and not town:
        out.append(f'''<a class="board-card" href="#quote">
  <span class="bc-icon">{icon("supply")}</span>
  <h3>Decking supply</h3>
  <p>Boards, framing, fixings, lighting and balustrade kits supplied in Newquay and Cornwall for DIY and trade projects.</p>
  <span class="bc-more">Ask for a price <span aria-hidden="true">→</span></span>
</a>''')
    return '<div class="card-grid">' + '\n'.join(out) + '</div>'

def process_section(town=None):
    where = f' in {town}' if town else ' in Newquay and Cornwall'
    return f'''<section class="section bg-navy process" id="process" aria-labelledby="process-title">
  <div class="container">
    <header class="section-head light"><p class="eyebrow">How we build your deck</p>
      <h2 id="process-title">Design <span class="dot">•</span> Supply <span class="dot">•</span> Install</h2>
      <p>One local team takes your decking project{e(where)} from first sketch to the final screw.</p></header>
    <ol class="steps">
      <li class="step-board"><span class="burn">01</span><div><h3>Design</h3><p>A free site visit, measurements and a clear decking design with material options and a fixed, itemised quote.</p></div></li>
      <li class="step-board"><span class="burn">02</span><div><h3>Supply</h3><p>We order your composite or timber boards, framing, fixings, balustrades and lighting, delivered when it suits you.</p></div></li>
      <li class="step-board"><span class="burn">03</span><div><h3>Install</h3><p>Solid groundwork and sub-frame, neat boarding and finishing, then aftercare advice and a tidy site.</p></div></li>
    </ol>
  </div>
</section>
'''

def faq_section(faqs, title, intro=''):
    items = '\n'.join(f'<details{" open" if i == 0 else ""}><summary>{e(q)}</summary><p>{e(a)}</p></details>' for i, (q, a) in enumerate(faqs))
    return f'''<section class="section bg-limed faq" id="faq" aria-labelledby="faq-title">
  <div class="container faq-grid">
    <header class="section-head left"><p class="eyebrow">FAQ</p><h2 id="faq-title">{e(title)}</h2>
      <p>{e(intro) if intro else ''} Can't see your question? Call <a href="tel:[PHONE_INTL]">[PHONE]</a> or <a href="#quote">send us a message</a>.</p></header>
    <div class="faq-list">{items}</div>
  </div>
</section>
'''

def quote_section(source, title='Get a free decking quote', town=None):
    where = f'in {town}' if town else 'in Newquay or nearby in Cornwall'
    return f'''<section class="section bg-hardwood contact" id="quote" aria-labelledby="quote-title">
  <div class="container contact-grid">
    <div class="contact-info">
      <p class="eyebrow">Free, no-obligation quote</p>
      <h2 id="quote-title">{e(title)}</h2>
      <p>Tell us about your decking project {e(where)} and we'll get back to you, usually within one working day.</p>
      <ul class="contact-list">
        <li><span class="ci-icon">{PHONE_SVG}</span><div><small>Phone</small><a href="tel:[PHONE_INTL]">[PHONE]</a></div></li>
        <li><span class="ci-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 5h18v14H3z" fill="none"/><path d="m3 6 9 7 9-7"/></svg></span><div><small>Email</small><a href="mailto:[EMAIL]">[EMAIL]</a></div></li>
        <li><span class="ci-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg></span><div><small>Based in</small><span>[BASE_TOWN], Cornwall</span></div></li>
        <li><span class="ci-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg></span><div><small>Hours</small><span>Mon–Fri 8:00–17:30</span></div></li>
      </ul>
    </div>
    <div class="oak-frame quote-frame">
      <span class="fr fr-t" aria-hidden="true"></span><span class="fr fr-r" aria-hidden="true"></span><span class="fr fr-b" aria-hidden="true"></span><span class="fr fr-l" aria-hidden="true"></span>
      <div class="oak-panel quote-panel">
    <form class="quote-form" action="contact.php" method="post" novalidate data-email="[EMAIL]">
      <p class="form-kicker">Your project</p>
      <h3 class="form-title">Send an enquiry</h3>
      <p class="form-micro">We usually reply within one working day.</p>
      <div class="form-row two">
        <label><span class="lbl">Name <b aria-hidden="true">*</b></span><input type="text" name="name" autocomplete="name" required maxlength="100"></label>
        <label><span class="lbl">Phone <b aria-hidden="true">*</b></span><input type="tel" name="phone" autocomplete="tel" required maxlength="30" inputmode="tel"></label>
      </div>
      <div class="form-row two">
        <label><span class="lbl">Email <b aria-hidden="true">*</b></span><input type="email" name="email" autocomplete="email" required maxlength="150"></label>
        <label><span class="lbl">Postcode <b aria-hidden="true">*</b></span><input type="text" name="postcode" autocomplete="postal-code" required maxlength="10" placeholder="e.g. TR1 2AB"></label>
      </div>
      <div class="form-row"><label><span class="lbl">Project type <b aria-hidden="true">*</b></span>
        <select name="project_type" required>
          <option value="">Please choose…</option>
          <option>New deck: design &amp; install</option><option>Composite decking</option><option>Hardwood / timber decking</option>
          <option>Glass or steel balustrade</option><option>Deck repair or restoration</option><option>Deck maintenance / cleaning</option>
          <option>Supply only (materials)</option><option>Something else</option>
        </select></label></div>
      <div class="form-row"><label><span class="lbl">Message <b aria-hidden="true">*</b></span>
        <textarea name="message" rows="5" required maxlength="3000" placeholder="Approximate size, location, timescale, anything else we should know…"></textarea></label></div>
      <div class="hp" aria-hidden="true"><label>Company <input type="text" name="company" tabindex="-1" autocomplete="off"></label></div>
      <input type="hidden" name="ts" value="">
      <input type="hidden" name="source" value="{e(source)}">
      <label class="consent"><input type="checkbox" name="consent" value="yes" required> <span>I agree to Kernow Decking Co. contacting me about my enquiry. See our <a href="privacy.html">privacy notice</a>.</span></label>
      <button class="btn btn-brass btn-lg btn-block" type="submit">Send my enquiry</button>
      <p class="form-status" role="status" aria-live="polite"></p>
    </form>
      </div>
      <span class="oak-screws" aria-hidden="true"></span>
    </div>
  </div>
</section>
'''

def footer():
    svc = ''.join(f'<li><a href="{href(s["slug"])}">{e(s["short"])} Cornwall</a></li>' for s in SERVICES)
    return f'''{planks('planks-footer')}<footer class="site-footer">
  <div class="container footer-grid">
    <div class="footer-brand">
      <a class="oak-frame footer-frame" href="index.html" aria-label="Kernow Decking Co. – decking Cornwall, home">
        <span class="fr fr-t" aria-hidden="true"></span><span class="fr fr-r" aria-hidden="true"></span><span class="fr fr-b" aria-hidden="true"></span><span class="fr fr-l" aria-hidden="true"></span>
        <span class="oak-panel"><picture><source srcset="assets/img/logo-360.webp 1x, assets/img/logo-720.webp 2x" type="image/webp"><img src="assets/img/logo-360.png" alt="Kernow Decking Co. – Design, Supply, Install decking in Cornwall" width="360" height="232" loading="lazy"></picture></span>
        <span class="oak-screws" aria-hidden="true"></span>
      </a>
      <p>Decking design, supply and installation, based in Newquay, Cornwall.</p>
      <ul class="footer-social">
        <li><a class="soc" href="{FB_URL}" target="_blank" rel="noopener" aria-label="Kernow Decking on Facebook"><svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M14 8h3V4h-3c-2.8 0-5 2.2-5 5v2H6v4h3v7h4v-7h3l1-4h-4V9c0-.6.4-1 1-1z"/></svg></a></li>
        <li><a class="soc" href="{IG_URL}" target="_blank" rel="noopener" aria-label="Kernow Decking on Instagram"><svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M7 3h10a4 4 0 0 1 4 4v10a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V7a4 4 0 0 1 4-4zm10 2H7a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2zm-5 3.2A3.8 3.8 0 1 1 8.2 12 3.8 3.8 0 0 1 12 8.2zm0 1.8A2 2 0 1 0 14 12a2 2 0 0 0-2-2zM17.2 6.8a1 1 0 1 1-1 1 1 1 0 0 1 1-1z"/></svg></a></li>
      </ul>
      <ul class="footer-contact"><li><a href="tel:[PHONE_INTL]">[PHONE]</a></li><li><a href="mailto:[EMAIL]">[EMAIL]</a></li><li>[BASE_TOWN], Cornwall</li></ul>
    </div>
    <div><h2 class="f-h">Decking services</h2><ul>{svc}<li><a href="index.html#quote">Free decking quote</a></li></ul></div>
    <div><h2 class="f-h">Explore</h2><ul><li><a href="index.html#process">How we work</a></li><li><a href="index.html#gallery">Decking gallery</a></li><li><a href="index.html#faq">Decking FAQs</a></li><li><a href="index.html#reviews">Reviews</a></li><li><a href="index.html#quote">Contact us</a></li></ul></div>
  </div>
  <div class="container footer-bottom">
    <p>© <span class="year">2026</span> Kernow Decking Co. · Decking Cornwall · Design • Supply • Install</p>
    <p><a href="privacy.html">Privacy</a> · <a href="credits.html">Photo credits</a> · <a href="sitemap.xml">Sitemap</a></p>
  </div>
</footer>
<div class="mobile-bar" aria-label="Quick contact"><a href="tel:[PHONE_INTL]" class="mb-call">Call us</a><a href="#quote" class="mb-quote">Free quote</a></div>
<script src="assets/js/main.js" defer></script>
</body>
</html>
'''

# ---------------------------------------------------------------- pages
def home():
    crumbs = [('Home', 'index')]
    hero = (photo_scene if HERO_PHOTO else lambda c: scene(c, 'scene-home'))('''<p class="eyebrow">Decking Newquay &amp; Cornwall · Design • Supply • Install</p>
    <h1>Proper decking in Cornwall. <span>Built to last.</span></h1>
    <p class="hero-lead">Kernow Decking Co. designs, supplies and installs composite and hardwood decking, glass balustrades and garden decks from our base in Newquay, built for Cornwall’s Atlantic weather and the best of every view.</p>
    <div class="hero-ctas"><a class="btn btn-brass btn-lg" href="#quote">Get a free quote</a><a class="btn btn-glass btn-lg" href="#services">Our decking services</a></div>
    <ul class="hero-badges"><li>Free site survey</li><li>Composite &amp; hardwood</li><li>Glass &amp; steel balustrades</li><li>Based in Newquay</li></ul>''')
    intro = f'''<section class="section bg-limed intro" aria-labelledby="intro-title">
  <div class="container intro-grid">
    <div>
      <p class="eyebrow">Decking installers in Cornwall</p>
      <h2 id="intro-title">Local deck builders who know Cornish weather</h2>
      <p>Cornwall is one of the most beautiful places in Britain to sit outside, and one of the toughest on outdoor timber. Salt air, driving rain, Atlantic gales and steep gardens all shape how a deck should be designed and built.</p>
      <p>We are a Cornish decking company offering design, supply and installation under one roof. Whether you want low-maintenance <a href="composite-decking-cornwall.html">composite decking</a>, natural <a href="hardwood-decking-cornwall.html">hardwood decking</a>, a sea-view terrace with <a href="balustrades-cornwall.html">glass balustrades</a> or <a href="deck-repairs-cornwall.html">repairs to an existing deck</a>, we will design it around your home, your garden and your view.</p>
      <p>Searching for <strong>decking near me</strong>? We are based in [BASE_TOWN]. <a href="#quote">Send us your postcode</a> for a free site survey and quote.</p>
    </div>
    <ul class="usp">
      <li class="board"><strong>Design, supply &amp; install</strong><span>One team and one clear, itemised price.</span></li>
      <li class="board"><strong>Built for the coast</strong><span>Stainless fixings, ventilated sub-frames, grippy boards.</span></li>
      <li class="board"><strong>Sloping gardens sorted</strong><span>Raised and multi-level decks with safe steps.</span></li>
      <li class="board"><strong>Honest advice</strong><span>Composite or timber? We'll tell you what suits your site.</span></li>
    </ul>
  </div>
</section>
'''
    services = f'''<section class="section bg-hardwood services" id="services" aria-labelledby="services-title">
  <div class="container">
    <header class="section-head light"><p class="eyebrow">Decking services in Cornwall</p>
      <h2 id="services-title">Everything for your deck, from first board to last screw</h2>
      <p>Garden decking, composite and timber decks, balustrades and repairs, designed and installed by one local team.</p></header>
    {service_cards()}
  </div>
</section>
'''
    why = '''<section class="section bg-limed why" id="why" aria-labelledby="why-title">
  <div class="container why-grid">
    <figure class="why-media framed"><img src="assets/img/coastal-decking-steps-sunset-cornwall.webp" alt="Coastal timber decking with steps and handrails built to face the Atlantic – decking Cornwall" width="960" height="720" loading="lazy"><figcaption>Example image</figcaption></figure>
    <div class="why-copy">
      <p class="eyebrow">Why choose Kernow Decking Co.</p>
      <h2 id="why-title">Decks that stand up to the Atlantic</h2>
      <p>A deck in Cornwall has to cope with more than sunshine. We build every deck with the local conditions in mind.</p>
      <ul class="tick-list">
        <li><strong>Built for coastal conditions.</strong> Marine-grade stainless fixings near the sea, good drainage and ventilation underneath.</li>
        <li><strong>The right boards for your site.</strong> Composite for low maintenance, hardwood for natural character, chosen honestly.</li>
        <li><strong>Fixed, itemised quotes.</strong> No hidden extras and no pressure.</li>
        <li><strong>Tidy, respectful installers.</strong> We look after your home and leave the site clean.</li>
        <li><strong>Holiday-let friendly.</strong> We can plan work around your bookings.</li>
        <li><strong>Workmanship guarantee.</strong> [GUARANTEE_YEARS]-year guarantee on our installations.</li>
      </ul>
      <a class="btn btn-navy" href="#quote">Book a free site survey</a>
    </div>
  </div>
</section>
'''
    gal = [('multi-level-garden-decking-cornwall.webp', 'Multi-level garden decking with steps and built-in planters – multi-level decking ideas for Cornwall', 'Multi-level garden decking', 1200, 900, 'g-big'),
           ('composite-decking-glass-balustrade-cornwall.webp', 'Long composite deck with a glass balustrade – composite decking in Cornwall', 'Composite decking & glass balustrade', 1100, 825, ''),
           ('decking-installation-joists-cornwall.webp', 'Deck boards being fixed over a timber sub-frame of joists – decking installation in Cornwall', 'Decking installation', 1100, 825, ''),
           ('hardwood-deck-boards-grain-cornwall.webp', 'Close-up of rich brown hardwood deck boards and grain – hardwood decking Cornwall', 'Hardwood board grain', 853, 640, ''),
           ('timber-deck-steel-balustrade-cornwall.webp', 'Timber deck walkway with stainless steel balustrade towards the sea – coastal decking Cornwall', 'Steel balustrade decking', 720, 540, ''),
           ('deck-board-gaps-grain-cornwall.webp', 'Close-up of timber deck boards with even drainage gaps and natural grain – decking Cornwall', 'Board spacing & grain', 850, 638, ''),
           ('coastal-decking-steps-sunset-cornwall.webp', 'Timber decking with steps and handrails leading to the sea at sunset – coastal deck steps Cornwall', 'Coastal deck steps', 960, 720, ''),
           ('deck-repairs-cornwall.webp', 'Timber deck boards being replaced – deck repairs in Cornwall', 'Deck repairs', 960, 720, 'g-wide')]
    figs = '\n'.join(f'<figure class="g-item {c}"><a href="assets/img/{f}"><img src="assets/img/{f}" alt="{e(a)}" width="{w}" height="{h}" loading="lazy"></a><figcaption>{e(cap)}</figcaption></figure>' for f, a, cap, w, h, c in gal)
    gallery = f'''<section class="section bg-cedar gallery" id="gallery" aria-labelledby="gallery-title">
  <div class="container">
    <header class="section-head"><p class="eyebrow on-wood">Decking gallery</p>
      <h2 id="gallery-title" class="on-wood">Decking ideas for Cornish homes</h2>
      <p class="placeholder-note">Placeholder images: these will be replaced with real Kernow Decking Co. projects.</p></header>
    <!-- PLACEHOLDER GALLERY: replace the images with real project photos (keep descriptive, keyword-rich file names) -->
    <div class="gallery-grid">{figs}</div>
  </div>
</section>
'''
    reviews = '''<section class="section bg-limed testimonials" id="reviews" aria-labelledby="reviews-title">
  <div class="container">
    <header class="section-head"><p class="eyebrow">Customer reviews</p><h2 id="reviews-title">What our decking customers say</h2>
      <p class="placeholder-note">Example reviews: replace these with genuine customer reviews before launch.</p></header>
    <!-- PLACEHOLDER TESTIMONIALS: replace with real reviews (names/towns with permission). -->
    <div class="review-grid">''' + ''.join(f'''
      <figure class="review board placeholder"><span class="ph-tag">Placeholder</span>
        <blockquote>"[REVIEW {i}] Customer review text goes here, e.g. what we built, how the team was and how happy they are with their new deck."</blockquote>
        <figcaption>[CUSTOMER NAME], [TOWN]</figcaption></figure>''' for i in (1, 2, 3)) + '''
    </div>
  </div>
</section>
'''
    body = (head('Decking Cornwall | Newquay Deck Builders | Kernow Decking Co.',
                 'Decking in Newquay and Cornwall by Kernow Decking Co.: composite and hardwood decking, garden decks, glass balustrades and deck repairs, designed, supplied and installed. Free quotes.',
                 'index', [faq_ld(HOME_FAQS)], preload_hero=True)
            + header('index') + '<main id="main">\n' + hero + planks() + intro + services + planks() + process_section() + why
            + gallery + reviews + faq_section(HOME_FAQS, 'Decking in Cornwall: your questions answered')
            + quote_section('Home page') + '</main>\n' + footer())
    return body

def service_page(s):
    crumbs = [('Home', 'index'), ('Decking services', 'index'), (s['short'], s['slug'])]
    crumbs_schema = [('Home', 'index'), (s['short'], s['slug'])]
    secs = '\n'.join(f'<h2>{e(h)}</h2>' + ''.join(f'<p>{e(p)}</p>' for p in ps) for h, ps in s['sections'])
    content = f'''<section class="section bg-limed svc-body" aria-label="{e(s["h1"])}">
  <div class="container svc-grid">
    <div class="prose">
      <p class="lead">{e(s["lead"])}</p>
      {secs}
      <p><a class="btn btn-navy" href="#quote">Get a free quote for {e(s["short"].lower())}</a></p>
    </div>
    <aside class="svc-aside">
      <figure class="framed"><img src="assets/img/{s["img"]}" alt="{e(s["img_alt"])}" loading="lazy" width="960" height="720"><figcaption>Example image</figcaption></figure>
      <div class="board aside-board"><h2 class="h3">{e(s["short"])} near you</h2><p>We are a local decking team based in [BASE_TOWN], Cornwall. Searching for {e(s["short"].lower())} near you? Send us your postcode for a free site survey and quote.</p>
        <p><a class="btn btn-brass" href="#quote">Get a free quote</a></p></div>
    </aside>
  </div>
</section>
'''
    others = f'''<section class="section bg-hardwood services" aria-labelledby="more-title">
  <div class="container"><header class="section-head light"><p class="eyebrow">More decking services</p><h2 id="more-title">Other decking services in Cornwall</h2></header>
  {service_cards(exclude=s["slug"])}</div>
</section>
'''
    return (head(s['title'], s['desc'], s['slug'], [crumbs_ld(crumbs_schema), service_ld(s['h1'], s['serviceType'], s['slug'], None), faq_ld(s['faqs'])])
            + header(s['slug']) + '<main id="main">\n'
            + page_hero(crumbs_schema, s['kicker'], s['h1'], s['desc'])
            + planks() + content + others + process_section()
            + faq_section(s['faqs'], f'{s["short"]} in Cornwall: FAQs')
            + quote_section(s['h1'], f'Get a free {s["short"].lower()} quote') + '</main>\n' + footer())

def simple_page(slug, title, body, robots='noindex'):
    return (head(f'{title} | Kernow Decking Co.', f'{title} – Kernow Decking Co., decking Cornwall.', slug, robots=robots)
            + header(slug) + f'<main id="main" class="section bg-limed page"><div class="container prose board page-board">{body}</div></main>\n' + footer())

def credits():
    return simple_page('credits', 'Photo credits', '''<p class="eyebrow">Credits</p><h1>Photo credits</h1>
<p>Example decking photography is used until Kernow Decking Co. project photos are added. Images were downloaded, resized and cropped (modified) for this site. Images marked CC BY-SA are shared under the same licence. Wood textures, the service-page deck and the sunset illustration were created for this site.''' + (' The home page hero photo was supplied by Kernow Decking Co.' if HERO_PHOTO else '') + '''</p>
<ul class="credits-list">
<li>Multi-level garden decking: <a href="https://commons.wikimedia.org/wiki/File:Backyard_deck.JPG" rel="noopener">"Backyard deck"</a> by JDoorjam, <a href="https://creativecommons.org/licenses/by/2.5/" rel="noopener">CC BY 2.5</a>.</li>
<li>Composite decking &amp; glass balustrade: <a href="https://commons.wikimedia.org/wiki/File:Deck-bois-composite.jpg" rel="noopener">"Deck bois composite"</a> by Ulysse17 (Geolam), <a href="https://creativecommons.org/licenses/by-sa/3.0/" rel="noopener">CC BY-SA 3.0</a>.</li>
<li>Decking installation: <a href="https://commons.wikimedia.org/wiki/File:Building_our_deck_2.JPG" rel="noopener">"Building our deck 2"</a> by Kenneth William Watkins, <a href="https://creativecommons.org/licenses/by-sa/4.0/" rel="noopener">CC BY-SA 4.0</a>.</li>
<li>Deck repairs: <a href="https://commons.wikimedia.org/wiki/File:Timber_Deck_Repairs.jpg" rel="noopener">"Timber Deck Repairs"</a> by Ridunwig, <a href="https://creativecommons.org/publicdomain/zero/1.0/" rel="noopener">CC0 1.0</a>.</li>
<li>Board close-ups, steel balustrade decks and coastal deck steps from <a href="https://stocksnap.io" rel="noopener">StockSnap.io</a> (CC0): <a href="https://stocksnap.io/photo/wood-texture-BJWPE8ABOZ">hardwood grain</a>, <a href="https://stocksnap.io/photo/wood-texture-CMLVPWCDSF">board spacing</a>, <a href="https://stocksnap.io/photo/blue-sky-8E7296FED5">steel balustrade walkway</a>, <a href="https://stocksnap.io/photo/sea-pier-GJ191GHM5D">coastal deck steps</a>.</li>
</ul>''', 'index, follow')

def privacy():
    return simple_page('privacy', 'Privacy notice', '''<p class="eyebrow">Privacy</p><h1>Privacy notice</h1>
<p><em>Placeholder privacy notice: please review and adapt it to how your business actually handles data before launch.</em></p>
<h2>Who we are</h2><p>Kernow Decking Co. ([BASE_TOWN], Cornwall) is responsible for the personal information you give us through this website. Contact: <a href="mailto:[EMAIL]">[EMAIL]</a>, <a href="tel:[PHONE_INTL]">[PHONE]</a>.</p>
<h2>What we collect</h2><p>When you send an enquiry we collect your name, phone number, email address, postcode, project type and message.</p>
<h2>How we use it</h2><p>We use it only to respond to your enquiry, prepare a quote and carry out any work you ask us to do. We do not sell your data or use it for unrelated marketing.</p>
<h2>How long we keep it</h2><p>Enquiries that do not lead to work are deleted within 12 months. Customer records are kept as long as needed for guarantees, accounting and legal obligations.</p>
<h2>Your rights</h2><p>Under UK GDPR you can ask to see, correct or delete the information we hold about you. Contact us using the details above. You can also complain to the Information Commissioner's Office (ico.org.uk).</p>
<h2>Cookies</h2><p>This website does not use tracking or advertising cookies.</p>''')

def thanks():
    return simple_page('thank-you', 'Thank you', '<p class="eyebrow">Enquiry sent</p><h1>Thank you, we have your decking enquiry</h1><p>We will be in touch soon, usually within one working day. If it is urgent, call us on <a href="tel:[PHONE_INTL]">[PHONE]</a>.</p><p><a class="btn btn-navy" href="index.html">Back to the home page</a></p>')

def notfound():
    return simple_page('404', 'Page not found', '<p class="eyebrow">404</p><h1>Sorry, that board has gone missing</h1><p>The page you were looking for could not be found. Try our <a href="index.html">decking Cornwall home page</a>, our <a href="composite-decking-cornwall.html">composite decking</a> or <a href="deck-repairs-cornwall.html">deck repairs</a> pages.</p><p><a class="btn btn-navy" href="index.html">Back to the home page</a></p>')

def apply_cfg(html):
    for k, v in CFG.items():
        if k.startswith('[') and v:
            html = html.replace(k, v)
    return html

def write(name, html):
    with open(os.path.join(ROOT, name), 'w', encoding='utf-8') as f:
        f.write(apply_cfg(html))

def nav_options():
    from nav_options import page
    hero = ('assets/img/' + HERO_NAME + '-1280.webp') if HERO_PHOTO else 'assets/img/cornish-sunset-sea.svg'
    return page(head('Navigation options | Kernow Decking Co.', 'Header design options for Kernow Decking Co.', 'nav-options', robots='noindex, nofollow'), SERVICES, hero, oak_header(nav_id='nav-opt-a', extra_cls=' oak-demo'))

def main():
    pages = {'index.html': home(), 'nav-options.html': nav_options(), 'credits.html': credits(),
             'privacy.html': privacy(), 'thank-you.html': thanks(), '404.html': notfound()}
    for s in SERVICES: pages[s['slug'] + '.html'] = service_page(s)
    for n, h in pages.items(): write(n, h)
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    order = [('index', '1.0')] + [(s['slug'], '0.9') for s in SERVICES] + [('credits', '0.1')]
    for slug, p in order:
        sm.append(f'  <url><loc>{url(slug)}</loc><lastmod>{TODAY}</lastmod><priority>{p}</priority></url>')
    sm.append('</urlset>')
    write('sitemap.xml', '\n'.join(sm) + '\n')
    print(len(pages), 'pages written')

if __name__ == '__main__':
    main()
