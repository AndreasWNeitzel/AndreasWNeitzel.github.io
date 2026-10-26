---
layout: page
permalink: /research/
title: Research
description: The research of Andreas W. Neitzel, machine learning for Galactic archaeology, in four lines of work, with the papers explained and the background in one minute each.
lede: Six lines of work, one chain. Neural networks read red-giant chemistry from Gaia spectra, unsupervised methods find the populations, asteroseismology sets their ages, and a simulation tests HAYDN.
extra_css: [/assets/css/thesis.css]
---
{%- assign L = site.data.ledger -%}
<div class="lines">
  <article class="line card" id="janus">
    <div class="line-pic">{% include figures/art-nn.svg %}</div>
    <div class="card-body">
      <span class="kicker">2025 to 2027 · PhD work within the FCT project ArqueoGal</span>
      <h2><a class="line-link" href="{{ '/research/janus/' | relative_url }}">JANUS: chemistry from <i>Gaia</i> spectra</a></h2>
      <p><i>Gaia</i> DR3 carries low-resolution spectra of 220 million stars. JANUS, eight normalising-flow networks, reads a red giant's parameters and abundances from them, with a per-star miss probability. Trained where <i>Gaia</i> overlaps APOGEE, validated on open clusters, wide binaries and the first dredge-up. Talks at TASC10/KASC17 and IMAS13; two FCT projects on Deucalion and MareNostrum 5.</p>
      <p class="links"><a href="{{ '/research/janus/' | relative_url }}">JANUS, in full</a> · <a href="{{ '/talks/' | relative_url }}">The talks</a> · <a href="{{ '/guide/machine-learning-for-stars/' | relative_url }}">Machine learning for stars, in a minute</a> · <a href="{{ '/playground/neural-network/' | relative_url }}">Train a small one yourself</a></p>
    </div>
  </article>
  <article class="line card" id="arqueogal">
    <div class="line-pic"><img src="{{ '/assets/img/guide/supercomputers.webp' | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async"></div>
    <div class="card-body">
      <span class="kicker">2026 to 2027 · FCT exploratory project 2024.15303.PEX · PI T. L. Campante</span>
      <h2><a class="line-link" href="{{ '/research/arqueogal/' | relative_url }}">ArqueoGal: the project the pipelines serve</a></h2>
      <p>ArqueoGal is an FCT exploratory project to unravel the Milky Way's history with Galactic archaeology, led by Tiago L. Campante. I am a co-investigator (team member) and I develop its machine-learning pipelines: JANUS for the stellar labels, Starfold for the populations, and the integration repository that prepares <i>Gaia</i> DR3 and APOGEE DR19 data with provenance for both. The two FCT computing allocations on Deucalion and MareNostrum 5 run that work.</p>
      <p class="links"><a href="{{ '/research/arqueogal/' | relative_url }}">ArqueoGal, in full</a> · <a href="https://doi.org/10.54499/2024.15303.PEX">The project record</a> · <a href="https://github.com/AndreasWNeitzel/ArqueoGal">The integration repository</a></p>
    </div>
  </article>
  <article class="line card" id="populations">
    <div class="line-pic">{% include figures/art-clusters.svg %}</div>
    <div class="card-body">
      <span class="kicker">2023 to now · A&amp;A 695, A243 and Starfold</span>
      <h2><a class="line-link" href="{{ '/papers/neitzel-2025-manifold-learning/' | relative_url }}">Stellar populations without labels</a></h2>
      <p>My 2025 A&amp;A paper tested manifold learning on a simulated galaxy without labels, and shows where realistic errors break it. Starfold, open source, picks UMAP and HDBSCAN settings itself, refits to test stability and raises one of 17 named warnings. On four held-out tables it beat the defaults on two and lost on two.</p>
      <p class="links"><a href="{{ '/papers/neitzel-2025-manifold-learning/' | relative_url }}">The paper, explained</a> · <a href="{{ '/software/starfold-demo/' | relative_url }}">Starfold on 9,242 stars</a> · <a href="{{ '/software/starfold-benchmark/' | relative_url }}">The benchmark</a> · <a href="{{ '/guide/galactic-archaeology/' | relative_url }}">Galactic archaeology, in a minute</a></p>
    </div>
  </article>
  <article class="line card" id="seismology">
    <div class="line-pic"><img src="{{ '/assets/img/photos/ut-mirror-cell.webp' | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async"></div>
    <div class="card-body">
      <span class="kicker">2021 to now · <i>TESS</i>, <i>Kepler</i>, ESPRESSO</span>
      <h2><a class="line-link" href="{{ '/papers/neitzel-2022-msc-thesis/' | relative_url }}">Asteroseismology, the clock</a></h2>
      <p>My MSc dissertation measured how seismology tightens ages of Sun-like planet hosts in the <i>Ariel</i> target list. With ESPRESSO at the VLT I observed on the campaign that detected oscillations in GJ 570 A, and I contributed to <i>Ariel</i> stellar characterisation and the ε Indi detection. <i>TESS</i> and <i>Kepler</i> ages anchor the main chain.</p>
      <p class="links"><a href="{{ '/observing/paranal/' | relative_url }}">Two nights at Paranal</a> · <a href="{{ '/papers/neitzel-2022-msc-thesis/' | relative_url }}">The dissertation, explained</a> · <a href="{{ '/guide/asteroseismology/' | relative_url }}">Asteroseismology, in a minute</a></p>
    </div>
  </article>
  <article class="line card" id="paranal">
    <div class="line-pic"><img src="{{ '/assets/img/photos/vlt-golden-hour.webp' | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async"></div>
    <div class="card-body">
      <span class="kicker">May 2024 · ESO Very Large Telescope, Paranal</span>
      <h2><a class="line-link" href="{{ '/observing/paranal/' | relative_url }}">Two nights at Paranal</a></h2>
      <p>Visiting astronomer for the ESPRESSO campaign on GJ 570 A: 571 exposures in one night, 2,250 velocities over five, and the oscillations they revealed, now in A&amp;A. The page follows the starlight from the 8.2 m mirror to one velocity, with the photographs from the run.</p>
      <p class="links"><a href="{{ '/observing/paranal/' | relative_url }}">The observing run</a> · <a href="{{ '/papers/campante-2026-gj570a/' | relative_url }}">The paper, explained</a> · <a href="{{ '/guide/eso-vlt/' | relative_url }}">ESO and the VLT, in a minute</a></p>
    </div>
  </article>
  <article class="line card" id="haydn">
    <div class="line-pic"><img src="{{ '/assets/img/guide/haydn.webp' | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async"></div>
    <div class="card-body">
      <span class="kicker">2025 to 2026 · INAF-OAS Bologna</span>
      <h2><a class="line-link" href="{{ '/software/haydnsim/' | relative_url }}">HAYDNsim: can the mission see into a cluster?</a></h2>
      <p><i>HAYDN</i> is a proposed ESA mission for asteroseismology in dense clusters. During a six-month secondment in Bologna I wrote HAYDNsim, which builds a synthetic field, runs it through the mission's noise estimator on Deucalion, and returns the noise and share of borrowed light for every star. Poster at TASC10/KASC17; paper in preparation.</p>
      <p class="links"><a href="{{ '/software/haydnsim/' | relative_url }}">The pipeline</a> · <a href="{{ '/guide/haydn/' | relative_url }}">What is <i>HAYDN</i>?</a> · <a href="{{ '/guide/inaf/' | relative_url }}">INAF, in a minute</a></p>
    </div>
  </article>
</div>

<section class="section" id="explainers" aria-labelledby="explainers-title">
  <div class="section-head"><h2 id="explainers-title">Papers, explained</h2><p>Each paper explained for non-specialists. <a href="{{ '/publications/' | relative_url }}">Full list with DOIs on the Publications page.</a></p></div>
  <div class="mosaic mosaic--pairs">
    {%- assign ps = site.papers | sort: "order" -%}
    {%- for x in ps %}
    <div class="card-wrap{% if x.card_wide %} wide{% endif %}">
      <a class="card" href="{{ x.url | relative_url }}" data-spotlight>
        {%- if x.card_wide and x.wide_figure %}<div class="media art" data-build>{% include {{ x.wide_figure }} %}</div>
        {%- elsif x.card_image %}<div class="media{% if x.card_light %} light{% endif %}"><img src="{{ x.card_image | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async"></div>{% else %}<div class="media art">{% include figures/art-hr.svg %}</div>{% endif %}
        <div class="card-body">
          <span class="tag tag--paper">{{ x.year }} · {{ x.role }}</span>
          <h3>{{ x.headline | missions }}</h3>
          <p>{{ x.title | missions | truncate: 120 }}</p>
          <span class="go">Read the explainer</span>
        </div>
      </a>
      {%- if x.card_credit %}<a class="ccredit" href="{{ x.card_credit_url }}">{{ x.card_credit }}</a>{% endif %}
    </div>
    {%- endfor %}
  </div>
</section>

<p class="prose"><a href="{{ '/guide/' | relative_url }}">The field guide</a> explains the science, the institutions and the machines behind this work, one minute each.</p>
