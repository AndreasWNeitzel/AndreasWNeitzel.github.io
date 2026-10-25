---
layout: page
permalink: /stellar-explorer/
title: Stellar Explorer
nav_section: Software
description: A client-side browser tool for one stellar evolutionary track computed with MESA and GYRE.
lede: A self-contained browser tool for exploring a single stellar evolutionary track computed with MESA (r24.08.1) and post-processed for non-radial oscillations with GYRE.
---
<div class="row">
  <div class="prose">
    <p>The track is a solar-metallicity, 1 solar-mass run from pre-main-sequence contraction through white-dwarf cooling. The app runs entirely in the browser: the track is streamed as an HDF5 file of about 33 MB from a companion repository on first load and decoded on the client. No server, no installation, no upload.</p>
    <p class="no-print"><a class="button" href="{{ '/stellar-explorer/app.html' | relative_url }}">Launch Stellar Explorer (loads about 33 MB)</a></p>
  </div>
</div>
<section class="row" aria-labelledby="shows">
  <h2 id="shows">What it shows</h2>
  <div class="prose">
    <ul class="list">
      <li>An HR diagram with phase-coloured points sampled by arc length along the track (pre-main sequence, main sequence, subgiant branch, red-giant branch, helium flash, core helium burning, red clump, asymptotic giant branch, post-AGB, white dwarf).</li>
      <li>An animated stellar interior at each selected model, with convective and radiative zones, opacity and burning shells.</li>
      <li>Profile panels for temperature, pressure, density, nuclear energy generation, the Brunt-Väisälä frequency and opacity, on logarithmic axes where the dynamic range warrants.</li>
      <li>A Schwarzschild to Ledoux stability toggle in the propagation panel.</li>
      <li>An asteroseismic spectrum: power spectral density, an échelle diagram with mode-type colouring (p, g, mixed) and a propagation diagram. Mode frequencies, degrees, radial orders and normalised inertias come directly from GYRE; radial-displacement eigenfunctions are reconstructed by a JWKB (Cowling) approximation from the GYRE-format equilibrium structure.</li>
    </ul>
  </div>
</section>
<section class="row" aria-labelledby="data">
  <h2 id="data">Data and scope</h2>
  <div class="prose">
    <p>The track is the direct output of a MESA r24.08.1 evolutionary run with GYRE oscillation post-processing (Paxton et al. 2011, ApJS 192, 3; Townsend and Teitler 2013, MNRAS 435, 3406). One track, one mass, one metallicity: the tool is a visualiser of that model, not a population or inference tool. The HDF5 file is hosted at <a href="https://github.com/AndreasWNeitzel/stellar-explorer-data">github.com/AndreasWNeitzel/stellar-explorer-data</a>.</p>
  </div>
</section>
