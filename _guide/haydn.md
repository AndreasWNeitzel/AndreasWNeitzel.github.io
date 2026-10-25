---
title: "What is HAYDN?"
short: "HAYDN mission concept"
lede: "HAYDN is a proposed space telescope to measure the vibrations of stars in crowded clusters, where today's missions cannot tell the stars apart."
order: 7
image: /assets/img/guide/haydn.webp
image_alt: "A dense, roughly spherical cluster of stars, packed into a bright core and thinning towards the edges, against a dark background scattered with field stars."
image_credit: "ESO/M.-R. Cioni/VISTA Magellanic Cloud survey. Acknowledgment: Cambridge Astronomical Survey Unit"
image_licence: "CC BY 4.0"
image_source: "https://www.eso.org/public/images/eso1302a/"
related:
  - pos-2025-visiting-inaf-bologna
  - pres-2026-07-tasc10-poster-haydnsim
  - pres-2026-04-dfa-week-haydn
  - fund-2025-hpcvlab-deucalion-team-member
sources:
  - {label: "Miglio et al. 2021, Experimental Astronomy 51, 963 (ESA Voyage 2050 white paper)", url: "https://doi.org/10.1007/s10686-021-09711-1"}
  - {label: "Neitzel et al. 2026, HAYDNsim poster, TASC10/KASC17 (Zenodo)", url: "https://doi.org/10.5281/zenodo.23263454"}
  - {label: "Howell et al. 2022, MNRAS 515, 3184 (M4)", url: "https://doi.org/10.1093/mnras/stac1918"}
  - {label: "Howell et al. 2023, MNRAS 527, 7974 (M80)", url: "https://doi.org/10.1093/mnras/stad3565"}
---

*HAYDN* (High-precision AsteroseismologY of DeNse stellar fields) is a proposed space telescope for asteroseismology in crowded fields. Globular clusters hold thousands of stars with nearly the same age and distance, which makes them clean tests of stellar physics. Their centres are so crowded that the pixels of *Kepler*, *TESS* and *PLATO* blend many stars together. *HAYDN* would combine much finer pixels with months of observation of a single field.

The concept comes from a white paper for ESA's Voyage 2050 long-term plan (Miglio et al. 2021), and the *HAYDN* consortium now presents it as a proposed ESA M-class mission. The white paper sketched a telescope of about 90 cm with a field of about one degree, pixels of about 0.25 arcseconds against 4 arcseconds for *Kepler*, and runs of 6 to 24 months on targets such as 47 Tucanae. By 2023, seismic masses had been measured in two globular clusters, for 75 red giants in M4 and 47 giants in M80 (Howell et al. 2022, 2023).

## Where I come in

During my secondment at INAF-OAS Bologna, from September 2025 to March 2026, I built the noise-estimation and synthetic-catalogue tools for the globular and open clusters on *HAYDN*'s target list, using TRILEGAL stellar populations and King-profile sampling. The noise simulations ran on Deucalion and on the University of Bologna clusters. I presented the pipeline, HAYDNsim, on a poster at TASC10/KASC17 in Aarhus in July 2026; it is on Zenodo under CC BY 4.0.
