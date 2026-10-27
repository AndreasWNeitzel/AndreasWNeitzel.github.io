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
<div class="prose"><p>HAYDNsim is a Python package that builds synthetic stellar fields for the proposed ESA <i>HAYDN</i> mission and turns them into per-star inputs for the HAYDN Noise Estimator. It serves the mission proposal, which is described on <a href="{{ '/guide/haydn/' | relative_url }}">its own page</a>; this page is about the pipeline. The paper is in preparation, so this page keeps to what the poster and the talk below have already shown.</p></div>

<figure class="panel blueprint guide-wide" data-build>
  {% include figures/haydn-pipeline.svg %}
  <figcaption class="credit">The six stages, read left to right: the archive data (a <i>Gaia</i> DR3 cone to G = 18.5, HST photometry of the core, and the catalogues of Harris 2010, Baumgardt and Hilker 2018, Hunt and Reffert 2024 and Forbes and Bridges 2010); the magnitude window where <i>Gaia</i> in the outskirts and HST in the core are both complete, which also selects the members; a King profile normalised to the HST counts in the 50 to 100 arcsec annulus and checked against <i>Gaia</i>; a TRILEGAL population calibrated to the cluster mass and bright-star counts and placed on the sky by inverse-CDF sampling; the HAYDN Noise Estimator (HNE, R. Samadi) on Deucalion, which owns the point spread function, the mask and the crowding treatment and returns a noise-to-signal ratio and a stellar pollution ratio per star; and the seismic performance model of Mosser et al. 2019. Open clusters and resolved fields skip the profile and the population steps. After the flowchart of my TASC10/KASC17 poster (Neitzel et al. 2026, doi:10.5281/zenodo.23263454) and slide 6 of my DFA Week 2026 talk; the instrument strip is from slide 2 of that talk. Outline means schematic.</figcaption>
</figure>

<figure class="panel blueprint guide-wide" data-build>
  {% include figures/haydn-field.svg %}
  <figcaption class="credit">What the noise estimator sees. Left: the telescope looks along the axis at a cluster of synthetic stars; the faint tube is the column of sky the one-degree field covers, and the plate at the near end is the detector, with the cluster landed on its pixels at 0.5 arcsec each (the current <i>HAYDN</i> study baseline). The seven ringed stars lie close to one line of sight through the core and their light (solid lines) meets on the same pixels; the depth is drawn for illustration, since the pipeline works with projected positions sampled from a King profile. Right: the target's mask in detail, the half-maximum circle of each star (one point spread function for all, a Gaussian with 90 per cent of its energy within 1.3 arcsec), and the light the mask collects split by origin. The noise estimator (HNE, R. Samadi) chooses each star's mask from its brightest pixels and returns the neighbours' share as the stellar pollution ratio, SPR = C/(S+C) over the mask; the value printed is that of this drawing, whose positions and brightnesses are schematic.</figcaption>
</figure>

<section class="section" aria-labelledby="what">
  <div class="section-head"><h2 id="what">What it does</h2></div>
  <div class="prose">
    <p>The pipeline takes a cluster from archive data to a noise forecast for every star in its field, as the schematic above shows stage by stage. In a cluster core the stars overlap, so a large share of the light in any one photometric mask belongs to the neighbours rather than to the target, and that share is what decides whether the mission can measure oscillations there.</p>
    <p>I am the sole developer of HAYDNsim. I wrote it during a secondment in A. Miglio's group at INAF-OAS Bologna, between September 2025 and March 2026, and the noise runs were made on Deucalion and on the University of Bologna clusters. The repository is private.</p>
  </div>
</section>

<figure class="panel blueprint guide-wide" data-build>
  {% include figures/haydn-crowding.svg %}
  <figcaption class="credit">The one result the proposal has published: the share of each cluster's stars whose light is mostly its neighbours', that is with a stellar pollution ratio above 0.5, for the seven globular clusters on the TASC10/KASC17 poster (Neitzel et al. 2026, doi:10.5281/zenodo.23263454). It separates the dense clusters from the open ones: 40 per cent in 47 Tucanae against 3 per cent in M4.</figcaption>
</figure>

<figure class="panel guide-wide">
  <img src="{{ '/assets/img/haydnsim/candidate-clusters-sky.webp' | relative_url }}" alt="The sky in Galactic coordinates over the Gaia map, with the footprints of the TESS, Kepler, K2, CoRoT and PLATO fields and the candidate globular clusters, open clusters and other fields marked." loading="lazy" decoding="async" width="1600" height="813">
  <figcaption class="credit">The candidate fields on the sky, from my DFA Week 2026 talk: globular clusters as circles, open clusters as triangles and other fields as squares, over the footprints of the <i>TESS</i> primary mission, <i>Kepler</i>, K2, CoRoT and the planned <i>PLATO</i> field. Background: ESA/Gaia/DPAC.</figcaption>
</figure>

<section class="section" aria-labelledby="where">
  <div class="section-head"><h2 id="where">Where it was presented</h2></div>
  <ul class="list prose">
    <li>Poster, TASC10/KASC17, Aarhus, July 2026: <a href="https://doi.org/10.5281/zenodo.23263454">doi:10.5281/zenodo.23263454</a>.</li>
    <li>Talk, DFA Week 2026, Porto, April 2026: photometric simulations of dense star clusters for <i>HAYDN</i>.</li>
    <li>The mission itself: <a href="{{ '/guide/haydn/' | relative_url }}">What is <i>HAYDN</i>?</a></li>
  </ul>
</section>
