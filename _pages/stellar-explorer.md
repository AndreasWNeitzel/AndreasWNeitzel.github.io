---
layout: page
permalink: /stellar-explorer/
title: Stellar Explorer
nav_section: Software
description: A browser app that shows one stellar evolutionary track computed with MESA and GYRE.
lede: Stellar Explorer follows one star of the Sun's mass through its life, using a MESA r24.08.1 track with non-radial oscillation modes from GYRE.
---
<div class="row se-panel">
  <div class="prose">
    <p>The track is a solar-metallicity, 1 solar-mass run from pre-main-sequence contraction to white-dwarf cooling. On first load the app fetches the track, an HDF5 file of about 33 MB, from a companion repository and decodes it in the browser. It needs no server or installation and uploads nothing.</p>
    <p class="no-print"><a class="button" href="{{ '/stellar-explorer/app.html' | relative_url }}">Open Stellar Explorer (about 33 MB)</a></p>
  </div>
  <figure class="panel">{% include figures/art-hr.svg %}<figcaption class="credit">Schematic of the track the app follows, from the main sequence through the red-giant branch to the white dwarf.</figcaption></figure>
</div>
<section class="row" aria-labelledby="shows">
  <h2 id="shows">What it shows</h2>
  <div class="prose">
    <ul class="list">
      <li>An HR diagram with phase-coloured points sampled by arc length along the track (pre-main sequence, main sequence, subgiant branch, red-giant branch, helium flash, core helium burning, red clump, asymptotic giant branch, post-AGB, white dwarf).</li>
      <li>An animated stellar interior at each selected model, with convective and radiative zones, opacity and burning shells.</li>
      <li>Profile panels for temperature, pressure, density, nuclear energy generation, the Brunt-Väisälä frequency and opacity, on logarithmic axes where the range is large.</li>
      <li>A Schwarzschild to Ledoux stability toggle in the propagation panel.</li>
      <li>An asteroseismic spectrum with power spectral density, an échelle diagram coloured by mode type (p, g, mixed) and a propagation diagram. Mode frequencies, degrees, radial orders and normalised inertias come from GYRE, and radial-displacement eigenfunctions are reconstructed from the GYRE-format equilibrium structure by a JWKB (Cowling) approximation.</li>
    </ul>
  </div>
</section>
<section class="row" aria-labelledby="data">
  <h2 id="data">Data and scope</h2>
  <div class="prose">
    <p>The track is the direct output of a MESA r24.08.1 evolutionary run with GYRE oscillation post-processing (Paxton et al. 2011, ApJS 192, 3; Townsend and Teitler 2013, MNRAS 435, 3406). The tool displays that single model, at one mass and one metallicity, and does no population modelling or inference. The HDF5 file is at <a href="https://github.com/AndreasWNeitzel/stellar-explorer-data">github.com/AndreasWNeitzel/stellar-explorer-data</a>.</p>
  </div>
</section>
