---
title: "Determination of Age and Mass for Seismic Stars in the Ariel Input Catalog"
headline: "Adding a star's oscillation frequencies, or an accurate luminosity, tightens the mass and age that stellar models give for Sun-like planet hosts, by an amount that depends on how well their temperature and metal content are known."
citation: "Neitzel, A. W. 2022, Determination of Age and Mass for Seismic Stars in the Ariel Input Catalog, MSc dissertation, Faculdade de Ciências da Universidade do Porto, supervisor D. Bossini, co-supervisor T. L. Campante, hdl:10216/147245"
handle: "10216/147245"
year: 2022
role: "MSc dissertation"
contribution: "My own dissertation: the luminosities from Gaia parallaxes and 2MASS photometry with bolometric corrections, the self-consistency tests of PARAM and its comparison with four other codes, and the characterisation of ten Ariel input catalogue stars over sixteen constraint sets. As an MSc research fellow on the BreakStarS project, I implemented the small-frequency-separation routine in PARAM."
figure: "/assets/img/papers/neitzel-2022-kippenhahn.webp"
figure_alt: "Two Kippenhahn diagrams, one above the other, showing the interior of a one solar mass star and of a 1.2 solar mass star against age. Grey circled regions mark convection, red hatched regions mark nuclear burning, and dashed lines mark the end of the main sequence, the end of the subgiant phase and the red-giant bump."
figure_caption: "How the inside of a star changes with age: for one solar mass (top) and 1.2 solar masses (bottom), the height is the fraction of the star's mass measured from the centre, grey circles mark convection and red hatching marks nuclear burning. The heavier star keeps a convective core through its main sequence, which ends in the hook that later makes its mass and age ambiguous. From the dissertation, Fig. 2.4, two MESA models at solar metallicity."
wide_figure: figures/thesis-method.svg
wide_caption: "How the dissertation turned measurements into masses and ages. Left: a star's spectrum (temperature, metal content and surface gravity from SWEET-Cat 2.0, Sousa et al. 2021; the stretch drawn carries the Mg b triplet and Fe I lines at their wavelengths, with schematic depths), its parallax and K-band brightness (a luminosity from the Gaia parallax and 2MASS KS magnitude, after MWDust reddening on the Green et al. 2019 map and a BCCode bolometric correction; the curve is the Planck spectrum at 5772 K with the KS band shaded) and its power spectrum (the large frequency separation and the frequency of maximum power, from Huber et al. 2013 for the Kepler hosts and the literature for the Ariel stars; the comb drawn uses the GYRE frequencies of a solar model, with schematic amplitudes). Above, the MESA grid of tracks following grid D1 of Moedas et al. 2022, from 0.5 to 1.8 solar masses (drawn from the Stellar Explorer's one-solar-mass track scaled by homology), and the GYRE mode frequencies that give each model its seismic parameters and critical points. In the middle PARAM (Rodrigues et al. 2017): the six constraints as likelihoods, every model on the grid weighted by its likelihood with the 68 and 95 per cent contours, and the marginals over age and mass, the age one read as a mode, a median and a 68th-percentile band. Right, the marginal distributions of mass, radius and age, with a second peak marking a double solution, and the sixteen constraint sets tried for every star, each cell filled in proportion to the age uncertainty that set gave (Chapters 4 to 6)."
extra_css: [/assets/css/papers.css, /assets/css/thesis.css]
math: true
order: 5
card_wide: true
card_image: "/assets/img/papers/neitzel-2022-kippenhahn.webp"
card_light: true
sources:
  - label: "Dissertation record, Repositório Aberto da Universidade do Porto (hdl:10216/147245)"
    url: "https://hdl.handle.net/10216/147245"
  - label: "Magrini et al. 2022, A&A 663, A161 (Ariel stellar characterisation I)"
    url: "https://doi.org/10.1051/0004-6361/202243405"
  - label: "Rodrigues et al. 2017, MNRAS 467, 1433 (PARAM)"
    url: "https://doi.org/10.1093/mnras/stx120"
  - label: "Paxton et al. 2011, ApJS 192, 3 (MESA)"
    url: "https://doi.org/10.1088/0067-0049/192/1/3"
  - label: "Townsend and Teitler 2013, MNRAS 435, 3406 (GYRE)"
    url: "https://doi.org/10.1093/mnras/stt1533"
  - label: "Casagrande and VandenBerg 2014, MNRAS 444, 392 (bolometric corrections)"
    url: "https://doi.org/10.1093/mnras/stu1476"
  - label: "Casagrande and VandenBerg 2018, MNRAS 475, 5023 (bolometric corrections, Gaia)"
    url: "https://doi.org/10.1093/mnras/sty149"
  - label: "Chen et al. 2019, A&A 632, A105 (YBC)"
    url: "https://doi.org/10.1051/0004-6361/201936612"
  - label: "Bovy et al. 2016, ApJ 818, 130 (MWDust)"
    url: "https://doi.org/10.3847/0004-637X/818/2/130"
  - label: "Green et al. 2019, ApJ 887, 93 (3D dust map)"
    url: "https://doi.org/10.3847/1538-4357/ab5362"
  - label: "Silva Aguirre et al. 2015, MNRAS 452, 2127 (33 Kepler planet hosts)"
    url: "https://doi.org/10.1093/mnras/stv1388"
  - label: "Sousa et al. 2021, A&A 656, A53 (SWEET-Cat 2.0)"
    url: "https://doi.org/10.1051/0004-6361/202141584"
---

## The question

A planet is only as well known as its star. *Ariel*, ESA's survey of the atmospheres of transiting planets, measures each planet against the light of its host, so the host's mass, radius and age must be pinned down first and in the same way for every star (Chapter 1). The dissertation asked how precisely the Bayesian code PARAM can recover the age and mass of Sun-like planet hosts in the *Ariel* input catalogue, and how much the answer improves when the star's own vibrations, its solar-like oscillations, join the usual spectroscopic and photometric constraints (Chapter 1, Sect. 6.2).

## The sample

Three sets of stars were run. First, 13 synthetic stars taken straight from the model grid, with made-up measurement errors, to test whether PARAM recovers what it already knows (Sect. 5.3). Second, 33 *Kepler* planet hosts from Silva Aguirre et al. (2015), with the large frequency separation <span class="tex" data-tex="\Delta\nu">Δν</span>, the frequency of maximum power <span class="tex" data-tex="\nu_{\max}">ν<sub>max</sub></span>, the temperature and the metal content from Huber et al. (2013), chosen because four other codes had already characterised them (Sect. 6.1). Third, ten F-G-K seismic planet hosts from the *Ariel* input catalogue, five of them also in Magrini et al. (2022); their identities were withheld at the consortium's request, so the dissertation calls them Ariel-1 to Ariel-10 (Sect. 6.2).

## The method

The chain is drawn above. On the model side, a grid of stellar tracks was computed with MESA following the grid D1 physics of Moedas et al. (2022), from 0.5 to 1.8 <span class="tex" data-tex="M_\odot">M<sub>☉</sub></span> in steps of 0.1 and from [M/H] of <span class="tex" data-tex="-0.7">−0.7</span> to <span class="tex" data-tex="+0.5">+0.5</span> in steps of 0.1, from the zero-age main sequence to the red-giant branch (Sect. 2.6). GYRE then gave each model its oscillation frequencies, from which <span class="tex" data-tex="\Delta\nu">Δν</span> follows by a weighted regression of the radial modes and <span class="tex" data-tex="\nu_{\max}">ν<sub>max</sub></span> from the scaling relation (Sects. 3.3, 5.1 and 5.2).

On the observed side, each star's distance came from its *Gaia* parallax, its reddening from MWDust with the Green et al. (2019) three-dimensional map, and its luminosity from the 2MASS K band through a BCCode bolometric correction, the band least affected by dust; YBC is introduced as the alternative, and 2,000 Monte Carlo draws show how the input errors reach the luminosity (Chapter 4). Temperature, metal content and surface gravity came from SWEET-Cat 2.0 (Sect. 6.2).

PARAM compares these inputs, with their one-sigma uncertainties, against the grid and returns marginal probability distributions of mass, radius and age, read off as a mode, a median and a 68th-percentile interval; a second peak means a double solution (Chapter 5). Every star was run sixteen times: spectroscopy with or without <span class="tex" data-tex="\log g">log g</span>, with or without the luminosity, and with none, one or both of the seismic parameters (Sect. 6.2).

## Testing the tool

PARAM passes its own test. On the synthetic stars, the recovered masses, radii and ages fall within their quoted uncertainties, with second-quartile relative accuracies of about 1 per cent in mass and 8 per cent in age for the cluster set (Table 5.1). Ages are hardest for stars below about 0.8 <span class="tex" data-tex="M_\odot">M<sub>☉</sub></span> and for young stars, and stars above about 1.2 <span class="tex" data-tex="M_\odot">M<sub>☉</sub></span> can return two solutions because of the hook in their tracks (Sects. 5.3 and 7).

Against other codes it is less precise. On the 33 *Kepler* hosts, PARAM, which uses only the two global seismic parameters, reached median relative uncertainties of 4.9 per cent in mass and 26.0 per cent in age, while BASTA, ASTFIT, YMCM and AMP, which fit individual oscillation frequencies, reached 2.7 to 3.4 per cent and 9.6 to 14.6 per cent (Table 6.4). Its masses agree with BASTA, ASTFIT and AMP to within about 1 per cent, with a 2.2 per cent offset against YMCM, and its ages run 4 to 12 per cent younger than two of the codes (Table 6.3). The dissertation concludes that PARAM is reliable for F-G-K stars but should keep being tested for systematics (Chapter 7).

## The results

<figure class="figure paper-fig">
  <div class="paper-fig-svg" data-build>{% include figures/thesis-results.svg %}</div>
  <figcaption>What each extra constraint buys. Median relative uncertainty of age (left) and mass (right) for the ten <i>Ariel</i> input catalogue stars under eight sets of constraints: circles with the input uncertainties as published (Table 6.8), squares after inflating the temperature and metallicity uncertainties to 75 K and 0.1 dex, typical of the literature (Table 6.18). Data from the dissertation's own tables.</figcaption>
</figure>

With the inputs as published, seismology and luminosity are each enough. Starting from spectroscopy alone, median uncertainties of 28.8 per cent in age and 5.3 per cent in mass, adding <span class="tex" data-tex="\Delta\nu">Δν</span> and <span class="tex" data-tex="\nu_{\max}">ν<sub>max</sub></span> brings them to 7.7 and 1.5 per cent, and adding the luminosity instead brings them to 9.2 and 1.2 per cent; adding both changes little more (Table 6.8, Chapter 7).

That result rests on unusually small input errors, 0.6 per cent in temperature and 0.02 dex in metal content, and the dissertation says so. When those errors are inflated to literature-typical values, spectroscopy alone gives 34.1 per cent in age and 5.9 per cent in mass, the luminosity 22.0 and 3.9, the two seismic parameters 19.0 and 4.1, and all of them together 14.1 and 3.3 (Table 6.18, Sect. 6.3). In this regime the seismic parameters constrain the age better than the luminosity, and the two together do better than either, which the conclusions flag as a contradiction of the first set of findings (Chapter 7). Adding constraints does not always help: for one star they bring out a second solution near 1.3 <span class="tex" data-tex="M_\odot">M<sub>☉</sub></span>, where the hook makes the tracks cross (Sects. 6.2 and 7).

## What it led to

The dissertation grew out of an FCT MSc research grant on the BreakStarS project at IA, during which I implemented the small-frequency-separation routine, <span class="tex" data-tex="\delta\nu_{02}">δν<sub>02</sub></span>, in PARAM. It put me in the age, mass and radius sub-group of the *Ariel* Stellar Characterisation working group, where I contributed to Magrini et al. (2022), and it was presented as a poster at ENAA XXXII and a talk at FÍSICA 2022. In 2023 the Faculty of Sciences named me its best master's student in astronomy and astrophysics.
<!-- ledger: fund-2021-fct-msc-research-grant, pos-2021-msc-research-fellow, mem-2021-ariel-science-consortium, pub-2022-magrini-ariel, pres-2022-09-enaa32-poster-ariel, pres-2022-09-fisica2022-oral-ariel, award-2023-best-msc-student-astronomy -->
