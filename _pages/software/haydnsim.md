---
layout: page
permalink: /software/haydnsim/
title: HAYDNsim
nav_section: Software
crumb: {label: Software, url: /software/}
description: HAYDNsim, the simulation pipeline Andreas W. Neitzel wrote to forecast per-star photometric noise in crowded clusters for the proposed HAYDN mission.
lede: A simulation pipeline that builds synthetic stellar fields of crowded clusters and forecasts the photometric noise of each star, written to test the proposed HAYDN mission.
extra_css: [/assets/css/haydn.css]
---
<div class="prose"><p>HAYDNsim is a Python package that builds synthetic stellar fields for the proposed ESA <i>HAYDN</i> mission and turns them into per-star inputs for the HAYDN Noise Estimator. It serves the mission proposal, which is described on <a href="{{ '/guide/haydn/' | relative_url }}">its own page</a>; this page is about the pipeline.</p></div>

<figure class="panel blueprint guide-wide" data-build>
  {% include figures/haydn-pipeline.svg %}
  <figcaption class="credit">How HAYDNsim turns a cluster into per-star noise forecasts. The six stages follow the flowchart of my TASC10/KASC17 poster (Neitzel et al. 2026, doi:10.5281/zenodo.23263454) and slide 6 of my DFA Week 2026 talk; the instrument figures are from slide 2 of that talk. The point-spread function, the aperture and the crowding treatment belong to the HAYDN Noise Estimator (HNE, R. Samadi), not to HAYDNsim.</figcaption>
</figure>

<section class="section" aria-labelledby="what">
  <div class="section-head"><h2 id="what">What it does</h2></div>
  <div class="prose">
    <p>For each target cluster the pipeline gathers the archive data (a <i>Gaia</i> DR3 cone to G = 18.5, HST photometry of the core and the literature catalogues), sets the magnitude range where both surveys are complete, fits a King profile normalised to the HST counts, and fills the field with a TRILEGAL population calibrated to the cluster's present-day mass and bright-star counts. The HAYDN Noise Estimator, written by R. Samadi, then computes for every star the noise-to-signal ratio including the light of all its neighbours, and the stellar pollution ratio. Open clusters and resolved fields skip the profile and the population steps.</p>
    <p>I designed and wrote HAYDNsim, starting from target lists and parameters provided by L. Girardi (INAF Padova), during a secondment in A. Miglio's group at INAF-OAS Bologna, from September 2025 to March 2026. The noise runs were made on Deucalion and on the University of Bologna clusters. The repository is private; the poster and the talk below describe the pipeline and its results.</p>
  </div>
</section>

<figure class="panel blueprint guide-wide" data-build>
  {% include figures/haydn-noise.svg %}
  <figcaption class="credit">What the forecast looks like for 47 Tucanae: crowding becomes the largest term for stars fainter than about 14th magnitude, and the share of a star's light that comes from its neighbours rises towards 0.4 at 18th magnitude. Left and top right: medians per 0.3 mag bin in Gaia G of the HNE output for 91,350 stars in 47 Tucanae, the same bins as the poster's 47 Tucanae panel; the per-star table is not public, the binned medians are in assets/data/haydnsim/. Bottom right: the fractions of stars with SPR above 0.5 printed on the poster for seven clusters.</figcaption>
</figure>

<section class="section" aria-labelledby="where">
  <div class="section-head"><h2 id="where">Where it was presented</h2></div>
  <ul class="list prose">
    <li>Poster, TASC10/KASC17, Aarhus, July 2026: <a href="https://doi.org/10.5281/zenodo.23263454">doi:10.5281/zenodo.23263454</a>.</li>
    <li>Talk, DFA Week 2026, Porto, April 2026: photometric simulations of dense star clusters for <i>HAYDN</i>.</li>
    <li>The mission itself: <a href="{{ '/guide/haydn/' | relative_url }}">What is <i>HAYDN</i>?</a></li>
  </ul>
</section>
