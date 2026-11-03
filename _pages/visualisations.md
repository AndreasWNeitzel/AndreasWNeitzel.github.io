---
layout: default
permalink: /visualisations/
title: Visualisations
copy: visualisations
extra_css: [/assets/css/visualisations.css]
# The album: one tile per piece, placed by its grid area in visualisations.css (area = id). A tile shows a loop
# (assets/video/<loop>, poster in assets/img/heroes), a still (img) or a figure (svg, from _includes/figures).
# credit names the key of a third-party credit in _data/home.yml guide_loop_credits; my own work carries none.
tiles:
  - {id: pipeline, loop: pipeline-hd, poster: /assets/img/visualisations/pipeline-galaxy.poster.webp, start: 52}
  - {id: gaia, loop: gaia-hd, pos: "50% 50%"}
  - {id: tellurion, img: /assets/img/tellurion/blackhole-legend-3d.webp, pos: "50% 55%"}
  - {id: hall, loop: hall-hd}
  - {id: starfold, img: /assets/img/visualisations/starfold-dashboard.webp, pos: "0% 0%"}
  - {id: plato, loop: plato, pos: "72% 50%", credit: plato}
  - {id: seismo, img: /assets/img/heroes/research_seismo.webp, pos: "50% 60%"}
  - {id: janus, loop: ai-hd, pos: "40% 50%"}
  - {id: unroll, loop: starfold}
  - {id: ariel, loop: ariel, pos: "86% 50%", credit: ariel}
  - {id: explorer, img: /assets/img/heroes/card_explorer.webp, pos: "62% 50%"}
  - {id: field, svg: figures/haydn-field.svg}
  - {id: allsky, img: /assets/img/heroes/research_allsky.webp}
  - {id: sky, loop: sky-hd, pos: "48% 50%"}
  - {id: travel, img: /assets/img/visualisations/travel-map.webp, pos: "58% 50%"}
---
{%- assign C = site.data.copy.visualisations -%}
{%- assign LC = site.data.home.guide_loop_credits -%}
{%- assign hc = LC["tess-kepler"] -%}
{% include plate.html loop="pair" still="/assets/img/heroes/pair.poster.webp" alt=C.header_alt title=C.title line=C.line loop_credit=hc loop_pos="31% 50%" %}
<div class="wrap">
<section class="section section--tight vis" aria-label="{{ C.title | strip_html }}">
  <div class="vis-grid" data-album>
    {%- for t in page.tiles %}{% assign c = C.tiles | where: "id", t.id | first %}
    <article class="vis-tile{% if t.svg %} vis-tile--fig{% endif %}" data-id="{{ t.id }}" style="--area: {{ t.id }}" tabindex="0" aria-labelledby="vis-{{ t.id }}">
      <div class="vis-media"{% if t.pos %} style="--pos: {{ t.pos }}"{% endif %}>
        {%- if t.loop %}{% include loop.html name=t.loop alt=c.alt pos=t.pos poster=t.poster start=t.start %}
        {%- elsif t.img %}<img src="{{ t.img | relative_url }}" alt="{{ c.alt }}" loading="lazy" decoding="async">
        {%- elsif t.svg %}{% include {{ t.svg }} %}{% endif %}
      </div>
      {%- if t.credit %}<a class="ccredit" href="{{ '/credits/' | relative_url }}">{{ LC[t.credit] }}</a>{% endif %}
      <div class="vis-glass"><h2 id="vis-{{ t.id }}">{{ c.title | missions }}</h2><p>{{ c.line | missions }}</p></div>
    </article>
    {%- endfor %}
  </div>
</section>
</div>
