---
title: "What is Gaia?"
short: "The Gaia satellite"
lede: "Gaia is an ESA space telescope that mapped where nearly two billion stars are and how they move."
order: 3
image: /assets/img/guide/gaia.webp
image_alt: "Illustration of the Gaia spacecraft, a wide circular sunshield with a box-shaped body on top, in front of a whole-sky map in which the Milky Way runs across the middle as a bright band."
image_credit: "Spacecraft: ESA/ATG medialab; Milky Way: ESA/Gaia/DPAC; acknowledgement: A. Moitinho"
image_licence: "CC BY-SA 3.0 IGO"
image_source: "https://www.esa.int/ESA_Multimedia/Images/2022/06/Gaia_observes_the_Milky_Way"
related:
  - pub-2025-neitzel-manifold-learning
  - pres-2026-07-tasc10-oral-janus
  - pres-2026-10-imas13-oral-janus
  - sw-2026-arqueogal-repo
  - fund-2026-10-cpca-a1-deucalion
  - fund-2026-10-cpca-a2-marenostrum
sources:
  - {label: "ESA, Last starlight for ground-breaking Gaia (15 January 2025)", url: "https://www.esa.int/Science_Exploration/Space_Science/Gaia/Last_starlight_for_ground-breaking_Gaia"}
  - {label: "ESA, end of Gaia spacecraft operations (27 March 2025)", url: "https://www.esa.int/Science_Exploration/Space_Science/Gaia/Farewell_Gaia!_Spacecraft_operations_come_to_an_end"}
  - {label: "Gaia Collaboration, Vallenari et al. 2023, Astronomy and Astrophysics 674, A1 (DR3 summary)", url: "https://doi.org/10.1051/0004-6361/202243940"}
  - {label: "De Angeli et al. 2023, Astronomy and Astrophysics 674, A2 (DR3 BP/RP spectra)", url: "https://doi.org/10.1051/0004-6361/202243680"}
  - {label: "ESA, Gaia data release scenario", url: "https://www.cosmos.esa.int/web/gaia/release"}
---

*Gaia* is a space telescope of the European Space Agency. For more than ten years it scanned the whole sky over and over, measuring the position of each star many times. A small yearly wobble in a star's position gives its distance, and a slow drift across the sky gives its motion. *Gaia* also spread the light of hundreds of millions of stars into low-resolution spectra, which carry information on their temperature and chemical composition.

ESA launched *Gaia* on 19 December 2013. It ended science observations on 15 January 2025, after more than three trillion observations of about two billion stars and other objects, and was switched off on 27 March 2025. The third data release (DR3, 13 June 2022), built from the first 34 months of data, gives parallaxes and proper motions for about 1.46 billion sources and mean BP/RP (XP) spectra from 330 to 1050 nm for about 220 million. ESA's schedule gives 2 December 2026 for DR4, built from 66 months of data.

## Where I come in

My 2025 paper tested a method for separating stellar populations on synthetic *Gaia* samples. I am developing JANUS, a neural network that predicts APOGEE-like stellar parameters and abundances from *Gaia* XP spectra, with a reliability score for each star, and presented it at TASC10/KASC17 in July 2026 and IMAS13 in October 2026. Two approved FCT computing allocations, on Deucalion and MareNostrum 5, are for running JANUS on the XP spectra of DR3 and DR4.
