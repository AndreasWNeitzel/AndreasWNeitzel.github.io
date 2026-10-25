---
title: "What does machine learning do with stars?"
short: "Machine learning for stars"
lede: "Machine learning carries measurements from well-studied stars over to millions of others, and finds groups of stars that nobody labelled."
order: 10
image: /assets/img/guide/machine-learning-for-stars.webp
image_alt: "The Sun's light spread into its colours in fifty horizontal strips, running from red at the top to violet at the bottom, crossed by many thin dark lines."
image_credit: "N.A. Sharp/KPNO/NOIRLab/NSO/NSF/AURA"
image_licence: "CC BY 4.0"
image_source: "https://noirlab.edu/public/images/noao-sun/"
related:
  - pub-2025-neitzel-manifold-learning
  - sw-2026-starfold
  - pres-2026-07-tasc10-oral-janus
  - skill-2026-ml-probabilistic-deep-learning
  - teach-2025-06-ia-summer-programme
sources:
  - {label: "Leung and Bovy 2019, Monthly Notices of the Royal Astronomical Society (astroNN)", url: "https://doi.org/10.1093/mnras/sty3217"}
  - {label: "Hunt and Reffert 2023, Astronomy and Astrophysics 673, A114", url: "https://doi.org/10.1051/0004-6361/202346285"}
---

Large surveys now measure millions of stars, too many to analyse one at a time. In supervised learning, a model such as a neural network learns from stars whose properties are already known from careful measurements, then predicts those properties for the rest. Unsupervised methods such as clustering search a catalogue for groups of similar stars without being told what the groups are.

Leung and Bovy (2019) trained a neural network on APOGEE spectra that returns abundances of 18 elements to about 0.03 dex (about 7 per cent), with uncertainties that grow for stars unlike its training set; it analysed about 250,000 spectra in ten minutes on one GPU. Hunt and Reffert (2023) ran the clustering algorithm HDBSCAN on 729 million *Gaia* DR3 sources and recovered 7,167 star clusters, 2,387 of them new candidates; a neural network that classifies colour-magnitude diagrams helped them validate the clusters.

## Where I come in

My 2025 paper introduced a method based on UMAP and HDBSCAN for separating the Milky Way's stellar populations and tested it on a synthetic galaxy where the answer is known. Starfold, my open-source Python package, extends it by refitting each grouping on 32 random subsets to measure how often every group recurs; it matched or beat the library defaults on 8 of 10 benchmark tables, but on only 2 of 4 held-out tables. I am also developing JANUS, a neural network that predicts APOGEE-like parameters and abundances from *Gaia* XP spectra, with a reliability score for each star.
