# NEITZEL_BIO.md — Comprehensive Biographical Reference

> **Purpose:** this document provides deep background context about who Andreas is, what his work is about, and what credentials matter. It is **reference material**, not site content. Do not copy from this document into the site verbatim — use `content/about.md`, `content/publications.bib`, and `content/cv.md` for that.
>
> Use this document to:
>
> - Verify claims before writing them into the site
> - Resolve ambiguities about Andreas's positioning
> - Understand why certain framings in `content/` are phrased the way they are

---

## 1. Identity

- **Full name:** Andreas W. Neitzel
- **Citizenship:** Luso-German (dual)
- **Location:** Porto, Portugal
- **Primary email:** andreaswneitzel@gmail.com
- **ORCID:** 0000-0001-6283-907X
- **LinkedIn:** andreaswneitzel
- **GitHub:** AndreasWNeitzel

## 2. Academic position and trajectory

**Current:** Fourth-year PhD candidate in Astronomy (expected defense: end of 2027).

**Institution:**

- Instituto de Astrofísica e Ciências do Espaço (IA/CAUP) — host institute
- Faculdade de Ciências da Universidade do Porto (FCUP) — degree-granting faculty
- University of Porto, Portugal

**Advisors:**

- **Tiago L. Campante** (primary, IA/CAUP Porto) — asteroseismology expert, PI of ArqueoGal
- **Diego Bossini** (co-advisor, IA/CAUP Porto) — Gaia DPAC affiliate, stellar populations expert
- **Andrea Miglio** (co-advisor, INAF-OAS Bologna) — Andreas completed a six-month secondment at his group in Bologna

**Funding:** Competitive FCT Doctoral Fellowship 2025.01843.BD (Sep 2025 – Sep 2026). **Not renewable.**

**Thesis title:** "Machine Learning Applied to Galactic Archaeology"

## 3. Career history

| Period    | Position                                     | Institution                                                      |
| --------- | -------------------------------------------- | ---------------------------------------------------------------- |
| 2017–2020 | BSc in Physics                               | University of Porto (FCUP)                                       |
| 2020–2022 | MSc in Astronomy & Astrophysics              | University of Porto (FCUP) — 16/20                               |
| 2021–2022 | FCT MSc Research Grant (CIAAUP-08/2021-BI-M) | IA/CAUP, BreakStarS project                                      |
| 2022–2027 | PhD Researcher                               | IA/CAUP, Stellar Astrophysics Group                              |
| 2025–2026 | Visiting PhD Student / Associate             | INAF Osservatorio di Astrofisica e Scienza dello Spazio, Bologna |
| 2025–2026 | FCT Doctoral Fellow                          | IA/CAUP                                                          |

**Honors:** Best Master's Student in Astronomy & Astrophysics, FCUP (2023)

## 4. Research positioning

### One-sentence version

Andreas develops machine-learning methods for Galactic archaeology — the study of the Milky Way's assembly history through its stellar populations.

### Three-minute version

Andreas works at the intersection of machine learning and stellar astrophysics. His PhD focuses on applying dimensionality-reduction and clustering algorithms to large-scale stellar datasets (primarily from the ESA _Gaia_ mission) to disentangle distinct Galactic populations — the thin disk, thick disk, halo, and accreted stellar populations from past merger events — in chemical, kinematic, and age space.

His first-author 2025 paper in _A&A_ introduced a manifold-learning framework (UMAP + HDBSCAN) validated on Gaia DR3-like synthetic samples from FIRE-2 cosmological simulations. The work demonstrated that ML methods can recover population membership for stars shaped by complex processes like radial migration and past accretion — a validation that standard chemo-dynamic cuts often miss.

This paper is now the cited prototype for the ML tool being built under ArqueoGal (FCT Exploratory Project 2024.15303.PEX, 2026–2027), where Andreas serves as Co-Investigator with substantial person-month allocations on two scientific tasks.

### In-flight research threads (papers in preparation)

1. **Chemical abundance prediction from _Gaia_ XP spectra** using contrastive self-supervised learning (TriGroupEncoder architecture, PyTorch). This addresses a key bottleneck in stellar population studies: predicting [M/H] and [α/M] for the ~220 million stars with XP coefficients but no spectroscopic follow-up.

2. **Noise modeling for the proposed _HAYDN_ mission.** During a six-month secondment at INAF-OAS Bologna with Andrea Miglio, Andreas built simulation pipelines for HAYDN's Noise Estimator, using TRILEGAL synthetic stellar populations with King-profile spatial sampling across globular and open clusters (47 Tuc, M67, Omega Cen, h+χ Per). This work ran on Deucalion, Portugal's EuroHPC petascale supercomputer (TOP500 #219), with additional use of UniBo's Matrix and BladeRunner data-analysis clusters.

### Additional research contributions

- **ESPRESSO / ε Indi A** — co-author on the first asteroseismic detection of solar-like oscillations in a K5 dwarf (_A&A_ 2024 letter, L16). Served as on-site observer at ESO's VLT, Paranal (May 2024).
- **Ariel Input Catalog** — MSc thesis delivered age and mass estimates for seismic stars in the Ariel target list; co-author on the consortium paper Magrini et al. 2022.
- **Seismic + spectroscopic characterisation pipelines** — built cross-matching infrastructure for Gaia DR3, GSP-Spec, TESS, Kepler/K2, and 2MASS with PARAM Bayesian ages, MWDUST extinction, and bolometric corrections.

## 5. Consortium affiliations

- **ESA _Ariel_ Science Consortium** — member of the Stellar Characterisation working group, Age/Mass/Radius sub-WG. Active primarily during MSc; current involvement is reduced but membership and co-authored consortium papers remain.
- **TESS Asteroseismic Science Operations Centre (TASOC)** — affiliate
- **Kepler Asteroseismic Science Consortium (KASOC)** — Red-Giant Oscillations working group

Andreas is NOT in: Euclid consortium, CHEOPS consortium, PLATO consortium directly (though his advisors are connected to PLATO). Do not claim these memberships.

## 6. Funded projects

### Current: ArqueoGal (2024.15303.PEX, 2026–2027)

- **Full title:** Galactic Archaeology with Machine Learning
- **PI:** Tiago L. Campante
- **Budget:** €59,935.98
- **Duration:** 18 months, starting Feb 2026
- **Success rate of the call:** 16% (400 funded out of 2,545 applications)
- **Andreas's role:** **Co-Investigator.** Named participant with allocations on:
  - Task 3 (1 PM, lead: Bossini)
  - Task 5: Stellar Population Classification (4.4 PM, leads: Campante, Miglio)
  - Task 6: Galactic Modeling (6 PM, leads: Campante, Miglio)

**Important:** Andreas is NOT a task lead. The ArqueoGal proposal clearly designates Campante, Miglio, and Bossini as leads. Calling Andreas "team lead" on any task is factually incorrect and must not appear anywhere on the site.

### Related: FCT HPCvLAB project 2025.00007 — Deucalion access

- **Role:** Team member (not PI)
- **Resource:** 500k core-hours on ARM A64FX, 100k on x86, via Deucalion EuroHPC petascale supercomputer

## 7. Publications (peer-reviewed, in order of prominence)

See `content/publications.bib` for canonical BibTeX.

1. **Neitzel, A. W.** et al. 2025, _A&A_ 695, A243 — first author
2. Campante, T. L., ..., **Neitzel, A. W.** et al. 2024, _A&A_ 683, L16 — co-author
3. Magrini, L., ..., **Neitzel, A. W.** et al. 2022, _A&A_ 663, A161 — co-author

Two additional first-author papers are in preparation (see Research positioning section). These should be mentioned on the Publications page under a clear "In Preparation" subheading, but must NOT be promoted to "submitted" or "forthcoming."

## 8. Invited talks and conferences

### International

- 11th Iberian Meeting on Asteroseismology, Lluc, Spain (Nov 2024) — oral
- 8th TESS / 15th Kepler Asteroseismic Science Consortium Workshop, Porto (Jul 2024) — oral

### National (Portugal)

- ENAA (Portuguese National Astronomy Meetings): XXXIII Coimbra 2023, XXXIV Guimarães 2024, XXXV Lisbon 2025 — oral
- ENAA XXXII Lisbon 2022, FÍSICA 2022 Porto — posters

### Training

- Porto Summer School on Asteroseismology, "From Pixels to Stellar Ages" (Jul 2024)
- The Milky Way Assembly Tale conference (May 2024)

**Note:** Andreas has NOT given any invited international talk at a non-Iberian meeting. Do not claim this.

## 9. Service, teaching, outreach

- **IA Summer Programme (2024, 2025):** supervised five BSc/MSc students on "Hands-on Galactic Archaeology and Machine Learning using Synthetic Data"
- **Escola de Verão de Física (EVF), FCUP:** recurring tutor 2023–2025; physics-demonstrations monitor for visiting school groups
- **Local Organising Committee, 8th TESS / 15th Kepler Workshop (Porto, Jul 2024)**
- **Chair, IA Stars Day 2023; LOC member, IA Stars Day 2022**

## 10. Technical skills (honest inventory)

### Strong

- Python (expert level, daily use)
- Machine learning: scikit-learn, PyTorch, manifold learning (UMAP, t-SNE, PCA), clustering (HDBSCAN, GMM), deep learning, contrastive self-supervised learning, Bayesian inference, MCMC
- Astronomy software: astropy, galpy, TOPCAT, ADQL; PARAM (Bayesian stellar characterisation), MESA (stellar evolution), MWDUST, BCCode/YBC (bolometric corrections), TRILEGAL (synthetic populations)
- Survey data: _Gaia_ DR3 (astrometry, radial velocities, XP spectra, GSP-Spec), APOGEE, LAMOST, GALAH, 2MASS, _TESS_, _Kepler_/K2, ESPRESSO
- HPC: Linux, WSL2, Bash, SLURM/SSH; Deucalion EuroHPC (ARM A64FX and x86); UniBo Matrix/BladeRunner; CUDA/NVIDIA GPUs

### Working knowledge

- R, SQL, LaTeX, Git
- Other ML: TensorFlow/Keras, gradient boosting (XGBoost)

### Languages

- Portuguese (native), English (C2), German (A2), French (A2)

## 11. Things Andreas is NOT

These are common pitfalls where an evaluator might misread. Do not claim any of the following:

- NOT a PI on any observing proposal, grant, or software release
- NOT a team lead on ArqueoGal (he is a named participant; leads are Campante, Miglio, Bossini)
- NOT a Gaia DPAC member (his co-advisor Bossini is; Andreas is not formally)
- NOT working on Euclid, CHEOPS, PLATO data directly (synergies exist but are forward-looking)
- NOT in an AI lab, a startup, or quantitative finance in any academic-facing context — those are separate tracks and should never appear on the academic site
- NOT a postdoc yet — PhD completion expected end of 2027

## 12. Positioning calibration

When in doubt about how to phrase something, use these calibrations:

- "Research area" = Galactic archaeology + machine learning (together, not separately)
- "Career stage" = fourth-year PhD candidate, not postdoc, not early-career researcher
- "ESA relevance" = member of _Ariel_ consortium since MSc, natural synergies with _Gaia_, _PLATO_, _Ariel_ (the three, not five)
- "Independence signal" = Co-I on ArqueoGal with paper as cited prototype
- "Methodological signal" = first-author A&A manifold learning paper + in-flight contrastive SSL work
- "International signal" = INAF Bologna secondment with Miglio
- "Observing signal" = on-site ESPRESSO observer at VLT (not PI, not multiple campaigns)

If you find yourself about to write a sentence that exceeds one of these calibrations, stop. Re-ground in the honest version.
