---
title: "Ariel stellar characterisation. I. Homogeneous stellar parameters of 187 FGK planet host stars"
headline: "One method gave consistent temperatures, gravities and metal content for 187 planet-host stars, and roughly halved the uncertainty on their masses."
citation: "Magrini, L., Danielski, C., Bossini, D., et al. 2022, Ariel stellar characterisation. I. Homogeneous stellar parameters of 187 FGK planet host stars: Description and validation of the method, A&A, 663, A161"
doi: "10.1051/0004-6361/202243405"
arxiv: "2204.08825"
year: 2022
role: "co-author (16 of 19)"
contribution: "Bayesian stellar characterisation runs with PARAM for a subset of the sample."
card_image: "/assets/img/cards/ariel.webp"
card_credit: "ESA, CC BY-SA 3.0 IGO"
card_credit_url: "https://www.esa.int/ESA_Multimedia/Images/2024/07/Ariel_key_visual"
order: 4
math: true
extra_css: [/assets/css/kiel.css]
figure_svg: figures/magrini-2022.svg
figure_alt: "Kiel diagram of the 187 host stars: surface gravity against effective temperature, each star with error bars, sized by mass and shaded by iron abundance, with the Sun marked."
figure_caption: >-
  Where the 187 host stars sit. Each mark is one star of table A.1 at its temperature and surface
  gravity with the table's error bars, sized by mass and shaded by [Fe/H]. Filled marks are thin-disc
  stars and open marks thick-disc stars by the paper's rule in Sect. 6.2, applied to table A.2: v is the
  peculiar velocity from U, V and W, with the 220 km/s rotation of the local standard of rest taken off V.
  The Sun is marked for reference. Data: Magrini et al. 2022, A&amp;A 663, A161, tables A.1 and A.2 via
  the CDS (J/A+A/663/A161).
sources:
  - label: "Article in A&A (open access)"
    url: "https://doi.org/10.1051/0004-6361/202243405"
  - label: "Preprint, arXiv:2204.08825"
    url: "https://arxiv.org/abs/2204.08825"
  - label: "Stellar parameter tables (CDS VizieR)"
    url: "https://cdsarc.cds.unistra.fr/viz-bin/cat/J/A+A/663/A161"
---

## The question

ESA's *Ariel* mission will study the atmospheres of about a thousand planets around other stars (abstract). It measures each planet's signal as a tiny fraction of its star's light, 10 to 50 parts per million, so every host star has to be characterised first (Sect. 1). Published stellar parameters come from many different methods, and the paper argues that all hosts should be analysed with one uniform technique (abstract).

## What the team did

The *Ariel* consortium's Stellar Characterisation working group applied one method to spectra of 187 known planet hosts of types F, G and K, from the first tier of the mission's target list (Sects. 2 and 3). The method runs three times, Run 0 to Run 2 in the paper: the spectra give temperature and chemical make-up, and from Run 1 on the surface gravity comes from the star's luminosity, built from 2MASS photometry and the *Gaia* parallax, together with its mass (Sect. 3).

Masses come from isochrone fitting with PARSEC isochrones, using the temperature and metal content from the spectra and that luminosity (Sect. 4). The team checked the method on three star clusters of known age and composition: NGC 2516, NGC 3532 and NGC 6633 (Sect. 5).

## What came out

All 187 stars now have temperatures, surface gravities and metal contents from one method, with the tables at the CDS (Appendix A). The average mass uncertainty roughly halves, from 0.21 ± 0.30 to 0.10 ± 0.02 solar masses (abstract, Sect. 4). For 15 per cent of the stars the new mass differs from the published one by 20 to 40 per cent, and for 5 per cent by more than 40 per cent (Sect. 8). Most of the stars belong to the Milky Way's thin disc (Sects. 6.2 and 8).

## My part

I joined the consortium's Stellar Characterisation working group (Age, Mass and Radius sub-group) in 2021, during my MSc. For this paper I ran Bayesian stellar characterisation with PARAM for a subset of the sample. PARAM estimates a star's mass, radius and age by comparing its measured properties with a grid of stellar models.
