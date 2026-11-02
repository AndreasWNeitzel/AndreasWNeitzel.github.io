---
layout: page
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
  eso-vlt: /assets/img/heroes/eso_daylight.webp
---
<div class="guide-grid">
  {%- assign gs = site.guide | sort: "order" -%}
  {%- for g in gs %}
  {%- assign slug = g.url | split: "/" | last -%}
  {%- assign ci = page.cards[slug] -%}
  <a class="card k-up" href="{{ g.url | relative_url }}">
    <div class="media">{% if ci %}<img src="{{ ci | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async">{% elsif g.image and g.image != "" %}<img src="{{ g.image | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async">{% elsif g.photo %}<img src="{{ g.photo | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async">{% else %}<img src="{{ '/assets/img/photos/vlt-golden-hour.webp' | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async">{% endif %}</div>
    <div class="card-body">
      <h3>{{ g.title | missions }}</h3>
      <p>{{ g.lede | missions }}</p>
      <span class="go">Read</span>
    </div>
  </a>
  {%- endfor %}
</div>
