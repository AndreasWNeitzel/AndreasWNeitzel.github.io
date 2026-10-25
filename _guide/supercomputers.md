---
title: "What is a supercomputer?"
short: "Research supercomputers"
lede: "A supercomputer links thousands of processors with a fast network, so that one scientific job can use far more computing power than any single machine."
order: 8
image: /assets/img/guide/supercomputers.webp
image_alt: "Rows of black computer cabinets in a white machine hall, with bundles of teal cables running along their tops and down their fronts."
image_credit: "Steve Jurvetson / Wikimedia Commons"
image_licence: "CC BY 4.0"
image_source: "https://commons.wikimedia.org/wiki/File:BSC_MareNostrum_5_(54686085845).jpg"
related:
  - fund-2025-hpcvlab-deucalion-team-member
  - fund-2026-10-cpca-a1-deucalion
  - fund-2026-10-cpca-a2-marenostrum
  - skill-2026-hpc
sources:
  - {label: "EuroHPC Joint Undertaking, Discover EuroHPC JU", url: "https://eurohpc-ju.europa.eu/about/discover-eurohpc-ju_en"}
  - {label: "EuroHPC Joint Undertaking, Our supercomputers", url: "https://eurohpc-ju.europa.eu/supercomputers/our-supercomputers_en"}
  - {label: "EuroHPC Joint Undertaking, Deucalion inaugurated (6 September 2023)", url: "https://eurohpc-ju.europa.eu/deucalion-new-eurohpc-supercomputer-has-been-inaugurated-2023-09-06_en"}
  - {label: "EuroHPC Joint Undertaking, Inauguration of MareNostrum 5 (21 December 2023)", url: "https://eurohpc-ju.europa.eu/marenostrum-5s-inauguration-2023-12-19_en"}
---

A supercomputer is many computers, called nodes, joined by a fast network so that they can work on one problem together. Its speed is measured in petaflops, millions of billions of calculations per second. Researchers apply for time in core-hours, one processor core for one hour, and in GPU-hours on graphics processors, which are used to train neural networks. Many of Europe's large machines are bought jointly by the EU and national governments through the EuroHPC Joint Undertaking.

The EuroHPC Joint Undertaking was created in 2018 and is based in Luxembourg. Deucalion, at the University of Minho in Guimarães, was inaugurated on 6 September 2023. It has 1,632 ARM (A64FX) nodes, 500 x86 (AMD EPYC) nodes and 33 GPU nodes with four NVIDIA A100 each, for a peak of 9.76 petaflops. MareNostrum 5, at the Barcelona Supercomputing Center, was inaugurated on 21 December 2023 and peaks at 314 petaflops. Its accelerated partition uses NVIDIA Hopper GPUs, and a Spanish-led consortium that includes Portugal runs it.

## Where I come in

As a member of the University of Porto's HPCvLAB project, I had development access to Deucalion from December 2025 to September 2026 and used 94,001 core-hours in about 250 jobs on its ARM, x86 and A100 partitions, for JANUS, the *HAYDN* proposal tests and the HAYDNsim noise runs. With Tiago L. Campante as co-responsible investigator, I am the responsible investigator on two approved FCT computing allocations, each for 12 months. One gives 99,840 core-hours and 1,500 A100 GPU-hours on Deucalion; the other gives 1,002,400 core-hours and 1,000 H100 GPU-hours on MareNostrum 5.
