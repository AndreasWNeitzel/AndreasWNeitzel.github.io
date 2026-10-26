---
layout: page
permalink: /research/arqueogal/
title: ArqueoGal
nav_section: Research
crumb: {label: Research, url: /research/}
description: ArqueoGal, the FCT exploratory project on the Milky Way's history, and the machine-learning pipelines Andreas W. Neitzel develops for it as co-investigator.
lede: An FCT exploratory project to read the Milky Way's history from its red giants, star by star, with ages from TESS, orbits from Gaia and chemistry from APOGEE and JANUS.
extra_css: [/assets/css/papers.css]
---
<figure class="panel blueprint guide-wide" data-build>
  {% include figures/arqueogal.svg %}
  <figcaption class="credit">How the pieces of the project fit. The three surveys are prepared once in the integration repository, with selection, the mandatory corrections, kinematics and provenance on every file; JANUS supplies the stellar labels and Starfold the populations, each from its own repository and called through a checked hand-off; the result is a map of the disc by age, chemistry and motion. After the responsibility boundary in the repository's README.</figcaption>
</figure>

<div class="article-layout">
  <article class="stack-m">
    <div class="prose article">
      <h2>The project</h2>
      <p>ArqueoGal, in full "Unraveling the evolutionary history of the Milky Way with Galactic Archaeology", is an FCT exploratory research project led by Tiago L. Campante at IA, with the Universities of Padova and Bologna as partners, running from February 2026 to August 2027. It sets out to build a high-resolution map of the Galactic disc in age, chemistry and kinematics from the red giants whose oscillations <i>TESS</i> has measured: asteroseismic ages from <i>TESS</i>, astrometry and orbits from <i>Gaia</i>, and abundances from APOGEE, with a machine-learning tool to classify the stellar populations.</p>
      <h2>My part</h2>
      <p>I am a co-investigator (team member) on the project and I develop its machine-learning pipelines, with allocations on the stellar population classification and Galactic modelling tasks. That work has three repositories. ArqueoGal itself is the platform: it prepares and corrects the observational catalogues, computes the kinematics and assembles the project's deliverables under an explicit release policy, with provenance on every file. It contains no model. JANUS, in its own repository, owns the <i>Gaia</i> XP input chain, the normalising-flow ensemble and the per-star reliability. Starfold, open source, owns the population search and its recurrence evidence. ArqueoGal hands each tool its input and receives a scored table back, so the three can be tested and replaced on their own.</p>
      <h2>Where it runs</h2>
      <p>The two FCT advanced-computing projects on Deucalion and MareNostrum 5, which I hold as responsible investigator, run the JANUS side of this work. My PhD fellowship since September 2026 is paid by the project.</p>
    </div>
  </article>
  <aside class="article-aside">
    <section class="card"><div class="card-body">
      <span class="tag tag--grant">FCT exploratory project</span>
      <p class="small">2024.15303.PEX · PI Tiago L. Campante · IA, with Padova and Bologna · 16 February 2026 to 15 August 2027 · my role: co-investigator (team member), developer of the machine-learning pipelines.</p>
      <p class="links"><a href="https://doi.org/10.54499/2024.15303.PEX">doi:10.54499/2024.15303.PEX</a></p>
    </div></section>
    <section class="card"><div class="card-body">
      <h2 class="zone-title">Code</h2>
      <ul class="list small">
        <li><a href="https://github.com/AndreasWNeitzel/ArqueoGal">ArqueoGal integration repository</a>, public</li>
        <li><a href="{{ '/research/janus/' | relative_url }}">JANUS</a>, private until the paper is submitted</li>
        <li><a href="https://github.com/AndreasWNeitzel/starfold">Starfold</a>, MIT, with <a href="{{ '/software/starfold-demo/' | relative_url }}">the demo</a></li>
      </ul>
    </div></section>
    <section class="card"><div class="card-body">
      <h2 class="zone-title">Related</h2>
      <ul class="list small">
        <li><a href="{{ '/guide/galactic-archaeology/' | relative_url }}">Galactic archaeology, in a minute</a></li>
        <li><a href="{{ '/guide/ia-porto/' | relative_url }}">IA and FCT, in a minute</a></li>
        <li><a href="{{ '/papers/neitzel-2025-manifold-learning/' | relative_url }}">The 2025 paper, where the population method was tested</a></li>
      </ul>
    </div></section>
  </aside>
</div>
