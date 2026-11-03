---
layout: default
permalink: /guide/
title: Field guide
copy: guide
cards:
  gaia: /assets/img/heroes/line_gaia.webp
  supercomputers: /assets/img/heroes/line_hpc.webp
  haydn: /assets/img/heroes/software_cluster.webp
  galactic-archaeology: /assets/img/heroes/research_allsky.webp
  asteroseismology: /assets/img/heroes/research_seismo.webp
  machine-learning-for-stars: /assets/img/heroes/line_janus.webp
  eso-vlt: /assets/img/photos/vlt-daylight.webp
  plato: /assets/img/heroes/plato_card.webp
  ariel: /assets/img/heroes/ariel_card.webp
loop_pos:
  plato: "72% 50%"
  tess-kepler: "77% 50%"
loops:
  gaia: gaia
  supercomputers: hall
  haydn: cluster
  machine-learning-for-stars: ai
  plato: plato
  tess-kepler: pair
---
{%- assign CP = site.data.copy.plates -%}
{% include plate.html loop="paranal" still="/assets/img/photos/vlt-golden-hour.webp" alt="Me on the VLT platform at Paranal at sunset, with the Unit Telescopes behind me" title="Field guide" line=CP.guide pos="50% 100%" textw="36vw" lift=true %}
<div class="wrap">
<section class="section section--tight">
  <div class="rows">
    {%- assign gs = site.guide | sort: "order" -%}
    {%- for g in gs %}
    {%- assign slug = g.url | split: "/" | last -%}
    {%- assign ci = page.cards[slug] -%}
    {%- assign lp = page.loops[slug] -%}
    {%- assign vf = nil -%}{% if lp %}{% assign vpath = "/assets/video/" | append: lp | append: ".av1.mp4" %}{% assign vf = site.static_files | where: "path", vpath | first %}{% endif %}
    <article class="row-item k-up">
      <div class="pic">
        {%- assign lpos = page.loop_pos[slug] -%}{%- if vf %}{% include loop.html name=lp alt="" pos=lpos %}
        {%- elsif ci %}<img src="{{ ci | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async">
        {%- elsif g.image and g.image != "" %}<img src="{{ g.image | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async">{% if g.image_credit %}<a class="ccredit" href="{{ g.image_source }}">{{ g.image_credit }}, {{ g.image_licence }}</a>{% endif %}
        {%- elsif g.photo %}<img src="{{ g.photo | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async">{% endif %}
      </div>
      <div class="words">
        <h2><a href="{{ g.url | relative_url }}">{{ g.title | missions }}</a></h2>
        <p>{{ g.lede | missions }}</p>
      </div>
    </article>
    {%- endfor %}
  </div>
</section>
</div>
