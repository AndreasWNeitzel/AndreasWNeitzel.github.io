---
title: "What is PLATO?"
short: "PLATO"
lede: "PLATO is a European space telescope made of 26 cameras that will search more than 200,000 stars for Earth-sized planets and measure those stars through their oscillations."
image: /assets/img/heroes/plato.webp
order: 7.3
image_alt: "Schematic render of the PLATO spacecraft: its 26 cameras in groups on a bench above a gold-wrapped service module, with a sunshield."
related:
  - fund-2026-05-plato-go-ngc1851-noise
  - fund-2026-05-plato-go-bss-noise
  - fund-2026-05-plato-go-accreted-noise
  - pos-2025-visiting-inaf-bologna
sources:
  - {label: "ESA, PLATO mission page", url: "https://www.esa.int/PLATO"}
  - {label: "ESA, PLATO Guest Observers Programme", url: "https://www.cosmos.esa.int/web/plato/go"}
  - {label: "Rauer et al. 2014, Experimental Astronomy 38, 249", url: "https://doi.org/10.1007/s10686-014-9383-4"}
  - {label: "Miglio et al. 2021, Experimental Astronomy 51, 963 (ESA Voyage 2050 white paper)", url: "https://doi.org/10.1007/s10686-021-09711-1"}
---

PLATO (PLAnetary Transits and Oscillations of stars) is a mission of the European Space Agency (ESA) to find Earth-sized planets around Sun-like stars, out to orbits where liquid water could exist on the surface. It will watch more than 200,000 stars with 26 small cameras, each of 81.4 megapixels, working together. The same measurements also record the faint, regular brightness changes caused by sound waves running through each star.

Those oscillations matter because planets are only as well known as their stars. Asteroseismology, the study of starquakes, gives a star's mass, radius and age far more accurately than its colour and brightness can (Rauer et al. 2014). A planet's size follows from the star's size, and the age of the system says how long the planet has had to change.

ESA plans to launch PLATO on an Ariane 6 rocket from Europe's spaceport in French Guiana, into an orbit around the Sun-Earth Lagrange point 2, 1.5 million kilometres from Earth. In November 2026 the planned launch date is early 2027.

ESA runs a Guest Observers Programme through which astronomers outside the mission team propose their own targets for PLATO, in calls for proposals that are submitted through ESA's proposal system. The crowded centres of star clusters are hard for it, because its pixels blend many stars together (the problem that HAYDN is designed to solve).

## Where I come in

In May 2026 I was a co-investigator on three PLATO guest-observer proposals. These are proposals, and none has funding or observing time attached. Each asks to observe a different kind of star: red giants in the globular cluster NGC 1851 (principal investigator A. Miglio), blue stragglers in open clusters (L. Briganti), and stars that the Milky Way captured from other galaxies (E. Leitinger).

For all three I ran the noise simulations, which forecast how well PLATO could measure the brightness of each target. I used the HAYDNsim pipeline that I wrote at INAF-OAS Bologna and the HAYDN noise estimator set to PLATO's camera configuration.
