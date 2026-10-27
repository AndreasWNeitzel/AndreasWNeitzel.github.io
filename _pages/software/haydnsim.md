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
  <figcaption class="credit">The six stages, read left to right: the archive data (a <i>Gaia</i> DR3 cone to G = 18.5, HST photometry of the core, and the catalogues of Harris 2010, Baumgardt and Hilker 2018, Hunt and Reffert 2024 and Forbes and Bridges 2010); the magnitude window where <i>Gaia</i> in the outskirts and HST in the core are both complete, which also selects the members; a King profile normalised to the HST counts in the 50 to 100 arcsec annulus and checked against <i>Gaia</i>; a TRILEGAL population calibrated to the cluster mass and bright-star counts and placed on the sky by inverse-CDF sampling; the HAYDN Noise Estimator (HNE, R. Samadi) on Deucalion, which owns the point spread function, the mask and the crowding treatment and returns a noise-to-signal ratio and a stellar pollution ratio per star; and the seismic performance model of Mosser et al. 2019, which detects the modes from the height of the oscillation envelope against the granulation and white noise under it. Stage 6 draws the power spectrum of a red giant around its frequency of maximum power, 30 μHz, in units of its own flux: granulation and envelope height from the red-giant scaling relations of Mosser et al. 2012, the modes as a comb at the asymptotic spacing with illustrative peak heights, the same in all three curves, and the white level the noise estimator gives in the 47 Tucanae run for an isolated star, a stellar pollution ratio of 0.2 and one of 0.5, for the adopted pointing-jitter level. The neighbours' light moving through the mask with the pointing jitter raises the white level about 8 times at 0.2 and 170 times at 0.5, and the height-to-background ratio falls from 3.4 to 2.7 and 0.5. Open clusters and resolved fields skip the profile and the population steps. After the flowchart of my TASC10/KASC17 poster (Neitzel et al. 2026, doi:10.5281/zenodo.23263454) and slide 6 of my DFA Week 2026 talk; the instrument strip is from slide 2 of that talk. Outline means schematic.</figcaption>
</figure>

<figure class="panel blueprint guide-wide" data-build>
  {% include figures/haydn-field.svg %}
  <figcaption class="credit">What the noise estimator sees. Left: the telescope looks along the axis at a cluster of synthetic stars; the faint tube is the column of sky the one-degree field covers, and the plate at the near end is the detector, with the cluster landed on its pixels at 0.5 arcsec each (the current <i>HAYDN</i> study baseline). The seven ringed stars lie close to one line of sight through the core and their light (solid lines) meets on the same pixels; the depth is drawn for illustration, since the pipeline works with projected positions sampled from a King profile. The tiles around the target are its pixels: the raised, lit ones are its mask, here the 13 brightest pixels of a star centred in its pixel, the size a bright star gets (the run's median is 6). Right: the mask in detail, the half-maximum circle of each star (one point spread function for all, a Gaussian with 90 per cent of its energy within 1.3 arcsec), and the light the mask collects split by origin. The noise estimator (HNE, R. Samadi) chooses each star's mask from its brightest pixels and returns the neighbours' share as the stellar pollution ratio, SPR = C/(S+C) over the mask; the value printed is that of this drawing, whose positions and brightnesses are schematic.</figcaption>
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
  <figcaption class="credit">The one result the proposal has published: the share of each cluster's stars whose light is mostly its neighbours', that is with a stellar pollution ratio above 0.5, for the seven globular clusters on the TASC10/KASC17 poster (Neitzel et al. 2026, doi:10.5281/zenodo.23263454). Each cluster is drawn as it fills the one-degree field, all at one angular scale: the same number of stars placed at radii drawn from its King profile, with the core radius and concentration of the Harris (2010) catalogue; the dashed circle is the tidal radius where it falls inside the field. Crowding follows both how compact a cluster is and how far away: 40 per cent in 47 Tucanae, 3 per cent in the loose and nearby M4, while the compact NGC 6397 stays low at 2.3 kpc and the compact M54 is high at 26.5 kpc. Star numbers in the drawings are schematic; the bars are the poster's values.</figcaption>
</figure>

<figure class="panel guide-wide">
  <a href="{{ '/assets/img/haydnsim/candidate-fields-sky-3000.webp' | relative_url }}"><img src="{{ '/assets/img/haydnsim/candidate-fields-sky.webp' | relative_url }}" alt="The sky in Galactic coordinates over the Gaia colour map, with the footprints of Kepler, the K2 campaigns, the CoRoT runs, the TESS continuous viewing zones and the PLATO fields, and the candidate HAYDN globular clusters, open clusters, young massive clusters and the bulge field marked and named." loading="lazy" decoding="async" width="1600" height="949"></a>
  <figcaption class="credit">The 26 target fields on the sky (8 globular clusters, 11 open clusters, the h and χ Persei pair, 5 young massive clusters or associations and Baade's Window in the bulge), in Galactic coordinates (Mollweide, l = 0 at the centre and increasing to the left), with the fields of earlier and coming missions: <i>Kepler</i> and the K2 campaigns C0 to C19 from K2fov, the CoRoT runs from the mission archive (VizieR B/corot), <i>TESS</i> sectors 1 to 26 from tess-point, shaded by number of sectors with the continuous viewing zones outlined in red (colours after the MIT <i>TESS</i> coverage maps), and the <i>PLATO</i> LOPS2 field from its published camera-count map (Nascimbeni et al. 2025) in the 6, 12, 18 and 24-camera tiers of the ESA LOPS2 figure, with LOPN1, provisional, after Nascimbeni et al. 2022. The K2 footprints are the <i>Kepler</i> detector with its failed modules missing: modules 3 and 7 were lost before K2 began and module 4 during Campaign 10. Globular clusters from Vasiliev and Baumgardt 2021, open clusters from Hunt and Reffert 2024, the rest from SIMBAD. Built with HAYDNsim's tooling; the larger image opens on click. Background: ESA/Gaia/DPAC, CC BY-SA 3.0 IGO (acknowledgement A. Moitinho); this figure is shared under the same licence.</figcaption>
</figure>

<section class="section" aria-labelledby="where">
  <div class="section-head"><h2 id="where">Where it was presented</h2></div>
  <ul class="list prose">
    <li>Poster, TASC10/KASC17, Aarhus, July 2026: <a href="https://doi.org/10.5281/zenodo.23263454">doi:10.5281/zenodo.23263454</a>.</li>
    <li>Talk, DFA Week 2026, Porto, April 2026: photometric simulations of dense star clusters for <i>HAYDN</i>.</li>
    <li>The mission itself: <a href="{{ '/guide/haydn/' | relative_url }}">What is <i>HAYDN</i>?</a></li>
  </ul>
</section>
