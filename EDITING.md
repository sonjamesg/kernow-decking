# Editing the Kernow Decking site

This is a static site. Change the source files below, then rebuild:

```bash
python3 tools/build.py
```

That writes the public HTML in the site root, plus the bundled `assets/css/styles.css` and `assets/js/main.js`. Commit those generated files with the sources so the site can be uploaded as-is. Do not edit the bundled stylesheet or script by hand — they are overwritten on every build.

## Where to change things

| What | Where |
| --- | --- |
| Phone, email, town, postcode, guarantee, domain, social URLs | `tools/site-config.json` |
| Service pages, FAQs, review copy | `tools/site_data.py` |
| Shared HTML (head, header/nav, mobile menu, plank dividers, heroes, gallery shell, quote form, footer, mobile CTA bar) | `src/partials/` |
| Page-specific copy and structure (home intro, services, process, why, privacy, 404, thank-you) | `tools/build.py` |
| Colours, fonts and other design tokens | `src/css/tokens.css` |
| Reset, simple pages, reveal and small-screen tweaks | `src/css/base.css` |
| Buttons | `src/css/buttons.css` |
| Header, logo frame, logo-shrink, desktop nav and mobile menu | `src/css/header.css` |
| Heroes | `src/css/hero.css`, `hero-photo.css`, `hero-fade.css` |
| Plank dividers | `src/css/dividers.css` |
| Gallery grid and lightbox | `src/css/gallery.css`, `lightbox.css` |
| Quote form | `src/css/form.css`, `form-frame.css` |
| Footer and mobile CTA bar | `src/css/footer.css`, `footer-brand.css` |
| Intro, services, process, why, service pages, FAQ | `src/css/sections.css`, `pages.css` |
| Type scale, later visual tweaks, reviews | `src/css/typography.css`, `refinements.css`, `reviews.css` |
| Mobile menu and scroll lock | `src/js/menu.js` |
| Logo shrink, contact bar, reveal-on-scroll | `src/js/scroll.js` |
| Gallery lightbox | `src/js/gallery.js` |
| Quote form validation and submit | `src/js/form.js` |
| Small boot (`.js` hook, year) | `src/js/boot.js` |
| Form mail (SMTP) | `contact.php` (password lives in `smtp-config.php`, not in git) |

`src/css/BUNDLE.txt` and `src/js/BUNDLE.txt` list the files in **cascade / IIFE order**. Keep that order — later files override earlier ones on purpose. The JavaScript files are concatenated into a single IIFE so the menu, lightbox and logo-shrink can share the same scroll-lock helpers.

`assets/css/nav-options.css` is only for the internal `nav-options.html` preview and is not bundled into the public stylesheet.

Placeholders such as `[PHONE]` in the partials are filled from `site-config.json` at the end of the build. Leave them as they are.

## After you edit

1. Run `python3 tools/build.py`.
2. Open `index.html` locally (or the existing local preview) and check the page you changed.
3. Commit the source *and* the generated HTML, `assets/css/styles.css` and `assets/js/main.js`.
