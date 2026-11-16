# Kernow Decking Co. — website

Static, multi-page website for **Kernow Decking Co.** (Cornwall, UK — *Design • Supply • Install*), built entirely around **decking in Cornwall**: a timber-deck visual identity (wood-grain boards, plank dividers with screws, a perspective deck looking out to a Cornish sunset) and local SEO on every page.

Preview (GitHub Pages): https://sonjamesg.github.io/kernow-decking/

## Pages (10)
- `index.html`: home (decking in Newquay & Cornwall)
- Services: `composite-decking-cornwall.html`, `hardwood-decking-cornwall.html`, `balustrades-cornwall.html`, `deck-repairs-cornwall.html`, `decking-design-cornwall.html`
- `credits.html`, `privacy.html`, `thank-you.html`, `404.html`, plus `sitemap.xml` and `robots.txt`

SEO: unique titles and meta descriptions, canonical and Open Graph tags, HomeAndConstructionBusiness JSON-LD (based in Newquay; areaServed Newquay and Cornwall), Service, FAQPage and BreadcrumbList schema, keyword-led image filenames and alt text, and internal links between services.
The earlier town and area pages were removed; `.htaccess` 301-redirects their old URLs to the home page.

## Placeholders
`[BASE_TOWN]` is set to Newquay in `tools/site-config.json`. Still to fill in: `[PHONE]`, `[PHONE_INTL]`, `[EMAIL]`, `[DOMAIN]`, `[POSTCODE]`, `[FACEBOOK_URL]`, `[INSTAGRAM_URL]`, `[GUARANTEE_YEARS]`, plus review text `[REVIEW 1–3]` / `[CUSTOMER NAME]` / `[TOWN]`.
Opening hours (Mon–Fri 8:00–17:30) are a suggestion — confirm. Gallery/project photos are labelled "Example image" stock photos (see `credits.html`) — replace with your own work.

### Fill them in (recommended)
1. Edit `tools/site-config.json` with your real values.
2. Run `python3 tools/build.py` — regenerates every page and `sitemap.xml` with the values filled in.
(Or find-and-replace the tokens across all files.)

## Contact form
`contact.php` emails enquiries (set `$TO_EMAIL` / `$FROM_EMAIL` — use a mailbox on your domain) and redirects to `thank-you.html`. If PHP isn't available (e.g. GitHub Pages) the form falls back to opening the visitor's email app (`mailto:`).

## Deploying to Hostinger
Upload everything to `public_html` **except** `tools/`, `README.md` and `.git`. Then update `[DOMAIN]`, rebuild, and submit `https://yourdomain/sitemap.xml` in Google Search Console.

## Tools (not needed on the server)
- `tools/build.py` + `tools/site_data.py` — page generator and all copy (services, FAQs)
- `tools/textures.py` — generates the procedural timber-board textures
- `tools/hero_deck.py` — renders the perspective hero deck
Requires Python 3 (+ numpy, Pillow for the image tools).
