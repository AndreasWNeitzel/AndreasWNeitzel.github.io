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
    <p>The track is a solar-metallicity, 1 solar-mass run from pre-main-sequence contraction to white-dwarf cooling. On first load the app fetches the track, an HDF5 file of about 33 MB, from a companion repository and decodes it in the browser. It needs no server or installation and uploads nothing.</p>
    <p class="no-print"><a class="btn btn--primary" href="{{ '/stellar-explorer/app.html' | relative_url }}">Open Stellar Explorer (about 33 MB)</a></p>
    <h2 id="shows">What it shows</h2>
    <ul class="list">
      <li>An HR diagram with phase-coloured points sampled by arc length along the track.</li>
      <li>An animated stellar interior at each selected model, with convective and radiative zones, opacity and burning shells.</li>
      <li>Profile panels for temperature, pressure, density, nuclear energy generation, the Brunt-Väisälä frequency and opacity, on logarithmic axes where the range is large.</li>
      <li>A Schwarzschild to Ledoux stability toggle in the propagation panel.</li>
      <li>An asteroseismic spectrum with power spectral density, an échelle diagram coloured by mode type (p, g, mixed) and a propagation diagram. Mode frequencies, degrees, radial orders and normalised inertias come from GYRE, and radial-displacement eigenfunctions are reconstructed from the GYRE-format equilibrium structure by a JWKB (Cowling) approximation.</li>
    </ul>
  </div>
  <figure class="se-fig">{% include figures/art-hr.svg %}<figcaption class="credit">The track the app follows. Every point is one model of the run, coloured by phase; squares mark where a phase begins and the faint diagonals are lines of constant radius.</figcaption></figure>
</div>
<section class="section" aria-labelledby="data">
  <div class="section-head"><h2 id="data">Data and scope</h2></div>
  <div class="prose">
    <p>The track is the direct output of a MESA r24.08.1 evolutionary run with GYRE oscillation post-processing (Paxton et al. 2011, ApJS 192, 3; Townsend and Teitler 2013, MNRAS 435, 3406). The tool displays that single model, at one mass and one metallicity, and does no population modelling or inference. The HDF5 file is at <a href="https://github.com/AndreasWNeitzel/stellar-explorer-data">github.com/AndreasWNeitzel/stellar-explorer-data</a>.</p>
  </div>
</section>
