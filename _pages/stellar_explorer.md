---
layout: page
permalink: /stellar-explorer/
title: Stellar Explorer
description: Interactive browser-based visualiser for a MIST v1.2 stellar evolutionary track.
nav: true
nav_order: 3
---

**Stellar Explorer** is a small, self-contained browser tool for exploring a single stellar evolutionary track from the MIST (MESA Isochrones and Stellar Tracks) v1.2 grid — a solar-metallicity ([Fe/H] = 0.00), 1 M☉ track.

The app runs entirely client-side. The underlying evolutionary data is streamed as an HDF5 file (~50 MB) from a companion public repository on first load and decoded in the browser. No server, no installation, no file upload.

## Data source

The stellar-structure grid is from the **MIST v1.2** release, retrieved from the [MIST web interface](https://waps.cfa.harvard.edu/MIST/).

- Choi, J. et al. 2016, _ApJ_ 823, 102
- Dotter, A. 2016, _ApJS_ 222, 8

The HDF5 file is hosted at [github.com/AndreasWNeitzel/stellar-explorer-data](https://github.com/AndreasWNeitzel/stellar-explorer-data).

[**Launch Stellar Explorer**](/stellar-explorer/app.html){: .btn .btn-primary}

_First load fetches ~50 MB of data; the browser caches the file, so subsequent visits are much faster._
