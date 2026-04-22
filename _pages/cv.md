---
layout: page
permalink: /cv/
title: CV
nav: true
nav_order: 5
---

A complete curriculum vitae is available as a PDF.

[**Download CV (PDF)**](/assets/pdf/CV_Neitzel_Academic_Public.pdf)

The CV is updated periodically. For the most recent version or for specific inquiries, please contact me directly.

---

## Research summary

Fourth-year PhD candidate at IA/CAUP (Porto) developing machine-learning methods for Galactic archaeology. My first-author _A&A_ paper (2025) applied manifold learning (UMAP, HDBSCAN) to disentangle thin/thick-disk, halo, and accreted populations in chrono-chemo-kinematic space, and is the cited prototype for the ML tool to be released by FCT Exploratory Project ArqueoGal (2024.15303.PEX), on which I am Co-Investigator with substantial allocations on two scientific tasks. Member of the ESA _Ariel_ Science Consortium (Stellar Characterisation WG) and _TESS_/_Kepler_ (TASOC/KASOC). Natural synergies with _Gaia_, _PLATO_, and _Ariel_, and ESA data-science initiatives.

Luso-German citizen (EU).

## Education

**PhD in Astronomy**, University of Porto (FCUP) & IA/CAUP · 2022–2027 (expected)
Thesis: "Machine Learning Applied to Galactic Archaeology". Advisors: Tiago L. Campante, Diego Bossini, Andrea Miglio (INAF-OAS Bologna). FCT Doctoral Fellowship 2025.01843.BD (Sep 2025 – Sep 2026).

**MSc in Astronomy & Astrophysics**, University of Porto (FCUP) · 2020–2022 · 16/20
Thesis: "Determination of Age and Mass for Seismic Stars in the Ariel Input Catalog". Best Master's Student in Astronomy & Astrophysics, FCUP (2023).

**BSc in Physics**, University of Porto (FCUP) · 2017–2020

## Research positions

**Visiting PhD Student / Associate**, INAF Osservatorio di Astrofisica e Scienza dello Spazio, Bologna · 2025–2026

- Six-month secondment at co-supervisor A. Miglio's group to develop simulation pipelines for the proposed _HAYDN_ mission; built Python dashboards for noise estimation and synthetic stellar catalogue generation (TRILEGAL, King-profile spatial sampling) across globular and open clusters (47 Tuc, M67, Omega Cen, h+χ Per).
- Team member on FCT HPCvLAB project 2025.00007 on Deucalion (Portugal's EuroHPC petascale supercomputer, TOP500 #219); ran _HAYDN_ Noise Estimator workloads on the ARM A64FX (500k core-hours allocated) and x86 (100k core-hours) partitions. Additional use of the Matrix HPC and BladeRunner data-analysis clusters (UniBo / INAF-OAS Bologna Open Physics Hub, SLURM-scheduled).

**PhD Researcher**, IA/CAUP, Stellar Astrophysics Group, Porto · 2022–present

- **Lead developer** of the ML pipelines for FCT Exploratory Project ArqueoGal (2024.15303.PEX, 2026–2027), PI: T. L. Campante. €60k, 16% success-rate call; Co-Investigator with substantial allocations on Task 5 (Stellar Population Classification, 4.4 PM) and Task 6 (Galactic Modeling, 6 PM). Architected and built two production pipelines: **xp_abundances** (semi-supervised multi-task regression with contrastive pretraining; predicts six stellar parameters from _Gaia_ DR3 XP coefficients calibrated against APOGEE DR19, with block-Cholesky covariant uncertainties and OOD/release-tier quality flags) and **Starfold** (the open-source ML classifier shipping as deliverable D5.1 in Dec 2026, extending the Neitzel+2025 _A&A_ manifold-learning methodology to real _Gaia_ DR3 stars — the first application of the method to observed data).
- First-author _A&A_ (2025) applying manifold learning (UMAP + HDBSCAN) to _Gaia_ DR3-like synthetic samples from FIRE-2 cosmological simulations; validated the ability to disentangle thin/thick disk, halo, and accreted stellar populations, including populations shaped by radial migration and past accretion events, in the chrono-chemo-kinematic parameter space.
- Built production ML infrastructure for chemical-abundance prediction from _Gaia_ XP spectra: multi-task regression targeting [M/H], [α/M], [Fe/H], [Mg/H], T_eff, and log g; PyTorch on CUDA (WSL2, RAPIDS 25.10); calibrated uncertainties via block-Cholesky decomposition; paper in preparation.
- Built seismic and spectroscopic characterisation pipelines cross-matching _Gaia_ DR3, GSP-Spec, _TESS_, _Kepler_/K2, and 2MASS; integrated PARAM Bayesian ages, MWDUST extinction, and bolometric corrections for Galactic archaeology targets.
- Co-author on the first asteroseismic detection of solar-like oscillations in a K5 dwarf (ε Indi A; _A&A_ 2024 letter, L16); on-site observer with ESPRESSO at ESO's VLT, Paranal (May 2024).
- Member of the ESA _Ariel_ Science Consortium (Stellar Characterisation WG, Age/Mass/Radius sub-WG) since MSc; co-author on the working group's homogeneous stellar-parameter paper (Magrini et al. 2022). Also affiliated with _TESS_ Asteroseismic Science Operations Centre (TASOC) and _Kepler_ (KASOC), Red-Giant Oscillations WG.
- Supervised 5 BSc/MSc students at IA Summer Programmes (2024, 2025) on "Hands-on Galactic Archaeology and Machine Learning using Synthetic Data".

**MSc Research Fellow (FCT)**, IA/CAUP, grant CIAAUP-08/2021-BI-M · 2021–2022

- Implemented a routine in the Bayesian stellar characterisation code PARAM to compute the small frequency separation from acoustic stellar oscillation modes, improving constraints on red-giant modelling.

## Publications

- **Neitzel, A. W.**, Campante, T. L., Bossini, D., Miglio, A. (2025). "Dissecting stellar populations with manifold learning I. Validation of the method on a synthetic Milky Way-like galaxy." _A&A_ 695, A243. [doi:10.1051/0004-6361/202451718](https://doi.org/10.1051/0004-6361/202451718)
- Campante, T. L., Kjeldsen, H., Li, Y., Lund, M. N., et al. including **Neitzel, A. W.** (2024). "Expanding the frontiers of cool-dwarf asteroseismology with ESPRESSO." _A&A_ 683, L16. [doi:10.1051/0004-6361/202449197](https://doi.org/10.1051/0004-6361/202449197)
- Magrini, L., Danielski, C., Bossini, D., et al. including **Neitzel, A. W.** (2022). "Ariel stellar characterisation I. Homogeneous stellar parameters of 187 FGK planet host stars." _A&A_ 663, A161. [doi:10.1051/0004-6361/202243405](https://doi.org/10.1051/0004-6361/202243405)

## Grants & awards

- **Co-Investigator, FCT Exploratory Research Project ArqueoGal** (2024.15303.PEX), PI: T. L. Campante. €60k over 18 months; awarded in a 16% success-rate call (400 / 2,545). Named participant on Stellar Population Classification (4.4 PM) and Galactic Modeling (6 PM). 2026–2027.
- **FCT Doctoral Fellowship** (2025.01843.BD), Fundação para a Ciência e a Tecnologia. 2025–2026.
- **Best Master's Student in Astronomy & Astrophysics**, FCUP, University of Porto. 2023.
- **FCT MSc Research Grant** (CIAAUP-08/2021-BI-M), BreakStarS project. 2021–2022.

## Software & open-source

- **[ArqueoGal](https://github.com/AndreasWNeitzel/ArqueoGal)** — _Gaia_ XP → APOGEE DR19 stellar-abundance prediction pipeline (Python 3.12, PyTorch 2.10, RAPIDS 25.10 on CUDA). Lead developer; OSI-licensed release scheduled for deliverable D5.1 (Dec 2026).
- **[Starfold](https://github.com/AndreasWNeitzel/Starfold)** — ML stellar-population classifier building on the Neitzel+2025 _A&A_ manifold-learning methodology, augmented and extended for first application to real _Gaia_ DR3 observations (the original paper validated the method on synthetic data only); downstream consumer of ArqueoGal abundance predictions; OSI-licensed release targeted for D5.1.
- **[Stellar Explorer](/stellar-explorer/)** — Interactive client-side web app for MIST v1.2 stellar evolution tracks with GYRE oscillation spectra; live HR diagram, real-time interior cross-section with pulsation/convection animations driven by GYRE eigenfunctions, interior profiles, PSD/échelle/Schwarzschild views.

## Selected talks & conferences

- Oral (international): "Intelligent Identification of Stellar Populations with Manifold Learning", 11th Iberian Meeting on Asteroseismology, Lluc, Spain (Nov 2024).
- Oral (international): "Identification of Stellar Populations through Latent Space Projection", 8th _TESS_ / 15th _Kepler_ Asteroseismic Science Consortium Workshop, Porto (Jul 2024).
- Oral (national): Portuguese National Astronomy Meetings (ENAA): XXXIII Coimbra 2023; XXXIV Guimarães 2024; XXXV Lisbon 2025. Poster: ENAA XXXII Lisbon 2022, and FÍSICA 2022 Porto on _Ariel_ stellar characterisation.
- Training: Porto Summer School on Asteroseismology "From Pixels to Stellar Ages" (Jul 2024); The Milky Way Assembly Tale conference (May 2024).

## Teaching, mentoring & service

- **Tutor / Outreach**: Escola de Verão de Física (EVF), FCUP. Recurring tutor (2023–2025); physics-demonstrations monitor for visiting school groups (Feb 2023 to present).
- **Organisation**: Local Organising Committee, 8th _TESS_ / 15th _Kepler_ Asteroseismic Workshop (Porto, Jul 2024); Chair, IA Stars Day (2023); LOC member, Stars Day (2022).

## Technical skills

- **Programming & ML**: Python (expert), R, SQL, Bash, LaTeX, Git. scikit-learn, PyTorch, TensorFlow/Keras; manifold learning (UMAP, t-SNE, PCA), clustering (HDBSCAN, k-means, GMM), deep learning, contrastive self-supervised learning, gradient boosting (XGBoost), Bayesian inference, MCMC.
- **Astronomy software & surveys**: astropy, galpy, TOPCAT, ADQL; PARAM, MESA, MWDUST, BCCode/YBC, TRILEGAL; IRAF, DS9. _Gaia_ DR3 (astrometry, radial velocities, XP spectra, GSP-Spec), APOGEE, LAMOST, GALAH, 2MASS, _TESS_, _Kepler_/K2 (via KASOC/TASOC), ESPRESSO.
- **Visualization, HPC & languages**: matplotlib, Plotly, seaborn; interactive web apps (Canvas2D, HTML5, Plotly.js); Manim animations. Linux, WSL2, SLURM/SSH; Deucalion EuroHPC (ARM, x86); UniBo Matrix / BladeRunner; CUDA / NVIDIA GPUs. Portuguese (native), English (C2), German (A2), French (A2).
