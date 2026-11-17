# -*- coding: utf-8 -*-
"""Kernow Decking Co. static site generator.
Usage:  python3 tools/build.py
Assembles every .html page from src/partials/ plus tools/site_data.py and tools/site-config.json,
and bundles and minifies src/css and src/js into assets/css/styles.css and assets/js/main.js.
No dependencies beyond Python 3. The generated HTML and bundled assets are committed, so the site
can be uploaded as-is without running this. See EDITING.md for where to change things."""
import json, os, re
from html import escape as e
from site_data import SERVICES, HOME_FAQS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

IMG_DIR = os.path.join(ROOT, 'assets', 'img')

def photo_widths(stem):
    """Pixel widths of responsive variants for a project photo stem, smallest first."""
    ws = []
    prefix = stem + '-'
    if os.path.isdir(IMG_DIR):
        for name in os.listdir(IMG_DIR):
            if name.startswith(prefix) and name.endswith('.jpg'):
                mid = name[len(prefix):-4]
                if mid.isdigit():
                    ws.append(int(mid))
    return sorted(set(ws))

def photo_size(stem):
    """width, height of the canonical (largest) JPG, used for width/height attributes."""
    path = os.path.join(IMG_DIR, stem + '.jpg')
    with open(path, 'rb') as f:
        data = f.read(256 * 1024)
    # JPEG SOF
    i = 0
    while i < len(data) - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        m = data[i+1]
        if m in (0xC0, 0xC1, 0xC2):
            h = (data[i+5] << 8) | data[i+6]
            w = (data[i+7] << 8) | data[i+8]
            return w, h
        if m == 0xD8 or m == 0x01 or (0xD0 <= m <= 0xD9):
            i += 2
            continue
        if i + 3 >= len(data):
            break
        seglen = (data[i+2] << 8) | data[i+3]
        i += 2 + seglen
    raise RuntimeError('could not read JPEG size for %s' % stem)

def picture(stem, alt, loading='lazy', sizes='(min-width:820px) 25vw, 50vw'):
    """Responsive <picture> with WebP + JPG. Lightbox links should use assets/img/{stem}.jpg."""
    w, h = photo_size(stem)
    widths = photo_widths(stem) or [w]
    srcset_w = ', '.join(f'assets/img/{stem}-{tw}.webp {tw}w' for tw in widths)
    srcset_j = ', '.join(f'assets/img/{stem}-{tw}.jpg {tw}w' for tw in widths)
    mid = widths[len(widths)//2]
    return (
        f'<picture>'
        f'<source type="image/webp" srcset="{srcset_w}" sizes="{sizes}">'
        f'<img src="assets/img/{stem}-{mid}.jpg" srcset="{srcset_j}" sizes="{sizes}" '
        f'alt="{e(alt)}" width="{w}" height="{h}" loading="{loading}">'
        f'</picture>'
    )



def oak_photo_figure(stem, alt, sizes, caption=None, extra_class=''):
    """Project photo in the same mitred oak plank frame as the header logo."""
    classes = ' '.join(c for c in ('framed', 'oak-frame', 'photo-frame', extra_class) if c)
    cap = f'<figcaption>{e(caption)}</figcaption>' if caption else ''
    return (
        f'<figure class="{classes}">'
        '<span class="fr fr-t" aria-hidden="true"></span>'
        '<span class="fr fr-r" aria-hidden="true"></span>'
        '<span class="fr fr-b" aria-hidden="true"></span>'
        '<span class="fr fr-l" aria-hidden="true"></span>'
        f'<span class="oak-panel">{picture(stem, alt, sizes=sizes)}</span>'
        '<span class="oak-screws" aria-hidden="true"></span>'
        f'{cap}</figure>'
    )


PARTIALS = os.path.join(ROOT, 'src', 'partials')
SRC_CSS = os.path.join(ROOT, 'src', 'css')
SRC_JS = os.path.join(ROOT, 'src', 'js')
_VAR = re.compile(r'\{\{([A-Z][A-Z0-9_]*)\}\}')

def _bundle_list(folder):
    manifest = os.path.join(folder, 'BUNDLE.txt')
    names = [ln.strip() for ln in open(manifest, encoding='utf-8') if ln.strip() and not ln.startswith('#')]
    return [os.path.join(folder, n) for n in names]

def render(name, **ctx):
    """Fill {{VARS}} in a src/partials file. Values are inserted as given (already escaped if needed)."""
    raw = open(os.path.join(PARTIALS, name), encoding='utf-8').read()
    missing = [k for k in _VAR.findall(raw) if k not in ctx]
    if missing:
        raise KeyError('partial %s missing values for: %s' % (name, ', '.join(missing)))
    return _VAR.sub(lambda m: str(ctx[m.group(1)]), raw)

def _strip_css_comments(src):
    out, i, n, in_s = [], 0, len(src), None
    while i < n:
        c = src[i]
        if in_s:
            out.append(c)
            if c == '\\\\' and i + 1 < n:
                out.append(src[i + 1]); i += 2; continue
            if c == in_s:
                in_s = None
            i += 1
            continue
        if c in ('"', "'"):
            in_s = c; out.append(c); i += 1; continue
        if c == '/' and i + 1 < n and src[i + 1] == '*':
            i += 2
            while i + 1 < n and not (src[i] == '*' and src[i + 1] == '/'):
                i += 1
            i += 2
            continue
        out.append(c); i += 1
    return ''.join(out)

def minify_css(src):
    text = _strip_css_comments(src)
    text = re.sub(r'[ \t\n\r\f]+', ' ', text)
    text = re.sub(r' ?([{}:;,>]) ?', r'\1', text)
    return text.strip()

def _strip_js_comments(src):
    """Strip // and /* */ comments without touching strings or regex literals."""
    out, i, n = [], 0, len(src)
    in_s = None
    prev_code = ' '
    while i < n:
        c = src[i]
        if in_s:
            out.append(c)
            if c == '\\\\' and i + 1 < n:
                out.append(src[i + 1]); i += 2; continue
            if c == in_s:
                in_s = None
            i += 1
            continue
        if c in ('"', "'"):
            in_s = c; out.append(c); prev_code = c; i += 1; continue
        if c == '/' and i + 1 < n and src[i + 1] == '*':
            i += 2
            while i + 1 < n and not (src[i] == '*' and src[i + 1] == '/'):
                i += 1
            i += 2
            out.append(' ')
            continue
        if c == '/' and i + 1 < n and src[i + 1] == '/':
            # Could be a comment, or the start of a regex that happens to look like one
            # (we don't have // regexes). Treat as a line comment.
            while i < n and src[i] not in '\n\r':
                i += 1
            continue
        if c == '/' and prev_code in '(,=:[!&|?{};~+%^\n\r\t ':
            # Regex literal
            out.append(c); i += 1
            while i < n:
                d = src[i]; out.append(d)
                if d == '\\\\' and i + 1 < n:
                    out.append(src[i + 1]); i += 2; continue
                if d == '/':
                    i += 1
                    while i < n and src[i].isalpha():
                        out.append(src[i]); i += 1
                    break
                i += 1
            prev_code = '/'
            continue
        out.append(c)
        if not c.isspace():
            prev_code = c
        i += 1
    return ''.join(out)

def minify_js(src):
    text = _strip_js_comments(src)
    text = re.sub(r'[ \t]*\n[ \t]*', '\n', text)
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip() + '\n'

ASSET_V = '20261117v21'

def _bust_css_urls(css):
    """Append a version query to every file url() so Hostinger's long CDN cache cannot serve stale textures."""
    def repl(m):
        q, path = m.group(1), m.group(2)
        if path.startswith('data:') or '?' in path:
            return m.group(0)
        return f'url({q}{path}?v={ASSET_V}{q})'
    return re.sub(r'url\((["\']?)([^)"\']+)\1\)', repl, css)

def bundle_assets():
    """Concatenate src/css and src/js in manifest order, minify, write the public assets."""
    css_parts = [_strip_css_comments(open(p, encoding='utf-8').read()) for p in _bundle_list(SRC_CSS)]
    css = '/* Kernow Decking Co. — bundled from src/css; edit the source files and run python3 tools/build.py */\n' + _bust_css_urls(minify_css('\n'.join(css_parts))) + '\n'
    js_parts = [open(p, encoding='utf-8').read() for p in _bundle_list(SRC_JS)]
    js = '/* Kernow Decking Co. — bundled from src/js; edit the source files and run python3 tools/build.py */\n' + minify_js('\n'.join(js_parts))
    os.makedirs(os.path.join(ROOT, 'assets', 'css'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'assets', 'js'), exist_ok=True)
    with open(os.path.join(ROOT, 'assets', 'css', 'styles.css'), 'w', encoding='utf-8') as f:
        f.write(css)
    with open(os.path.join(ROOT, 'assets', 'js', 'main.js'), 'w', encoding='utf-8') as f:
        f.write(js)

CFG = json.load(open(os.path.join(os.path.dirname(__file__), 'site-config.json')))
TODAY = '2026-11-17'
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
   {"@type": "Offer", "itemOffered": {"@type": "Service", "name": s['h1']}} for s in SERVICES]}
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

def load_reviews():
    """Normalise tools/site-config.json reviews. sample:true entries must never appear on public pages."""
    out = []
    raw = CFG.get('reviews') or []
    if not isinstance(raw, list):
        return out
    for r in raw:
        if not isinstance(r, dict):
            continue
        quote = (r.get('quote') or '').strip()
        if not quote:
            continue
        try:
            rating = int(r.get('rating') or 5)
        except (TypeError, ValueError):
            rating = 5
        out.append({
            'quote': quote,
            'name': (r.get('name') or '').strip() or 'Customer',
            'area': (r.get('area') or '').strip(),
            'project': (r.get('project') or '').strip(),
            'rating': max(1, min(5, rating)),
            'sample': bool(r.get('sample')),
        })
    return out

def published_reviews():
    return [r for r in load_reviews() if not r['sample']]

def review_url():
    return (CFG.get('[GOOGLE_REVIEW_URL]') or CFG.get('reviews_url') or '').strip()

def reviews_ld(items):
    """AggregateRating / Review JSON-LD for genuine published reviews only."""
    if not items:
        return []
    ratings = [r['rating'] for r in items]
    return [{
        "@context": "https://schema.org",
        "@type": "HomeAndConstructionBusiness",
        "@id": SITE + "#business",
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": str(round(sum(ratings) / len(ratings), 1)),
            "bestRating": "5",
            "worstRating": "1",
            "reviewCount": str(len(items)),
        },
        "review": [{
            "@type": "Review",
            "author": {"@type": "Person", "name": r['name']},
            "reviewBody": r['quote'],
            "reviewRating": {"@type": "Rating", "ratingValue": str(r['rating']), "bestRating": "5", "worstRating": "1"},
        } for r in items],
    }]

def stars_html(n, of=5):
    bits = []
    for i in range(of):
        fill = '#C9A66B' if i < n else 'none'
        bits.append(
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="%s" stroke="#8A6A3C" stroke-width="1.2" '
            'stroke-linejoin="round" d="M12 2.6l2.7 6.4 6.9.6-5.2 4.6 1.6 6.7L12 17.2 6 20.9l1.6-6.7-5.2-4.6 6.9-.6z"/></svg>' % fill
        )
    return '<p class="review-stars" aria-label="%s out of %s stars">%s</p>' % (n, of, ''.join(bits))

def review_card(r, labelled_sample=False):
    loc = e(r['name']) + (', ' + e(r['area']) if r['area'] else '')
    tag = '<span class="review-tag">%s</span>' % e(r['project']) if r['project'] else ''
    sample = '<span class="review-sample-tag">Sample</span>' if labelled_sample else ''
    klass = 'review-card is-sample' if labelled_sample else 'review-card'
    return (
        '<article class="%s" role="listitem">'
        '<div class="review-plank" aria-hidden="true"></div>%s'
        '%s'
        '<blockquote><span class="review-mark" aria-hidden="true">&ldquo;</span><p>%s</p></blockquote>'
        '<footer class="review-by"><cite>%s</cite>%s</footer>'
        '</article>'
    ) % (klass, sample, stars_html(r['rating']), e(r['quote']), loc, tag)

def reviews_cta():
    href = review_url()
    if href:
        return (
            '<p class="reviews-cta"><a class="btn btn-brass" href="%s" target="_blank" '
            'rel="noopener nofollow">Leave us a review</a></p>' % e(href)
        )
    return '<p class="reviews-cta"><a class="btn btn-brass" href="#" aria-disabled="true">Leave us a review</a></p>'

def reviews_section(items, labelled_samples=False):
    if not items:
        return ''
    cards = '\n      '.join(review_card(r, labelled_sample=labelled_samples) for r in items)
    return (
        '<section class="section bg-navy reviews-section" id="reviews" aria-labelledby="reviews-title">\n'
        '  <div class="container">\n'
        '    <header class="section-head light"><p class="eyebrow">Customer reviews</p>\n'
        '      <h2 id="reviews-title">What our decking customers say</h2></header>\n'
        '    <div class="review-track" role="list">\n'
        '      %s\n'
        '    </div>\n'
        '    %s\n'
        '  </div>\n'
        '</section>\n'
    ) % (cards, reviews_cta())


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

HOME_OG_ALT = 'Decking in Cornwall: a wooden deck looking out to a sunset sea and lighthouse'

def head(title, desc, slug, extra_ld=(), robots='index, follow', preload_hero=False, og_image=None, og_alt=None):
    lds = '\n'.join(ld(x) for x in [BUSINESS, *extra_ld])
    if preload_hero and HERO_PHOTO:
        pre = (f'<link rel="preload" as="image" type="image/webp" imagesrcset="assets/img/{HERO_NAME}-768.webp 768w, assets/img/{HERO_NAME}-1280.webp 1280w, assets/img/{HERO_NAME}-1920.webp 1920w" imagesizes="100vw">\n')
    elif preload_hero:
        pre = '<link rel="preload" as="image" href="assets/img/hero-deck-perspective-cornwall.webp">\n'
    else:
        pre = ''
    return render('head.html',
        TITLE=e(title), DESC=e(desc), ROBOTS=robots,
        CANONICAL=url(slug),
        OG_IMAGE=og_image or (SITE + 'assets/img/kernow-decking-cornwall-og.jpg'),
        OG_ALT=e(og_alt or HOME_OG_ALT),
        PRE=pre, LDS=lds, ASSET_V=ASSET_V,
    )

MAIN_NAV = [('index', 'Home'), ('about', 'About'), ('gallery', 'Gallery'), ('faq', 'FAQ'), ('contact', 'Contact')]

def oak_header(current='', nav_id='main-nav', extra_cls=''):
    """Live site header: smoked-oak plank bar + logo in a mitred plank frame (also used as Option A on nav-options.html)."""
    def cur(s): return ' aria-current="page"' if s == current else ''
    nav_items = ''.join(f'<li><a href="{href(slug)}"{cur(slug)}>{label}</a></li>' for slug, label in MAIN_NAV)
    return render('header.html',
        EXTRA_CLS=extra_cls, NAV_ID=nav_id, NAV_ITEMS=nav_items, PHONE_SVG=PHONE_SVG,
    )


def header(current):
    return oak_header(current)

def planks(cls=''):
    klass = 'planks ' + cls if cls else 'planks'
    def board(n):
        screws = ''.join(f'<i class="scr s{i}"></i>' for i in range(1, 5))
        return f'<span class="plank p{n}">{screws}</span>'
    return render('planks.html', CLASS=klass, BOARDS=board(1) + board(2))


def photo_scene(content):
    p = 'assets/img/' + HERO_NAME
    return render('hero-photo.html',
        SRCSET_WEBP=f'{p}-768.webp 768w, {p}-1280.webp 1280w, {p}-1920.webp 1920w',
        IMG=f'{p}-1280.jpg',
        SRCSET_JPG=f'{p}-1280.jpg 1280w, {p}-1920.jpg 1920w',
        ALT=e(HERO_ALT), CONTENT=content,
    )


def scene(content, cls=''):
    return render('hero-scene.html', CLS=cls, CONTENT=content)


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
    return scene(render('page-hero.html',
        BREADCRUMBS=breadcrumb_html(items), KICKER=e(kicker), H1=e(h1), LEAD=e(lead),
        CTA2_HREF=c2[1], CTA2_LABEL=e(c2[0]),
    ), 'scene-page')



def compact_hero(items, kicker, h1, lead):
    """Short dark oak-trimmed page intro: eyebrow, H1 and one lead line."""
    return (
        '<section class="compact-hero">\n'
        '  <div class="container">\n'
        f'    {breadcrumb_html(items)}\n'
        f'    <p class="eyebrow">{e(kicker)}</p>\n'
        f'    <h1>{e(h1)}</h1>\n'
        f'    <p class="hero-lead">{e(lead)}</p>\n'
        '  </div>\n'
        '  <div class="compact-hero-plank" aria-hidden="true"></div>\n'
        '</section>\n'
    )


def faq_cards(faqs, open_first=True):
    items = []
    for i, (q, a) in enumerate(faqs):
        opened = ' open' if open_first and i == 0 else ''
        items.append(
            f'<details class="faq-card"{opened}>'
            f'<summary>{e(q)}<span class="faq-toggle" aria-hidden="true"></span></summary>'
            f'<div class="faq-a"><p>{e(a)}</p></div>'
            f'</details>'
        )
    return '<div class="faq-cards">\n' + '\n'.join(items) + '</div>'

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
        out.append(f'''<a class="board-card" href="contact.html">
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
      <p>{e(intro) if intro else ''} Can't see your question? Call <a href="tel:[PHONE_INTL]">[PHONE]</a> or <a href="contact.html">send us a message</a>.</p></header>
    <div class="faq-list">{items}</div>
  </div>
</section>
'''

def quote_section(source, title='Get a free decking quote', town=None):
    where = f'in {town}' if town else 'in Newquay or nearby in Cornwall'
    form = render('quote-form.html', SOURCE=e(source))
    return render('quote-section.html', TITLE=e(title), WHERE=e(where), PHONE_SVG=PHONE_SVG, FORM=form)


def footer():
    reviews_link = '<li><a href="index.html#reviews">Reviews</a></li>' if published_reviews() else ''
    svc = ''.join(f'<li><a href="{href(s["slug"])}">{e(s["short"])} Cornwall</a></li>' for s in SERVICES)
    return render('footer.html', PLANKS=planks('planks-footer'), FB_URL=FB_URL, IG_URL=IG_URL, SVC_LINKS=svc, REVIEWS_LINK=reviews_link, ASSET_V=ASSET_V)


# ---------------------------------------------------------------- pages
GALLERY_PHOTOS = [
    ('timber-deck-pergola-night-cornwall', 'Decking projects Cornwall: a lit timber deck and pergola at night', 'g-big'),
    ('composite-deck-cable-balustrade-cornwall', 'Composite deck in Cornwall with a stainless steel cable balustrade along the house', ''),
    ('timber-deck-glass-balustrade-cornwall', 'Long pine timber deck, one of our decking projects in Cornwall, with a glass balustrade', ''),
    ('timber-deck-garden-room-cornwall', 'Pine timber decking around a garden room in Cornwall, with wrap-around steps', ''),
    ('composite-deck-steps-cable-rails-cornwall', 'Split-level composite decking in Cornwall with built-in steps and a stainless steel cable balustrade', ''),
    ('timber-deck-countryside-view-cornwall', 'Pine timber deck and dining set looking out to the countryside, a decking project in Cornwall', ''),
    ('timber-deck-glass-rail-long-cornwall', 'Long pine timber deck in Cornwall with a glass balustrade, dining table and garden beyond', ''),
    ('composite-deck-cable-rail-view-cornwall', 'Stainless steel cable balustrade on a composite deck in Cornwall, keeping the garden view open', ''),
    ('composite-deck-step-lights-cornwall', 'Dark composite deck in Cornwall with built-in step lights and garden seating', ''),
    ('timber-deck-lounge-cornwall', 'Timber decking in Cornwall with outdoor lounge seating and agapanthus', ''),
    ('composite-deck-lit-steps-garden-cornwall', 'Dark composite deck in Cornwall with lit steps, a brick house and garden planting', ''),
    ('composite-deck-fascia-cable-rail-cornwall', 'Raised composite deck in Cornwall with wood-effect fascia boards and a stainless steel cable balustrade', ''),
    ('timber-deck-with-bench-cornwall', 'Light pine timber decking in Cornwall with a garden bench, planters and a chiminea', ''),
    ('composite-deck-stainless-cable-balustrade-cornwall', 'Stainless steel cable balustrade on a composite deck in Cornwall, with steps and a built-in bench', ''),
    ('timber-garden-deck-cornwall', 'Pine timber garden deck in Cornwall, enclosed by fencing with a bench and planters', ''),
    ('composite-decking-steps-cornwall', 'Built-in steps on a split-level composite deck in Cornwall, with a stainless cable balustrade', ''),
    ('timber-deck-garden-room-steps-cornwall', 'Pine timber deck and steps beside a garden room in Cornwall', ''),
    ('timber-deck-garden-room-corner-cornwall', 'Mitred corner and steps on a pine timber deck around a garden room in Cornwall', ''),
    ('composite-deck-raised-cable-balustrade-cornwall', 'Raised composite decking in Cornwall with a stainless cable balustrade beside garden steps', ''),
    ('composite-deck-walkway-cable-balustrade-cornwall', 'Composite decking walkway in Cornwall with a stainless steel cable balustrade and open views', ''),
    ('composite-deck-corner-cable-balustrade-cornwall', 'Corner of a composite deck in Cornwall with a stainless steel cable balustrade', ''),
    ('timber-deck-garden-seating-cornwall', 'Timber deck in Cornwall with an outdoor sofa, coffee table and garden planting', ''),
    ('timber-walkway-cable-rail-cornwall', 'Pale timber walkway in Cornwall with a stainless steel cable balustrade through planting', ''),
    ('timber-walkway-cable-rail-landing-cornwall', 'Timber walkway and landing in Cornwall with a stainless cable balustrade', ''),
    ('timber-walkway-cable-rail-house-cornwall', 'Raised timber walkway in Cornwall beside a house, with a stainless cable balustrade', ''),
    ('timber-walkway-cable-rail-close-cornwall', 'Close view of a timber walkway and cable balustrade on a decking project in Cornwall', ''),
    ('timber-walkway-cable-rail-curve-cornwall', 'Curved timber walkway in Cornwall with a stainless steel cable balustrade and planting', ''),
    ('timber-walkway-cable-rail-hedge-cornwall', 'Timber walkway in Cornwall running beside a hedge, with a stainless cable balustrade', ''),
    ('timber-walkway-cable-rail-wide-cornwall', 'Wide view of a pale timber deck and cable balustrade in Cornwall', ''),
]


def gallery_figures():
    def gal_sizes(cls):
        return '(min-width:820px) 50vw, 100vw' if 'g-big' in cls or 'g-wide' in cls else '(min-width:820px) 25vw, 50vw'
    return '\n'.join(
        f'<figure class="g-item{(" "+c) if c else ""}"><a href="assets/img/{stem}.jpg">{picture(stem, a, sizes=gal_sizes(c))}</a></figure>'
        for stem, a, c in GALLERY_PHOTOS
    )


def teasers():
    return (
        '<section class="section bg-limed teasers" aria-label="Find out more">'
        '<div class="container teaser-row">'
        '<article class="teaser"><p class="eyebrow">Our work</p>'
        '<h2>See our work</h2>'
        '<p>Browse recent decks, steps and balustrades we have installed for homes around Newquay and across Cornwall.</p>'
        '<a class="btn btn-navy" href="gallery.html">See our work <span aria-hidden="true">&rarr;</span></a>'
        '</article>'
        '<article class="teaser"><p class="eyebrow">Free site survey</p>'
        '<h2>Get a free quote</h2>'
        '<p>Tell us about your project and we will come back to you, usually within one working day, with a clear next step.</p>'
        '<a class="btn btn-brass" href="contact.html">Get a free quote <span aria-hidden="true">&rarr;</span></a>'
        '</article></div></section>\n'
    )


def home():
    hero = (photo_scene if HERO_PHOTO else lambda c: scene(c, 'scene-home'))(
        '<p class="eyebrow">Decking Newquay &amp; Cornwall &middot; Design &bull; Supply &bull; Install</p>'
        '<h1>Proper decking in Cornwall. <span>Built to last.</span></h1>'
        '<p class="hero-lead">Kernow Decking Co. designs, supplies and installs composite and hardwood decking, glass balustrades and garden decks from our base in Newquay, built for Cornwall’s Atlantic weather and the best of every view.</p>'
        '<div class="hero-ctas"><a class="btn btn-brass btn-lg" href="contact.html">Get a free quote</a>'
        '<a class="btn btn-glass btn-secondary btn-lg" href="gallery.html">See our work</a></div>'
        '<ul class="hero-badges"><li>Free site survey</li><li>Composite &amp; hardwood</li>'
        '<li>Glass &amp; steel balustrades</li><li>Based in Newquay</li></ul>'
    )
    intro = f'''<section class="section bg-limed intro" aria-labelledby="intro-title">
  <div class="container intro-grid">
    <div>
      <p class="eyebrow">Decking installers in Cornwall</p>
      <h2 id="intro-title">Local deck builders who know Cornish weather</h2>
      <p>Cornwall is one of the most beautiful places in Britain to sit outside, and one of the toughest on outdoor timber. Salt air, driving rain, Atlantic gales and steep gardens all shape how a deck should be designed and built.</p>
      <p>We are a Cornish decking company offering design, supply and installation under one roof. Whether you want low-maintenance <a href="composite-decking-cornwall.html">composite decking</a>, natural <a href="hardwood-decking-cornwall.html">hardwood decking</a>, a sea-view terrace with <a href="balustrades-cornwall.html">glass balustrades</a> or <a href="deck-repairs-cornwall.html">repairs to an existing deck</a>, we will design it around your home, your garden and your view.</p>
      <p>Searching for <strong>decking near me</strong>? We are based in [BASE_TOWN]. <a href="contact.html">Send us your postcode</a> for a free site survey and quote.</p>
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
    why = (
        '<section class="section bg-limed why" id="why" aria-labelledby="why-title">'
        '<div class="container why-grid">'
        + oak_photo_figure(
            'timber-deck-pergola-night-cornwall',
            'Lit timber deck and pergola at night, decking Cornwall',
            sizes='(min-width:900px) 40vw, 90vw',
            extra_class='why-media photo-natural',
        )
        + '''
    <div class="why-copy">
      <p class="eyebrow">Why choose Kernow Decking Co.</p>
      <h2 id="why-title">Decks that stand up to salt, wind and weather.</h2>
      <p>A deck in Cornwall has to cope with more than sunshine. We build every deck with the local conditions in mind.</p>
      <ul class="tick-list">
        <li><strong>Built for coastal conditions.</strong> Marine-grade stainless fixings near the sea, good drainage and ventilation underneath.</li>
        <li><strong>The right boards for your site.</strong> Composite for low maintenance, hardwood for natural character, chosen honestly.</li>
        <li><strong>Fixed, itemised quotes.</strong> No hidden extras and no pressure.</li>
        <li><strong>Tidy, respectful installers.</strong> We look after your home and leave the site clean.</li>
        <li><strong>Holiday-let friendly.</strong> We can plan work around your bookings.</li>
        <li><strong>Workmanship guarantee.</strong> [GUARANTEE_YEARS]-year guarantee on our installations.</li>
      </ul>
      <a class="btn btn-navy" href="contact.html">Book a free site survey</a>
    </div>
  </div>
</section>
'''
    )
    genuine = published_reviews()
    reviews = reviews_section(genuine) if genuine else ''
    home_ld = []
    if genuine:
        home_ld.extend(reviews_ld(genuine))
    return (
        head(
            'Decking Cornwall | Newquay Deck Builders | Kernow Decking Co.',
            'Decking in Newquay and Cornwall by Kernow Decking Co.: composite and hardwood decking, garden decks, glass balustrades and deck repairs, designed, supplied and installed. Free quotes.',
            'index', home_ld, preload_hero=True,
        )
        + header('index') + '<main id="main">\n' + hero + planks() + intro + services + planks()
        + process_section() + why + reviews + teasers() + '</main>\n' + footer()
    )


def service_page(s):
    crumbs_schema = [('Home', 'index'), (s['short'], s['slug'])]
    secs = '\n'.join(f'<h2>{e(h)}</h2>' + ''.join(f'<p>{e(p)}</p>' for p in ps) for h, ps in s['sections'])
    content = f'''<section class="section bg-limed svc-body" aria-label="{e(s["h1"])}">
  <div class="container svc-grid">
    <div class="prose">
      <p class="lead">{e(s["lead"])}</p>
      {secs}
      <p><a class="btn btn-navy" href="contact.html">Get a free quote for {e(s["short"].lower())}</a></p>
    </div>
    <aside class="svc-aside">
      {oak_photo_figure(s["img"], s["img_alt"], sizes="(min-width:900px) 28vw, 90vw", caption=s.get("img_caption") or s["short"])}
      <div class="board aside-board"><h2 class="h3">{e(s["short"])} near you</h2><p>We are a local decking team based in [BASE_TOWN], Cornwall. Searching for {e(s["short"].lower())} near you? Send us your postcode for a free site survey and quote.</p>
        <p><a class="btn btn-brass" href="contact.html">Get a free quote</a></p></div>
    </aside>
  </div>
</section>
'''
    others = f'''<section class="section bg-hardwood services" aria-labelledby="more-title">
  <div class="container"><header class="section-head light"><p class="eyebrow">More decking services</p><h2 id="more-title">Other decking services in Cornwall</h2></header>
  {service_cards(exclude=s["slug"])}</div>
</section>
'''
    og = SITE + 'assets/img/' + s.get('og', 'kernow-decking-cornwall-og.jpg')
    return (
        head(s['title'], s['desc'], s['slug'],
             [crumbs_ld(crumbs_schema), service_ld(s['h1'], s['serviceType'], s['slug'], None), faq_ld(s['faqs'])],
             robots='noindex, follow', og_image=og, og_alt=s['img_alt'])
        + header(s['slug']) + '<main id="main">\n'
        + page_hero(crumbs_schema, s['kicker'], s['h1'], s['desc'])
        + planks() + content + others + process_section()
        + faq_section(s['faqs'], f'{s["short"]} in Cornwall: FAQs')
        + '</main>\n' + footer()
    )


def about_page():
    crumbs = [('Home', 'index'), ('About', 'about')]
    title = 'Decking company Cornwall – meet Neil | Kernow Decking'
    desc = (
        'Kernow Decking Co. is a decking company Cornwall homeowners rely on for proper work. '
        'Meet Neil, the founder and installer, based near Newquay.'
    )
    hero = compact_hero(
        crumbs, 'About us', 'A decking company Cornwall can count on',
        'A decking company Cornwall homeowners can call, led by Neil and based near Newquay.'
    )
    photo = oak_photo_figure(
        'timber-deck-pergola-night-cornwall',
        'Lit timber deck and pergola at night, built by a decking company in Cornwall',
        sizes='(min-width:860px) 36vw, 90vw', extra_class='photo-natural')
    intro = (
        '<section class="section about-intro" aria-labelledby="about-neil-h2">\n'
        '  <div class="container about-intro-grid">\n'
        '    <div class="prose">\n'
        '      <h2 id="about-neil-h2">Meet Neil, our founder and installer</h2>\n'
        '      <p>Neil has years of experience in landscaping and decking, from the first site visit through to the last board. He is the founder, and the installer you will meet on site. He still leads each project himself, so you never go from a salesperson to a crew you have not met.</p>\n'
        '      <p>He started the company to do the work properly: a square frame, the right fixings, and a tidy site. He lives and works near Newquay, on the north coast of <a href="https://www.visitcornwall.com/destinations/north-cornwall/newquay" rel="noopener">Cornwall</a>, and can reach most of the county easily.</p>\n'
        '      <p>We install composite and timber decks, steps, and glass or cable balustrades. We also repair tired or unsafe decks when a repair is the honest choice. If a full rebuild would serve you better, he will say so.</p>\n'
        '    </div>\n'
        f'    {photo}\n'
        '  </div>\n'
        '</section>\n'
    )
    values = (
        '<section class="section about-values" aria-labelledby="about-values-h2">\n'
        '  <div class="container">\n'
        '    <h2 id="about-values-h2">How we work</h2>\n'
        '    <ul class="about-values-grid">\n'
        '      <li>\n'
        '        <h3>Neil on site</h3>\n'
        '        <p>He leads each project himself, from the first visit to the last board.</p>\n'
        '      </li>\n'
        '      <li>\n'
        '        <h3>Honest advice</h3>\n'
        '        <p>If a repair is enough, he will say so. If a rebuild would serve you better, he will say that too.</p>\n'
        '      </li>\n'
        '      <li>\n'
        '        <h3>Clear quotes</h3>\n'
        '        <p>A free site visit, then a fixed, itemised quote. No pressure and no hidden extras.</p>\n'
        '      </li>\n'
        '      <li>\n'
        '        <h3>Proper work</h3>\n'
        '        <p>The frame is kept square, the right fixings are used, and the site is left tidy.</p>\n'
        '      </li>\n'
        '    </ul>\n'
        '  </div>\n'
        '</section>\n'
    )
    cta = (
        '<section class="section about-cta" aria-labelledby="about-cta-h2">\n'
        '  <div class="container about-cta-row">\n'
        '    <div class="about-cta-copy">\n'
        '      <p class="eyebrow">Work with us</p>\n'
        '      <h2 id="about-cta-h2">Ready to talk about your deck?</h2>\n'
        '      <p>Look through our <a href="gallery.html">recent work</a>, or get in touch for a free site survey.</p>\n'
        '    </div>\n'
        '    <a class="btn btn-brass" href="contact.html">Get a free quote</a>\n'
        '  </div>\n'
        '</section>\n'
    )
    og = SITE + 'assets/img/about-decking-company-cornwall-og.jpg'
    return (
        head(title, desc, 'about', [crumbs_ld(crumbs)],
             og_image=og, og_alt='Lit timber deck and pergola at night, built by a decking company in Cornwall')
        + header('about') + '<main id="main">\n' + hero + intro + values + cta + '</main>\n' + footer()
    )


def gallery_page():
    crumbs = [('Home', 'index'), ('Gallery', 'gallery')]
    title = 'Decking projects Cornwall – our work | Kernow Decking'
    desc = (
        'Browse decking projects Cornwall homeowners can compare: timber and composite decks, steps, '
        'balustrades and garden rooms, from our Newquay base.'
    )
    hero = compact_hero(
        crumbs, 'Our work', 'Decking projects Cornwall',
        'A gallery of decking projects Cornwall homeowners can browse, from timber decks to lit composite steps.'
    )
    gallery = (
        '<section class="section gallery gallery-follow" id="gallery" aria-label="Project photographs">'
        '<div class="container"><div class="gallery-grid">'
        + gallery_figures() +
        '</div></div></section>\n'
    )
    about = (
        '<section class="section gallery-note" aria-label="About this gallery">\n'
        '  <div class="container">\n'
        '    <p>These photographs show decking projects Cornwall homeowners can browse. They are decks Neil and the team have installed near Newquay and across Cornwall. Look through the gallery at your own pace, then <a href="contact.html">get in touch for a free site survey</a> if something feels close to what you have in mind.</p>\n'
        '  </div>\n'
        '</section>\n'
    )
    og = SITE + 'assets/img/decking-projects-cornwall-og.jpg'
    return (
        head(title, desc, 'gallery', [crumbs_ld(crumbs)],
             og_image=og, og_alt='Decking projects Cornwall: a lit timber deck and pergola at night')
        + header('gallery') + '<main id="main">\n' + hero + gallery + about + '</main>\n' + footer()
    )


def faq_page():
    crumbs = [('Home', 'index'), ('FAQ', 'faq')]
    title = 'Decking FAQ Cornwall – your questions | Kernow Decking'
    desc = (
        'Straight answers in this decking FAQ Cornwall homeowners ask most: cost, materials, planning, '
        'timescales, repairs and where we work from our Newquay base.'
    )
    hero = compact_hero(
        crumbs, 'Help and advice', 'Decking FAQ Cornwall',
        'Straight answers in this decking FAQ Cornwall homeowners ask most, before they book a visit.'
    )
    faqs = (
        '<section class="section faq-follow" id="faq" aria-label="Frequently asked questions">'
        '<div class="container"><h2 class="faq-list-title">Common questions</h2>' + faq_cards(HOME_FAQS) + '</div></section>\n'
    )
    photo = oak_photo_figure(
        'timber-deck-countryside-view-cornwall',
        'Timber deck looking over the countryside, used on our decking FAQ Cornwall page',
        sizes='(min-width:860px) 36vw, 90vw', extra_class='photo-natural')
    after = (
        '<section class="section faq-after" aria-labelledby="faq-guide-h2">\n'
        '  <div class="container faq-after-grid">\n'
        '    <div class="prose">\n'
        '      <h2 id="faq-guide-h2">How to use this decking FAQ Cornwall guide</h2>\n'
        '      <p>These answers cover cost, materials, timing, repairs, supply and where we work. Open any item that matches your project. Because every garden is different, a visit is still the best way to get a firm price.</p>\n'
        '      <p>We are based in Newquay and work across Cornwall. For planning, most low garden decks do not need permission, yet raised decks and some listed or conservation sites may. Therefore you should confirm anything unusual with <a href="https://www.cornwall.gov.uk/planning/" rel="noopener">Cornwall Council planning</a> before work begins. We will flag concerns when we see them on site.</p>\n'
        '      <p>After you have read the answers, you can <a href="contact.html">request a free decking quote</a> or look at our <a href="gallery.html">recent work</a>.</p>\n'
        '      <p class="faq-cta"><a class="btn btn-brass" href="contact.html">Get a free quote</a></p>\n'
        '    </div>\n'
        f'    {photo}\n'
        '  </div>\n'
        '</section>\n'
    )
    og = SITE + 'assets/img/decking-faq-cornwall-og.jpg'
    return (
        head(title, desc, 'faq', [crumbs_ld(crumbs), faq_ld(HOME_FAQS)],
             og_image=og, og_alt='Timber deck looking over the countryside, used on our decking FAQ Cornwall page')
        + header('faq') + '<main id="main">\n' + hero + faqs + after + '</main>\n' + footer()
    )


def contact_page():
    crumbs = [('Home', 'index'), ('Contact', 'contact')]
    title = 'Decking quote Cornwall – free survey | Kernow Decking'
    desc = (
        'Get a decking quote Cornwall homeowners can rely on. '
        'Tell us about your project and we will arrange a free site survey, from our Newquay base.'
    )
    hero = compact_hero(
        crumbs, 'Contact us', 'Get a decking quote in Cornwall',
        'Tell us about your project and we will arrange a free site survey.'
    )
    form = render('quote-form.html', SOURCE='Contact page')
    photo_alt = 'Lit timber deck and pergola at night, after a decking quote Cornwall enquiry'
    photo = oak_photo_figure(
        'timber-deck-pergola-night-cornwall', photo_alt,
        sizes='(min-width:860px) 36vw, 90vw', extra_class='photo-natural')
    mail_svg = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 5h18v14H3z" fill="none"/><path d="m3 6 9 7 9-7"/></svg>'
    clock_svg = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>'
    icon_msg = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v11H7l-3 3z"/></svg>'
    icon_visit = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 21V8l8-5 8 5v13"/><path d="M9 21v-8h6v8"/></svg>'
    icon_quote = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="3" width="14" height="18"/><path d="M8 8h8M8 12h8M8 16h5"/></svg>'
    split = (
        '<section class="section contact-page" aria-label="Request a quote">\n'
        '  <div class="container contact-split">\n'
        '    <div class="oak-frame quote-frame">\n'
        '      <span class="fr fr-t" aria-hidden="true"></span><span class="fr fr-r" aria-hidden="true"></span><span class="fr fr-b" aria-hidden="true"></span><span class="fr fr-l" aria-hidden="true"></span>\n'
        '      <div class="oak-panel quote-panel">\n'
        f'{form}'
        '      </div>\n'
        '      <span class="oak-screws" aria-hidden="true"></span>\n'
        '    </div>\n'
        '    <aside class="contact-aside">\n'
        '      <p class="aside-place">Based near Newquay, covering Cornwall</p>\n'
        '      <ul class="contact-list">\n'
        f'        <li><span class="ci-icon">{PHONE_SVG}</span><div><small>Phone</small><a href="tel:[PHONE_INTL]">[PHONE]</a></div></li>\n'
        f'        <li><span class="ci-icon">{mail_svg}</span><div><small>Email</small><a href="mailto:[EMAIL]">[EMAIL]</a></div></li>\n'
        f'        <li><span class="ci-icon">{clock_svg}</span><div><small>Hours</small><span>[HOURS]</span></div></li>\n'
        '      </ul>\n'
        '      <p class="steps-label">What happens next</p>\n'
        '      <ol class="quote-steps">\n'
        f'        <li><span class="qs-icon" aria-hidden="true">{icon_msg}</span><strong>Send your details</strong><span class="qs-copy">A few notes and your postcode are enough to start.</span></li>\n'
        f'        <li><span class="qs-icon" aria-hidden="true">{icon_visit}</span><strong>Free site visit</strong><span class="qs-copy">If we can help, Neil will come to measure up and talk it through.</span></li>\n'
        f'        <li><span class="qs-icon" aria-hidden="true">{icon_quote}</span><strong>Fixed, itemised quote</strong><span class="qs-copy">You will see what you are paying for before you decide.</span></li>\n'
        '      </ol>\n'
        '    </aside>\n'
        '  </div>\n'
        '</section>\n'
    )
    follow = (
        '<section class="section contact-follow" aria-labelledby="contact-follow-h2">\n'
        '  <div class="container contact-follow-grid">\n'
        '    <div class="prose">\n'
        '      <h2 id="contact-follow-h2">What happens after your decking quote Cornwall enquiry</h2>\n'
        '      <p>First, we read your message and check the postcode. If we can help, we will call or email to arrange a free site survey. On that visit Neil will measure up and talk through options.</p>\n'
        '      <p>He will then send a fixed, itemised quote. Because he breaks the price down, you can see what you are paying for before you decide. There is no obligation and no hard sell. We usually reply within one working day.</p>\n'
        '      <p>Tell us the boards you like and when you would like to start. A rough size is helpful, yet you do not need to have a finished plan.</p>\n'
        '      <p>You can also call us on <a href="tel:[PHONE_INTL]">[PHONE]</a> or email <a href="mailto:[EMAIL]">[EMAIL]</a>. Our hours are [HOURS]. In the meantime, you may like to look at our <a href="gallery.html">gallery of recent work</a> or read <a href="about.html">about Neil and the company</a>.</p>\n'
        '      <p>For general questions, see the <a href="faq.html">FAQ page</a>. Planning advice is also published by <a href="https://www.cornwall.gov.uk/planning/" rel="noopener">Cornwall Council</a>.</p>\n'
        '    </div>\n'
        f'    {photo}\n'
        '  </div>\n'
        '</section>\n'
    )
    og = SITE + 'assets/img/contact-decking-quote-cornwall-og.jpg'
    return (
        head(title, desc, 'contact', [crumbs_ld(crumbs)], og_image=og, og_alt=photo_alt)
        + header('contact') + '<main id="main">\n' + hero + split + follow + '</main>\n' + footer()
    )



def simple_page(slug, title, body, robots='noindex'):
    return (head(f'{title} | Kernow Decking Co.', f'{title} – Kernow Decking Co., decking Cornwall.', slug, robots=robots)
            + header(slug) + f'<main id="main" class="section bg-limed page"><div class="container prose board page-board">{body}</div></main>\n' + footer())

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
    return simple_page('404', 'Page not found', '<p class="eyebrow">404</p><h1>Sorry, that board has gone missing</h1><p>The page you were looking for could not be found. Try our <a href="index.html">home page</a>, the <a href="gallery.html">project gallery</a> or the <a href="contact.html">contact page</a>.</p><p><a class="btn btn-navy" href="index.html">Back to the home page</a></p>')

def apply_cfg(html):
    for k, v in CFG.items():
        if k.startswith('[') and v:
            html = html.replace(k, v)
    # Empty year tokens must not appear on the live site.
    if '[NEIL_YEARS]' in html:
        html = html.replace('spent [NEIL_YEARS] years working', 'years of experience')
        html = html.replace('[NEIL_YEARS]', '')
    if '[GUARANTEE_YEARS]' in html:
        html = html.replace(
            'with a [GUARANTEE_YEARS]-year guarantee on our installations',
            'on our installations')
        html = html.replace(
            '[GUARANTEE_YEARS]-year guarantee on our installations.',
            'We stand behind the workmanship on our installations.')
        html = html.replace('[GUARANTEE_YEARS]', '')
    return html

def write(name, html):
    with open(os.path.join(ROOT, name), 'w', encoding='utf-8') as f:
        f.write(apply_cfg(html))

def nav_options():
    from nav_options import page
    hero = ('assets/img/' + HERO_NAME + '-1280.webp') if HERO_PHOTO else 'assets/img/cornish-sunset-sea.svg'
    return page(head('Navigation options | Kernow Decking Co.', 'Header design options for Kernow Decking Co.', 'nav-options', robots='noindex, nofollow'), SERVICES, hero, oak_header(nav_id='nav-opt-a', extra_cls=' oak-demo'))


def reviews_preview_page():
    """Noindex design preview. Renders sample reviews with a clear banner; never listed in the sitemap."""
    samples = [r for r in load_reviews() if r['sample']]
    items = samples or load_reviews()
    banner = (
        '<div class="sample-banner" role="status">'
        '<strong>Sample layout &mdash; placeholder reviews, not real customers</strong>'
        '</div>'
    )
    return (
        head('Reviews section preview | Kernow Decking Co.',
             'Internal preview of the reviews section layout. These are placeholder reviews, not real customers.',
             'reviews-preview', robots='noindex, nofollow')
        + header('reviews-preview')
        + banner
        + '<main id="main" class="reviews-preview-main">\n'
        + reviews_section(items, labelled_samples=True)
        + '</main>\n' + footer()
    )

def main():
    bundle_assets()
    pages = {'index.html': home(), 'about.html': about_page(), 'gallery.html': gallery_page(),
             'faq.html': faq_page(), 'contact.html': contact_page(),
             'nav-options.html': nav_options(),
             'privacy.html': privacy(), 'thank-you.html': thanks(), '404.html': notfound(),
             'reviews-preview.html': reviews_preview_page()}
    for s in SERVICES: pages[s['slug'] + '.html'] = service_page(s)
    for n, h in pages.items(): write(n, h)
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    order = [('index', '1.0'), ('about', '0.8'), ('gallery', '0.8'), ('faq', '0.7'), ('contact', '0.8')]
    for slug, pri in order:
        sm.append(f'  <url><loc>{url(slug)}</loc><lastmod>{TODAY}</lastmod><priority>{pri}</priority></url>')
    sm.append('</urlset>')
    write('sitemap.xml', '\n'.join(sm) + '\n')
    print(len(pages), 'pages written')

if __name__ == '__main__':
    main()
