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
  <figcaption class="credit">The six stages, read left to right: the archive data (a <i>Gaia</i> DR3 cone to G = 18.5, HST photometry of the core, and the catalogues of Harris 2010, Baumgardt and Hilker 2018, Hunt and Reffert 2024 and Forbes and Bridges 2010); the magnitude window where <i>Gaia</i> in the outskirts and HST in the core are both complete, which also selects the members; a King profile normalised to the HST counts in the 50 to 100 arcsec annulus and checked against <i>Gaia</i>; a TRILEGAL population calibrated to the cluster mass and bright-star counts and placed on the sky by inverse-CDF sampling; the HAYDN Noise Estimator (HNE, R. Samadi) on Deucalion, which owns the point spread function, the mask and the crowding treatment and returns a noise-to-signal ratio and a stellar pollution ratio per star; and the seismic performance model of Mosser et al. 2019. Open clusters and resolved fields skip the profile and the population steps. After the flowchart of my TASC10/KASC17 poster (Neitzel et al. 2026, doi:10.5281/zenodo.23263454) and slide 6 of my DFA Week 2026 talk; the instrument strip is from slide 2 of that talk. Outline means schematic.</figcaption>
</figure>

<section class="section" aria-labelledby="what">
  <div class="section-head"><h2 id="what">What it does</h2></div>
  <div class="prose">
    <p>The pipeline takes a cluster from archive data to a noise forecast for every star in its field, as the schematic above shows stage by stage. What it builds for 47 Tucanae, and what the noise estimator then returns, are drawn below.</p>
    <p>I designed and wrote HAYDNsim, starting from target lists and parameters provided by L. Girardi (INAF Padova), during a secondment in A. Miglio's group at INAF-OAS Bologna, from September 2025 to March 2026. The noise runs were made on Deucalion and on the University of Bologna clusters. The repository is private; the poster and the talk below describe the pipeline and its results.</p>
  </div>
</section>

<figure class="panel blueprint guide-wide" data-build>
  {% include figures/haydn-field.svg %}
  <figcaption class="credit">How a field is built, for 47 Tucanae. Left: the one degree field, with star marks placed by inverse-CDF sampling of the binned radial profile of the simulated stars (the marks are schematic; the curve beside them is the data, in 24 logarithmic bins from 2 to 1,800 arcsec), the HST normalisation annulus at 50 to 100 arcsec, and a King (1962) profile of the Harris 2010 shape for 47 Tucanae (core radius 0.36 arcmin, concentration 2.07, so a tidal radius of 42.3 arcmin) scaled to the points; the fitted amplitude itself is not published. Middle: the luminosity function of the delivered field, 91,629 stars in half-magnitude bins, from a TRILEGAL population run at the cluster mass of 853,000 solar masses (Baumgardt and Hilker 2018) at 12.8 Gyr and [Fe/H] of −0.63 (Mészáros et al. 2020). Right: the detector at 0.5 arcsec per pixel, one star as the Gaussian point spread function of the noise estimator with 90 per cent of its light inside 1.3 arcsec, the photometric mask the estimator chooses (a median of 6 pixels, 3 to 13 for 90 per cent of the stars), and neighbours whose light spills into it. Below: the noise-to-signal ratio as the quadrature sum of nine terms and the stellar pollution ratio, both as defined in the noise estimator (Marchiori et al. 2019 for the pollution ratio), and the median terms of the 1,038 stars between P 15.7 and 16.0, which do not add in quadrature because each is a median. Binned data in assets/data/haydnsim/.</figcaption>
</figure>

<figure class="panel blueprint guide-wide" data-build>
  {% include figures/haydn-noise.svg %}
  <figcaption class="credit">What the forecast looks like for 47 Tucanae: crowding becomes the largest term for stars fainter than about 14th magnitude, and the share of a star's light that comes from its neighbours rises towards 0.4 at 18th magnitude. Left and top right: medians per 0.3 mag bin of the HNE output for 91,350 stars in 47 Tucanae, the same bins as the poster's 47 Tucanae panel; the magnitude is the PLATO P band, in which the noise estimator works, about 0.23 mag brighter than <i>Gaia</i> G for these stars, and the public poster mislabels this axis as G. The per-star table is not public; the binned medians are in assets/data/haydnsim/. Bottom right: the fractions of stars with SPR above 0.5 printed on the poster for seven clusters.</figcaption>
</figure>

<section class="section" aria-labelledby="where">
  <div class="section-head"><h2 id="where">Where it was presented</h2></div>
  <ul class="list prose">
    <li>Poster, TASC10/KASC17, Aarhus, July 2026: <a href="https://doi.org/10.5281/zenodo.23263454">doi:10.5281/zenodo.23263454</a>.</li>
    <li>Talk, DFA Week 2026, Porto, April 2026: photometric simulations of dense star clusters for <i>HAYDN</i>.</li>
    <li>The mission itself: <a href="{{ '/guide/haydn/' | relative_url }}">What is <i>HAYDN</i>?</a></li>
  </ul>
</section>
