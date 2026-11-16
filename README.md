# Kernow Decking Co. — website

Static, multi-page website for **Kernow Decking Co.** (Cornwall, UK — *Design • Supply • Install*), built entirely around **decking in Cornwall**: a timber-deck visual identity (wood-grain boards, plank dividers with screws, a perspective deck looking out to a Cornish sunset) and local SEO on every page.

Preview (GitHub Pages): https://sonjamesg.github.io/kernow-decking/

## Pages (10)
- `index.html`: home (decking in Newquay & Cornwall)
- Services: `composite-decking-cornwall.html`, `hardwood-decking-cornwall.html`, `balustrades-cornwall.html`, `deck-repairs-cornwall.html`, `decking-design-cornwall.html`
- `privacy.html`, `thank-you.html`, `404.html`, plus `sitemap.xml` and `robots.txt`

SEO: unique titles and meta descriptions, canonical and Open Graph tags, HomeAndConstructionBusiness JSON-LD (based in Newquay; areaServed Newquay and Cornwall), Service, FAQPage and BreadcrumbList schema, keyword-led image filenames and alt text, and internal links between services.
The earlier town and area pages were removed; `.htaccess` 301-redirects their old URLs to the home page.

## Contact details & placeholders
Filled in via `tools/site-config.json`: domain `kernowdecking.com`, email `info@kernowdecking.com`, base town Newquay.

> **⚠️ TEMPORARY PHONE NUMBER:** `07700 900461` (+447700900461) is an Ofcom drama/fiction number that does not connect. It **must be replaced** with the real business number in `tools/site-config.json` (`[PHONE]` and `[PHONE_INTL]`), then rebuild, before launch.

Still to fill in: `[POSTCODE]`, `[GUARANTEE_YEARS]`, `[FACEBOOK_URL]`, `[INSTAGRAM_URL]` (social links stay hidden until set), plus review text `[REVIEW 1–3]` / `[CUSTOMER NAME]` / `[TOWN]`.
Opening hours (Mon–Fri 8:00–17:30) are a suggestion, so please confirm them. Gallery/project photos are labelled "Example image" stock photos; replace them with your own work.

### Fill them in (recommended)
1. Edit `tools/site-config.json` with your real values.
2. Run `python3 tools/build.py` — regenerates every page and `sitemap.xml` with the values filled in.
(Or find-and-replace the tokens across all files.)

## Contact form
`contact.php` sends enquiries over authenticated SMTP (PHPMailer, `smtp.hostinger.com:465` SSL) and redirects to `thank-you.html`. Credentials are read from `smtp-config.php`, which is gitignored. Copy `smtp-config.example.php` and set the mailbox password. If PHP isn't available (e.g. GitHub Pages) the form falls back to opening the visitor's email app (`mailto:`).

## Deploying to Hostinger
Upload everything to `public_html` **except** `tools/`, `README.md`, `.git` and `smtp-config.php`. Place `smtp-config.php` one directory above `public_html` (recommended) or inside it — `.htaccess` blocks HTTP access if it is in the web root. The password file is not in git, so it has to be uploaded separately when the site first goes live. Then submit `https://yourdomain/sitemap.xml` in Google Search Console.

## Home page hero photo
Run `python3 tools/hero_photo.py /path/to/photo.jpg` then `python3 tools/build.py`. This writes responsive WebP (768/1280/1920) + JPG fallbacks named `decking-cornwall-newquay-sea-view-deck-*` and the Open Graph image; the build switches the home hero to the photo automatically when those files exist (otherwise it uses the illustrated deck and sunset).

## Navigation options
**Header:** Option A was chosen and is live on every page: a smoked-oak plank bar with engraved brass lettering, and the logo on its white panel inside a mitred four-plank oak frame with brass screws (pure CSS + small WebP textures + 4 tiny SVG screws). The mobile menu locks page scrolling while open (works on iOS Safari and Android Chrome) and closes on link tap, Escape, or resizing to desktop.

`nav-options.html` (noindex, not linked, not in the sitemap) still shows all three header designs (A, B and C) for comparison. It can be deleted any time.

## Design
Dark smoked oak and walnut accents, brushed brass, navy and cream. Headings, nav and buttons: Roboto Slab 700/800 (the closest free match to the Unit Slab used by offermanwoodshop.com); body: IBM Plex Sans 400/600. Both are SIL Open Font License and self-hosted in `assets/fonts`. Text always sits on flat, high-contrast surfaces (WCAG AA).

## Tools (not needed on the server)
- `tools/build.py` + `tools/site_data.py` — page generator and all copy (services, FAQs)
- `tools/textures.py` — generates the procedural timber-board textures
- `tools/frame_textures.py` — generates the smoked-oak header bar and logo-frame plank textures
- `tools/hero_deck.py` renders the perspective hero deck
- `tools/hero_photo.py` makes the hero photo sizes and the OG image
- `tools/nav_options.py` builds `nav-options.html`
Requires Python 3 (+ numpy, Pillow for the image tools).
