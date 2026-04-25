---
layout: page
permalink: /stellar-explorer/
title: Stellar Explorer
description: Interactive browser-based visualiser for a MESA r24.08.1 + GYRE 1 M☉ stellar evolutionary track.
nav: true
nav_order: 3
---

**Stellar Explorer** is a small, self-contained browser tool for exploring a single stellar evolutionary track computed with the **MESA** stellar-evolution code (r24.08.1) and post-processed for non-radial oscillations with **GYRE**. The track is a solar-metallicity ([Fe/H] = 0.00), 1 M☉ run from pre-main-sequence contraction through white-dwarf cooling.

The app runs entirely client-side. The underlying track is streamed as an HDF5 file (~33 MB) from a companion public repository on first load and decoded in the browser. No server, no installation, no file upload.

## What it shows

- **HR diagram** with phase-coloured points sampled by HR-curve arc length (PMS, ZAMS, MS, SGB, RGB, He-flash, HeCB, RC, AGB, post-AGB, WD).
- **Animated stellar interior** at each selected model, with convective and radiative zones, opacity, and burning shells.
- **Profile panels** for T, P, ρ, ε<sub>nuc</sub>, N², κ on log axes where the dynamic range warrants.
- **Schwarzschild ↔ Ledoux** stability toggle in the propagation panel.
- **Asteroseismic spectrum**: PSD, échelle diagram with mode-type colouring (p / g / mixed), and a propagation diagram. Mode frequencies, ℓ, n<sub>g</sub>, n<sub>p</sub>, n<sub>pg</sub>, and E<sub>norm</sub> come directly from GYRE; radial-displacement eigenfunctions are reconstructed by JWKB (Cowling) from the GYRE-format equilibrium structure.

## Data source

The track is the direct output of an in-house MESA r24.08.1 evolutionary run with GYRE oscillation post-processing.

- Paxton, B., et al. 2011, _ApJS_ 192, 3 (MESA paper I)
- Townsend, R. H. D., Teitler, S. A. 2013, _MNRAS_ 435, 3406 (GYRE)

The HDF5 file is hosted at [github.com/AndreasWNeitzel/stellar-explorer-data](https://github.com/AndreasWNeitzel/stellar-explorer-data).

[**Launch Stellar Explorer**](/stellar-explorer/app.html){: .btn .btn-primary}

_First load fetches ~33 MB of data; the browser caches the file, so subsequent visits are much faster._
