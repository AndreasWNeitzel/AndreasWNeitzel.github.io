---
layout: default
permalink: /guide/space-missions/
title: Space missions
nav_section: Guide
extra_css: [/assets/css/thesis.css]
description: The space telescopes behind Andreas W. Neitzel's research, with what each contributes to his work.
lines:
  - {id: gaia, loop: mcard-gaia, url: /guide/gaia/}
  - {id: plato, loop: plato, url: /guide/plato/}
  - {id: tess, loop: tess, url: /guide/tess-kepler/}
  - {id: kepler, loop: mcard-kepler, url: /guide/tess-kepler/}
  - {id: ariel, loop: ariel, url: /guide/ariel/}
  - {id: haydn, loop: cluster, url: /guide/haydn/}
---
{%- assign M = site.data.copy.home.missions -%}
{%- assign CP = site.data.copy.plates -%}
{%- assign mcredit = "Mock-ups after NASA and ESA references; TESS on NASA 3D Resources mesh; sky ESO/S. Brunier, CC BY 4.0" -%}
{% include plate.html stage=true loop="missions" still="/assets/img/heroes/missions.poster.webp" alt="Gaia, PLATO, TESS, Kepler and Ariel turn in turn against the Milky Way" title="Space missions" line=CP.missions loop_credit=mcredit %}
<div class="wrap">
<section class="section section--tight">
  <div class="rows">
    {%- for ln in page.lines %}{% assign c = M | where: "id", ln.id | first %}{% assign g = site.guide | where: "url", ln.url | first %}
    <article class="row-item k-up" id="{{ ln.id }}">
      <div class="pic">{% if ln.loop %}{% include loop.html name=ln.loop alt="" %}{% else %}<img src="{{ ln.img | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async">{% endif %}</div>
      <div class="words">
        <span class="kicker">{{ c.who }}</span>
        <h2><a href="{{ ln.url | relative_url }}">{{ c.name }}</a></h2>
        <p>{{ c.line | missions }}</p>
        <p class="textlinks"><a href="{{ ln.url | relative_url }}">{{ g.title | default: "In the field guide" | missions }}</a></p>
      </div>
    </article>
    {%- endfor %}
  </div>
</section>
</div>
