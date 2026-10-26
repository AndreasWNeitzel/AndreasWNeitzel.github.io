---
title: "Dissecting stellar populations with manifold learning"
headline: "In a simulated Milky Way, a method that needs no labels told disc from halo stars and, in error-free data, found the debris of two swallowed galaxies."
citation: "Neitzel, A. W., Campante, T. L., Bossini, D., & Miglio, A. 2025, Dissecting stellar populations with manifold learning. I. Validation of the method on a synthetic Milky Way-like galaxy, A&A, 695, A243"
doi: "10.1051/0004-6361/202451718"
arxiv: "2501.16294"
year: 2025
role: "first author"
contribution: "First and corresponding author."
figure: "/assets/img/papers/neitzel-2025-manifold-learning.webp"
figure_alt: "Twelve scatter plots in four columns, one per test sample (A to D), and three rows: velocity, alpha-element abundance against iron abundance, and iron abundance against age. Stars are coloured by the group the method assigned; columns A and B show five groups, columns C and D three."
figure_caption: "Each colour is one group the method found without labels, shown by motion (top), chemistry (middle) and age (bottom) for the four test samples. The error-free samples A and B give five groups; with measurement errors (C and D) the disc stays one group, in green. From Neitzel et al. 2025, A&A 695, A243, Fig. 11, CC BY 4.0."
card_image: "/assets/img/cards/milky-way.webp"
card_credit: "ESO/S. Brunier, CC BY 4.0"
card_credit_url: "https://www.eso.org/public/images/eso0932a/"
order: 1
wide_figure: figures/neitzel-2025-workflow.svg
wide_caption: >-
  How the paper turned a simulated galaxy into a test of the method: a synthetic <i>Gaia</i> survey of the FIRE-2 galaxy m12f, four samples, five features, an embedding, a clustering, two runs, and a check against the galaxy's own record of each star. Sample A has 75,000 random stars within 3 kpc and sample B 76,168 TESS-like seismic red giants; C and D are B with realistic and optimistic errors (ages 20 and 10 per cent; [Fe/H] and [α/Fe] at the APOGEE DR17 median and 25th-percentile uncertainties) (Sect. 2.2). The five features are V, the combined U and W velocity, [Fe/H], [α/Fe] and age, each standardised (Sect. 2.1). UMAP maps them to two dimensions (n_neighbors 15, min_dist 0, 10,000 epochs), and an embedding passes only if its trustworthiness exceeds 0.90; the four samples score 0.988, 0.994, 0.969 and 0.978 (Sects. 3.1, 3.2, Table 2). HDBSCAN is tuned by Optuna on cluster persistence against a baseline from 1,000 random inputs (Sect. 3.3). The first run gives two components, MC1 and MC2; the second run repeats UMAP 100 times on each (Sect. 4.2). Against the velocity and metallicity criterion the informedness is 0.989, 0.966, 0.966 and 0.973 (Sect. 3.4, Table 2); 97.6 to 98.7 per cent of the accreted stars, those with a formation distance <span class="tex" data-tex="d_\mathrm{form} > 30\ \mathrm{kpc}">d<sub>form</sub> &gt; 30 kpc</span>, fall in MC2, which is 10.9 to 16.6 per cent accreted (Sects. 2.1, 4.1). In the error-free samples the second run separates a low-α and a high-α disc, the in situ halo and the two mergers (6.5 and 1.4 Gyr ago); with errors the disc stays one and the halo splits in two (Sect. 4.3, Table 3; Neitzel et al. 2025, A&amp;A 695, A243).
extra_css: [/assets/css/papers.css]
math: true
sources:
  - label: "Article in A&A (open access)"
    url: "https://doi.org/10.1051/0004-6361/202451718"
  - label: "Preprint, arXiv:2501.16294"
    url: "https://arxiv.org/abs/2501.16294"
  - label: "Online appendix (Zenodo)"
    url: "https://doi.org/10.5281/zenodo.14749285"
  - label: "Starfold, the Python package that extends the method"
    url: "https://github.com/AndreasWNeitzel/starfold"
---

## The question

The Milky Way grew from stars it formed itself and from smaller galaxies it swallowed. Stars from each episode differ in age, chemistry and motion, but the groups overlap and are hard to separate (Sect. 1). The paper tests whether manifold learning, an unsupervised machine-learning approach that assumes little about how many groups exist or what they look like, can find them.

## What we did

The test bed was a simulated galaxy with a known history: m12f, from the FIRE-2 simulations, which went through two major mergers, 6.5 and 1.4 billion years ago (Sect. 2.1). A mock *Gaia* survey of it gave four samples (Sect. 2.2): 75,000 stars at all stages of evolution (A), and 76,168 red giants like those in the *TESS* catalogue of oscillating giants, with no errors (B), realistic errors (C) or optimistic errors (D).

UMAP turned five numbers per star (age, two chemical abundances, two measures of velocity) into a position on a two-dimensional map, and HDBSCAN found the groups on that map (Sect. 3).

## What came out

The method separated disc from halo in every sample. The first pass scored an informedness of 0.966 to 0.989, where 1 is a perfect match, and put 97.6 to 98.7 per cent of the stars born in other galaxies into the halo group, although no input said where a star was born (Sect. 4.1, Table 2).

A second pass on each group found more structure. Samples A and B gave five groups: two discs with slightly different chemistry, the halo that formed in place, and one group per merger (Table 3, Fig. 11). With measurement errors added (C and D), the discs could no longer be told apart, and the halo split into two groups instead of three (Sect. 4.3).

## My part

I am the first and corresponding author; the co-authors are my PhD supervisors. The paper reports the first project of my PhD: I built the pipeline, compared UMAP with PCA and t-SNE (Appendix D, on Zenodo) and ran the tests. Starfold, a Python package I develop, extends the method.
