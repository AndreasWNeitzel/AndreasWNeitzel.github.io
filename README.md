# andreaswneitzel.github.io

Source of [andreaswneitzel.github.io](https://andreaswneitzel.github.io), the personal site of
Andreas W. Neitzel, PhD candidate in astronomy at IA/CAUP, University of Porto.

The site is built with Jekyll and jekyll-scholar. Layouts live in `_layouts/` and `_includes/`,
one stylesheet in `assets/css/site.css`, and the content in `_pages/`, `_bibliography/papers.bib`
and `_data/`. The data files under `_data/` are generated from a private record and are not
edited by hand.

Build locally with `bundle install` and `bundle exec jekyll build`; the workflow in
`.github/workflows/deploy.yml` builds, checks and deploys the site to the `gh-pages` branch.

## Licence

Text, figures and data in this repository are copyright Andreas W. Neitzel unless a file states
otherwise. The fonts in `assets/fonts/` are under the SIL Open Font License 1.1. The layout
code may be reused under the terms in `LICENSE`.
