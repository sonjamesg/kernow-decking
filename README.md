# Kernow Decking Co. website

Static website for **Kernow Decking Co.** (Cornwall, UK) — *Design • Supply • Install*.

Plain HTML, CSS and JavaScript with no build step, so the files can be uploaded to Hostinger
shared hosting (or any web host) exactly as they are. The only server-side file is `contact.php`,
which sends quote-form enquiries by email.

## Files

| File | What it is |
| --- | --- |
| `index.html` | The one-page site: hero, services, why us, process, gallery, areas, testimonials, FAQ, contact form |
| `contact.php` | Quote form handler (PHP `mail()`), for Hostinger |
| `thank-you.html` | Shown after a form is sent without JavaScript |
| `privacy.html`, `credits.html`, `404.html` | Privacy notice (placeholder), photo credits, not-found page |
| `assets/css/styles.css` | All styling. Brand colours are at the top (`--navy`, `--gold`, and so on) |
| `assets/js/main.js` | Mobile menu, gallery lightbox, scroll effects and form sending |
| `assets/img/` | Logo, photos, social share image |
| `assets/fonts/` | Montserrat (self-hosted, SIL Open Font Licence) |
| `sitemap.xml`, `robots.txt` | SEO files |
| `.htaccess` | Caching, compression, 404 page and an optional HTTPS redirect for Hostinger |

## 1. Fill in the placeholders

Every detail that still needs filling in is written in square brackets. Use **find and replace across
all files** (VS Code: `Ctrl+Shift+H`), and replace each token everywhere it appears:

| Placeholder | Replace with | Example |
| --- | --- | --- |
| `[PHONE]` | Phone number as people should see it | `07700 900123` |
| `[PHONE_INTL]` | The same number in international format, no spaces (used for `tel:` links and Google) | `+447700900123` |
| `[EMAIL]` | Email address enquiries should go to | `hello@kernowdecking.co.uk` |
| `[DOMAIN]` | Your domain, without `https://` or a trailing slash | `kernowdecking.co.uk` |
| `[BASE_TOWN]` | Town you are based in | `Truro` |
| `[POSTCODE]` | Business postcode (used for Google only, not shown on the page) | `TR1 2AB` |
| `[FACEBOOK_URL]` | Full Facebook page link (or delete the link) | `https://facebook.com/kernowdecking` |
| `[INSTAGRAM_URL]` | Full Instagram link (or delete the link) | `https://instagram.com/kernowdecking` |
| `[GUARANTEE_YEARS]` | Length of your workmanship guarantee in years (or remove that bullet) | `5` |

Content that also needs your attention:

- **Testimonials** (`index.html`, section `testimonials`): the three reviews are clearly marked placeholders
  (`[REVIEW 1]`, `[CUSTOMER NAME]`, `[TOWN]`). Replace them with real reviews, then delete the
  `<span class="ph-tag">Placeholder</span>` tags, the `placeholder` class and the yellow notice above them.
- **Gallery**: the photos are free stock images. Replace `assets/img/gallery-01…08-*.webp` with your own
  project photos (landscape, about 1000px wide, saved as `.webp` or `.jpg`), update the `alt` text
  and captions, then remove the yellow "Placeholder images" notice.
- **Areas covered**: edit the town list to match where you actually work.
- **Claims**: check "Fully insured", the guarantee and the opening hours (Mon–Fri 8:00–17:30) are true for you,
  in both the page and the JSON-LD block in the `<head>` of `index.html`.
- **Privacy notice** (`privacy.html`): a sensible starting point, but check it matches how you handle data.

## 2. The quote form

- On Hostinger the form posts to `contact.php`, which emails the enquiry to `[EMAIL]`.
- Open `contact.php` and check the two settings at the top: `$TO_EMAIL` (your inbox) and `$FROM_EMAIL`.
  `$FROM_EMAIL` **must be an address on your own domain** (for example `no-reply@kernowdecking.co.uk`):
  create it in hPanel → Emails, or messages may be rejected or go to spam.
- It includes spam protection (a hidden honeypot field and a minimum time check) and validates
  UK postcodes, phone numbers and email addresses.
- If PHP isn't available (for example on the GitHub Pages preview), the form opens the visitor's own
  email app with the enquiry filled in, sent to the address in the form's `data-email` attribute.
  Until `[EMAIL]` is filled in, it asks people to call or email instead.
- Send yourself a test enquiry after going live, and check your spam folder the first time.

## 3. Deploy to Hostinger

1. Fill in the placeholders (step 1) and commit.
2. In hPanel, add the domain to your hosting plan and open **File Manager** (or connect with FTP using the
   details in hPanel → Files → FTP Accounts).
3. Upload **everything in this repository** (including `.htaccess`) into `public_html/` for the domain.
   You don't need to upload `README.md`, `.git/` or `.nojekyll`.
4. Turn on the free SSL certificate in hPanel → Security → SSL, then uncomment the three HTTPS lines
   in `.htaccess`.
5. Submit `https://[DOMAIN]/sitemap.xml` in Google Search Console, and set up a Google Business Profile
   with the same name, phone and address.

Alternatively, Hostinger's **Git** deployment (hPanel → Advanced → Git) can pull this repository
straight into `public_html`.

## Preview locally

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

(The form needs PHP to send email: use `php -S localhost:8000` if PHP is installed.)

## Editing tips

- Colours: change the variables at the top of `assets/css/styles.css`. Navy `#041E37` and gold `#C98A34`
  were sampled from the logo.
- Logo: `assets/img/logo-360/720.(webp|png)` (navy text, for light backgrounds) and
  `logo-white-360/720.*` (white text, for the footer). `logo-original.jpg` is the original artwork.
- Social share image: `assets/img/og-image.jpg` (1200×630).

## Photo credits

Stock photos are CC0 (public domain) or Creative Commons Attribution. The attributions on
`credits.html` must stay on the site for as long as the CC BY photos (hero, call-to-action and
"why choose us" images) are used. If you replace them with your own photos, you can remove their credits.
