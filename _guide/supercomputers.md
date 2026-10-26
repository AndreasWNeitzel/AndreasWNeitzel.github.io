---
title: "What is a supercomputer?"
short: "Research supercomputers"
lede: "A supercomputer links thousands of processors with a fast network, so that one scientific job can use far more computing power than any single machine."
order: 8
hero: false
extra_css: [/assets/css/hpc.css]
wide_figure: figures/hpc.svg
wide_caption: "The two national machines I compute on, drawn to scale, and how one JANUS run moves through them. Left, each square is 32 nodes and the filled squares are the partitions my allocations use; the bars compare peak performance. Right, the spectra wait on the parallel file system, a Slurm job array prepares them on CPU nodes, the GPU nodes run the network, and the catalogue is written back; the bars compare the computing time I have used and been granted. By arithmetic, 299,520 core-hours is one 48-core Deucalion node for 260 days, and 1,002,400 core-hours is one 112-core MareNostrum 5 node for 373 days. Node counts, peaks and storage from EuroHPC JU and BSC, node hardware from the hosting sites, allocations from the FCT decisions."
wide_figures:
  - include: figures/hpc-halls.svg
    caption: "The two machines as halls of cabinets at one scale, one cabinet for 32 nodes: Deucalion with 51 cabinets of ARM nodes, 16 of x86 and one of A100 GPUs; MareNostrum 5 with 200 of general-purpose nodes and 35 with H100 GPUs. Cabinets of the partitions my two allocations use are in the stronger tone, the GPU cabinets lit. Node counts from EuroHPC JU and the hosting sites; the halls' real layouts differ."
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
  - {label: "Deucalion, about the system (hosting site)", url: "https://deucalion.acnca.pt/about/"}
  - {label: "Barcelona Supercomputing Center, MareNostrum 5 overview", url: "https://www.bsc.es/supportkc/docs/MareNostrum5/overview/"}
---

A supercomputer is many computers, called nodes, joined by a fast network so that they can work on one problem together. Its speed is measured in petaflops, millions of billions of calculations per second. Researchers apply for time in core-hours, one processor core for one hour, and in GPU-hours on graphics processors, which are used to train neural networks. Many of Europe's large machines are bought jointly by the EU and national governments through the EuroHPC Joint Undertaking.

The EuroHPC Joint Undertaking was created in 2018 and is based in Luxembourg. Deucalion, at the University of Minho in Guimarães, was inaugurated on 6 September 2023. It has 1,632 ARM (A64FX) nodes, 500 x86 (AMD EPYC) nodes and 33 GPU nodes with four NVIDIA A100 each, for a peak of 9.76 petaflops. MareNostrum 5, at the Barcelona Supercomputing Center, was inaugurated on 21 December 2023 and peaks at 314 petaflops. Its accelerated partition uses NVIDIA Hopper GPUs, and a Spanish-led consortium that includes Portugal runs it.

## Where I come in

As a member of the University of Porto's HPCvLAB project, I had development access to Deucalion from December 2025 to September 2026 and used 94,001 core-hours in about 250 jobs on its ARM, x86 and A100 partitions, for JANUS, the *HAYDN* proposal tests and the HAYDNsim noise runs. With Tiago L. Campante as co-responsible investigator, I am the responsible investigator on two approved FCT computing allocations, each for 12 months. One gives 299,520 core-hours (99,840 granted, tripled as a bonus) and 1,500 A100 GPU-hours on Deucalion; the other gives 1,002,400 core-hours and 1,000 H100 GPU-hours on MareNostrum 5. The figure above shows what each run is granted and where on the two machines it runs.
