# andreaswneitzel.github.io

Source of [andreaswneitzel.github.io](https://andreaswneitzel.github.io), the personal site of
Andreas W. Neitzel, PhD researcher in astrophysics and machine learning at IA and the
University of Porto.

The site is built with Jekyll and jekyll-scholar, with hand-written layouts in `_layouts/` and
`_includes/`, one stylesheet in `assets/css/site.css` and plain JavaScript in `assets/js/`.
Content lives in `_pages/`, the `_guide/` and `_papers/` collections, `_bibliography/papers.bib`
and `_data/`. The ledger files under `_data/` are generated from a private record and are not
edited by hand.

Figures and data products are rebuilt by scripts in `figures/`:

- `figures/map/build_basemap.py` builds the travel-map basemap from Natural Earth 5.1.1
  (public domain) into `assets/img/map/world_map.svg`.
- `figures/playground/build_gaia_xp_mh.py` builds the playground data from Gaia DR3.

Build locally with `bundle install` and `bundle exec jekyll build`; the workflow in
`.github/workflows/deploy.yml` builds, checks and deploys the site to the `gh-pages` branch.

## Licence

Text, figures, photographs and data in this repository are copyright Andreas W. Neitzel unless a
file states otherwise. Images in `assets/img/guide/` and `assets/img/papers/` keep the licences
stated on the pages that use them. Fonts in `assets/fonts/` are under the SIL Open Font
License 1.1. The layout code may be reused under the terms in `LICENSE`.
