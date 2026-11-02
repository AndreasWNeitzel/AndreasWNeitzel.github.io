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
<div class="prose"><p>HAYDNsim is a Python package that builds synthetic stellar fields for the proposed ESA HAYDN mission and turns them into per-star inputs for the HAYDN Noise Estimator. It serves the mission proposal, which is described on <a href="{{ '/guide/haydn/' | relative_url }}">its own page</a>; this page is about the pipeline. The paper is in preparation, so this page keeps to what the poster and the talk below have already shown.</p></div>

<figure class="panel blueprint guide-wide" data-build>
  {% include figures/haydn-pipeline.svg %}
</figure>

<figure class="panel blueprint guide-wide" data-build>
  {% include figures/haydn-field.svg %}
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
  <figcaption class="credit">The share of each cluster's stars whose light is mostly its neighbours', for the seven globular clusters on the TASC10/KASC17 poster (Neitzel et al. 2026, doi:10.5281/zenodo.23263454). Star positions are schematic; the bars are the poster's values.</figcaption>
</figure>

<figure class="panel guide-wide">
  <a href="{{ '/assets/img/haydnsim/candidate-fields-sky-3000.webp' | relative_url }}"><img src="{{ '/assets/img/haydnsim/candidate-fields-sky.webp' | relative_url }}" alt="The sky in Galactic coordinates over the Gaia colour map, with the footprints of Kepler, the K2 campaigns, the CoRoT runs, the TESS continuous viewing zones and the PLATO fields, and the candidate HAYDN globular clusters, open clusters, young massive clusters and the bulge field marked and named." loading="lazy" decoding="async" width="1600" height="949"></a>
  <figcaption class="credit">The 26 target fields on the sky in Galactic coordinates, with the fields of earlier and coming missions. Background: ESA/Gaia/DPAC, CC BY-SA 3.0 IGO (acknowledgement A. Moitinho); this figure is shared under the same licence.</figcaption>
</figure>

<section class="section" aria-labelledby="where">
  <div class="section-head"><h2 id="where">Where it was presented</h2></div>
  <ul class="list prose">
    <li>Poster, TASC10/KASC17, Aarhus, July 2026: <a href="https://doi.org/10.5281/zenodo.23263454">doi:10.5281/zenodo.23263454</a>.</li>
    <li>Talk, DFA Week 2026, Porto, April 2026: photometric simulations of dense star clusters for HAYDN.</li>
    <li>The mission itself: <a href="{{ '/guide/haydn/' | relative_url }}">What is HAYDN?</a></li>
  </ul>
</section>
