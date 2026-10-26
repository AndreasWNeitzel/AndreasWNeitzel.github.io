---
layout: page
permalink: /research/janus/
title: JANUS
nav_section: Research
crumb: {label: Research, url: /research/}
description: JANUS, the neural network Andreas W. Neitzel wrote to read the chemistry of red giants from Gaia's low-resolution spectra, with a reliability score for every star.
lede: A neural network that reads a red giant's parameters and chemistry from its Gaia spectrum, and says how far to trust each answer.
extra_css: [/assets/css/fig1.css]
math: true
---
<figure class="panel blueprint guide-wide" data-build>
  {% include figures/janus.svg %}
  <figcaption class="credit">The JANUS stages of the pipeline on the home page: a real <i>Gaia</i> XP spectrum of a red giant (DR3 5289554869898620416) and the seismic input from <i>TESS</i> and <i>Kepler</i> go into the ensemble of eight normalising-flow networks, 110 inputs to six outputs, which returns each label with a spread and a calibrated miss probability. On stars withheld from training (IMAS13, October 2026) the robust scatter about APOGEE is 32 K in <span class="tex" data-tex="T_\mathrm{eff}">T_eff</span>, 0.072 dex in <span class="tex" data-tex="\log g">log g</span>, 0.051 dex in [M/H] and 0.021 dex in <span class="tex" data-tex="[\alpha/\mathrm{M}]">[α/M]</span>; the catalogue covers 144,304 <i>TESS</i> red giants, about nine times as many as have APOGEE DR19 values passing the same cuts.</figcaption>
</figure>

<div class="article-layout">
  <article class="stack-m">
    <div class="prose article">
      <h2>The problem</h2>
      <p><i>TESS</i> has measured the frequency of maximum oscillation power for about 158,000 red giants across the sky, and asteroseismology turns that into masses and ages. Ages put the events of Galactic history in sequence: the formation of the thick and thin discs, the merger of accreted systems such as <i>Gaia</i>-Enceladus, the migration of stars through the disc. Reading that history also needs each star's chemistry, and the high-resolution surveys cover few of these stars: about one in ten has APOGEE DR19 values that pass the quality cuts.</p>
      <h2>What JANUS does</h2>
      <p>JANUS (Joint Abundance Network with Uncertainty and Stratification) is an ensemble of neural networks built on conditional normalising flows, trained on APOGEE DR19. From the low-resolution <i>Gaia</i> BP/RP spectrum of a red giant, with its astrometry, photometry and extinction, it predicts a joint probability distribution over <span class="tex" data-tex="T_\mathrm{eff}">T_eff</span>, <span class="tex" data-tex="\log g">log g</span>, [M/H], [Fe/H], <span class="tex" data-tex="[\alpha/\mathrm{M}]">[α/M]</span> and individual abundances. Each star also receives a novelty score and a calibrated probability that its atmospheric parameters miss the APOGEE values, so that a user can choose which stars to trust.</p>
      <h2>What the tests showed</h2>
      <p>On stars withheld from training the robust scatter about APOGEE is 32 K, 0.072 dex, 0.051 dex and 0.021 dex in the four parameters above, with calibrated uncertainties. Repeating every test with a model trained without the spectrum shows that the XP spectra carry information on [M/H], <span class="tex" data-tex="[\alpha/\mathrm{M}]">[α/M]</span>, carbon and nitrogen, and that JANUS separates the two α sequences of the disc, which the model without the spectrum merges.</p>
      <h2>Where it runs</h2>
      <p>Two FCT advanced-computing projects carry the work, both with me as responsible investigator: 299,520 ARM core-hours and 1,500 A100 GPU-hours on Deucalion to run JANUS on the <i>Gaia</i> DR3 spectra of about 220 million stars, and 1,002,400 core-hours and 1,000 H100 GPU-hours on MareNostrum 5 for <i>Gaia</i> DR4. The catalogue is the chemistry layer of ArqueoGal and will be released through the project.</p>
    </div>
  </article>
  <aside class="article-aside">
    <section class="card"><div class="card-body">
      <span class="tag tag--software">research software</span>
      <p class="small">JANUS, sole developer, 2025 to 2027. PhD work within the FCT project ArqueoGal. The paper is in preparation; the repository is private until it is submitted.</p>
    </div></section>
    <section class="card"><div class="card-body">
      <h2 class="zone-title">Presented at</h2>
      <ul class="list small">
        <li>IMAS13, Cádiar, October 2026 (talk)</li>
        <li>ENAA XXXVI, Porto, September 2026 (poster)</li>
        <li>TASC10/KASC17, Aarhus, July 2026 (talk, <a href="https://doi.org/10.5281/zenodo.23262691">slides on Zenodo</a>)</li>
        <li>IA Stars Day, Porto, May 2026</li>
      </ul>
    </div></section>
    <section class="card"><div class="card-body">
      <h2 class="zone-title">Related</h2>
      <ul class="list small">
        <li><a href="{{ '/research/arqueogal/' | relative_url }}">ArqueoGal, the project</a></li>
        <li><a href="{{ '/guide/machine-learning-for-stars/' | relative_url }}">Machine learning for stars, in a minute</a></li>
        <li><a href="{{ '/playground/neural-network/' | relative_url }}">Train a small network on <i>Gaia</i> spectra</a></li>
        <li><a href="{{ '/guide/supercomputers/' | relative_url }}">The supercomputers</a></li>
      </ul>
    </div></section>
  </aside>
</div>
