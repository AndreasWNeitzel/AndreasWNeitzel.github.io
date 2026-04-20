# FILE_GUIDE.md — al-folio Repository Structure

This document maps the al-folio template's file structure. Read this before navigating the repo so you know what each file/folder does and what you should (and should not) touch.

---

## Files you WILL edit

### `_config.yml` (root)
Site-wide configuration: name, email, URL, social links, navigation, theme. The most important file in the repo. Changes here propagate everywhere.

**What to change:** identity fields (name, email, description), social handles (ORCID, LinkedIn, GitHub), URL.
**What to leave alone:** theme colors (unless explicitly requested), Jekyll collections config, plugin list.

Apply changes per `content/config_values.yml`.

### `_pages/about.md`
The landing/home page. Contains front matter (YAML block between `---` lines) and markdown prose below.

**What to change:** the prose below the front matter.
**What to leave alone:** the front matter itself — it controls page layout, permalink, navigation position. Only touch front matter fields if `content/about.md` explicitly tells you to.

Content source: `content/about.md`.

### `_pages/cv.md`
The CV page. al-folio's default generates a CV from `_data/cv.yml` (a structured YAML file). Andreas prefers a simpler approach: a single link to a downloadable PDF, so there is only one canonical CV (the PDF) and no version drift.

**What to change:** replace the auto-generated CV layout with the content from `content/cv.md`.

### `_pages/publications.md`
The publications page. al-folio auto-renders publications from BibTeX files in `_bibliography/`. The page itself is typically minimal — it just tells Jekyll to display the bibliography.

**What to change:** usually nothing beyond front matter. The actual publication list lives in `_bibliography/papers.bib`.

### `_bibliography/papers.bib`
BibTeX entries for all publications. al-folio reads this file and renders formatted citations on the publications page.

**What to change:** replace the template's default entries with the three entries from `content/publications.bib`.

### Pages to hide (set `nav: false`)
- `_pages/blog.md` (or `_posts/` index)
- `_pages/news.md`
- `_pages/teaching.md`
- `_pages/projects.md`
- `_pages/repositories.md`

For each: open the file, find the `nav: true` line in front matter, change to `nav: false`. Do NOT delete these files — that can break al-folio's internal references.

---

## Files you will NOT edit

### `_config.yml` sections you should NOT touch
- `plugins:` — controlled by al-folio, editing breaks the build
- `collections:` — controlled by al-folio
- `sass:` — styling internals
- `kramdown:` — markdown rendering config
- `jekyll-archives:` — archive generation

If a config change seems to require editing one of these sections, stop and ask Andreas.

### Template internals (do not edit)
- `_includes/` — reusable HTML fragments used across pages
- `_layouts/` — page layout templates
- `_sass/` — stylesheet sources
- `_plugins/` — Ruby plugins
- `Gemfile`, `Gemfile.lock` — Ruby dependencies
- `package.json` — Node dependencies (if present)
- `.github/workflows/` — GitHub Actions configs (these build the site)

Exception: if a GitHub Actions build fails with a clear error pointing to a specific config line, you may edit the minimum necessary to fix the build. Ask before making structural workflow changes.

### Assets (user uploads — do not create, do not replace with fake content)
- `assets/img/prof_pic.jpg` — Andreas will upload his headshot manually
- `assets/pdf/CV_Neitzel_Academic_Public.pdf` — Andreas will upload his CV PDF manually

If these files don't exist yet, the site will show a placeholder or broken link. That's expected until Andreas uploads them. **Do not substitute placeholder content.**

---

## al-folio directory tree (reference)

```
.
├── _bibliography/
│   └── papers.bib              ← EDIT: replace with content/publications.bib
├── _data/
│   ├── cv.yml                  ← IGNORE: we use simple PDF link instead
│   ├── coauthors.yml           ← IGNORE
│   ├── repositories.yml        ← IGNORE
│   └── venues.yml              ← IGNORE
├── _includes/                  ← DO NOT EDIT (template internals)
├── _layouts/                   ← DO NOT EDIT (template internals)
├── _pages/
│   ├── about.md                ← EDIT: prose from content/about.md
│   ├── blog.md                 ← EDIT: set nav: false
│   ├── cv.md                   ← EDIT: replace with content/cv.md
│   ├── news.md                 ← EDIT: set nav: false
│   ├── projects.md             ← EDIT: set nav: false
│   ├── publications.md         ← USUALLY LEAVE ALONE
│   ├── repositories.md         ← EDIT: set nav: false
│   └── teaching.md             ← EDIT: set nav: false
├── _plugins/                   ← DO NOT EDIT
├── _posts/                     ← IGNORE (blog posts; we have no blog)
├── _projects/                  ← IGNORE (project entries; we have none)
├── _sass/                      ← DO NOT EDIT
├── assets/
│   ├── css/                    ← DO NOT EDIT
│   ├── img/
│   │   └── prof_pic.jpg        ← USER UPLOADS (don't create)
│   ├── js/                     ← DO NOT EDIT
│   └── pdf/                    ← USER UPLOADS (CV PDF goes here)
├── _config.yml                 ← EDIT per content/config_values.yml
├── Gemfile                     ← DO NOT EDIT
├── Gemfile.lock                ← DO NOT EDIT
├── package.json                ← DO NOT EDIT
└── README.md                   ← USER-FACING, OK to edit if outdated
```

---

## How al-folio renders content

Understanding the rendering chain helps debugging:

1. **Jekyll reads `_config.yml`** on build to know the site's identity
2. **Pages in `_pages/`** with `nav: true` appear in the navigation bar
3. **The About page** uses `_layouts/about.html` (which reads from `_config.yml` for the profile block)
4. **The Publications page** uses `_layouts/bib.html` which reads `_bibliography/papers.bib` and renders each entry as a formatted citation
5. **The CV page** by default uses `_layouts/cv.html` which reads `_data/cv.yml` — **but we override this** by making `_pages/cv.md` a simple markdown page with a PDF link, bypassing `_data/cv.yml` entirely
6. **The footer** is generated from `_includes/footer.html` which reads social fields from `_config.yml`

If a change doesn't appear on the site after a build, the most common causes:
- Front matter `nav:` or `permalink:` field is wrong
- The BibTeX entry is malformed (missing comma, bad field name)
- The page references a layout that doesn't exist
- Cache issue: delete `_site/` and `.jekyll-cache/` and rebuild

---

## Safe-change checklist

Before committing any change, verify:

- [ ] File I edited is listed in "Files you WILL edit" above
- [ ] Front matter (if any) is valid YAML (no tabs, consistent indentation, quoted strings where needed)
- [ ] If I changed `_config.yml`, I only touched identity/social fields
- [ ] If I hid a page, I set `nav: false` rather than deleting the file
- [ ] Local build passes (`bundle exec jekyll build` if toolchain available)
- [ ] No placeholder text like "Your Name Here" or "Lorem ipsum" remains
- [ ] Commit message describes the change in imperative mood
