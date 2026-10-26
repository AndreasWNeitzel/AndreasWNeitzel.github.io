---
layout: page
permalink: /stellar-explorer/
title: Stellar Explorer
nav_section: Software
crumb: {label: Software, url: /software/}
description: A browser app that shows one stellar evolutionary track computed with MESA and GYRE.
lede: Stellar Explorer follows one star of the Sun's mass through its life, using a MESA r24.08.1 track with non-radial oscillation modes from GYRE.
---
<div class="se-top">
  <div class="prose stack-m">
    <p>The track is a solar-metallicity, 1 solar-mass run from pre-main-sequence contraction to white-dwarf cooling. On first load the app fetches the track, an HDF5 file of about 12 MB, from a companion repository and decodes it in the browser. It needs no server or installation and uploads nothing.</p>
    <p class="no-print"><a class="btn btn--primary" href="{{ '/stellar-explorer/app.html' | relative_url }}">Open Stellar Explorer (about 12 MB)</a></p>
    <h2 id="shows">What it shows</h2>
    <ul class="list">
      <li>A timeline of the 94 stored models against fractional radius, with convective zones and nuclear burning regions, which doubles as the control for moving along the track.</li>
      <li>The HR diagram drawn from every row of the run, with the stored models coloured by phase and lines of constant radius.</li>
      <li>A cut through the star at the selected model, coloured by temperature, with convective cells, radiative zones and burning regions from that model's own profile; a ruler marks the zone boundaries, and a detail circle magnifies the centre of giants, where the burning shell sits within a hundredth of the radius. The shells move with the selected oscillation mode.</li>
      <li>Six profiles against radius: temperature, density, pressure, nuclear energy generation, opacity, and the hydrogen and helium fractions.</li>
      <li>The propagation diagram (Brunt-Väisälä and Lamb frequencies with the selected mode's cavities), the échelle diagram, the mode inertias and the mode's radial displacement. Frequencies, degrees, radial orders and inertias come from GYRE; the displacement is a JWKB reconstruction on the GYRE equilibrium structure. Eight models, at the helium flash and along the asymptotic giant branch, have no GYRE output in the run, and the panels say so.</li>
    </ul>
  </div>
  <figure class="se-fig">{% include figures/art-hr.svg %}<figcaption class="credit">The track the app follows, every row of the run. Points mark the models that carry a stored interior, coloured by phase; squares mark where a phase begins and the faint diagonals are lines of constant radius.</figcaption></figure>
</div>
<section class="section" aria-labelledby="data">
  <div class="section-head"><h2 id="data">Data and scope</h2></div>
  <div class="prose">
    <p>The track is the direct output of a MESA r24.08.1 evolutionary run with GYRE oscillation post-processing (Paxton et al. 2011, ApJS 192, 3; Townsend and Teitler 2013, MNRAS 435, 3406). The tool displays that single model, at one mass and one metallicity, and does no population modelling or inference. The HR curve is the run's full history, 13,024 models; the selectable models are the 94 for which the run saved an interior profile, each shown with its own, so no two models share an interior. The HDF5 file is at <a href="https://github.com/AndreasWNeitzel/stellar-explorer-data">github.com/AndreasWNeitzel/stellar-explorer-data</a>.</p>
  </div>
</section>
