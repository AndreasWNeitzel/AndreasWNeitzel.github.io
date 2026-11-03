---
layout: default
permalink: /visualisations/
title: Visualisations
copy: visualisations
extra_css: [/assets/css/visualisations.css]
# The album in four sections. Each section is a grid of its own, placed by grid areas in visualisations.css (area = id),
# on one 12-column grid whose seams fall only after column 5 or column 7. A tile shows a loop (assets/video/<loop>,
# poster in assets/img/heroes), a still (img) or a figure (svg, from _includes/figures). credit names the key of a
# third-party credit in _data/home.yml guide_loop_credits; my own work carries none. Section headings and intros come
# from _data/copy.yml visualisations.sections (same id).
sections:
  - id: craft
    # the four craft loops are framed on the craft: fit sets the video's height as a multiple of the tile's height (vz)
    # and the craft's centre as a fraction of the frame (cx, cy), measured over a whole turn on frames of each loop, so the
    # craft fills about 65 per cent of the tile's height at any width and never leaves it while it turns
    credit: "Mock-ups after NASA and ESA references; TESS on NASA 3D Resources mesh; sky ESO/S. Brunier, CC BY 4.0"
    tiles:
      - {id: gaia, loop: gaia-hd, pos: "50% 50%"}
      - {id: plato, loop: plato, fit: "--vz: 1.133; --cx: .639; --cy: .498"}
      - {id: kepler, loop: mcard-kepler, fit: "--vz: 1.111; --cx: .639; --cy: .503"}
      - {id: ariel, loop: ariel, fit: "--vz: 1.02; --cx: .640; --cy: .499"}
      - {id: tess, loop: pair, fit: "--vz: 1.09; --cx: .453; --cy: .500"}
  - id: stars
    tiles:
      - {id: seismo, img: /assets/img/heroes/research_seismo.webp, pos: "50% 60%"}
      - {id: pipeline, loop: pipeline-hd, poster: /assets/img/visualisations/pipeline-galaxy.poster.webp, start: 52}
      - {id: allsky, img: /assets/img/heroes/research_allsky.webp}
      - {id: sky, loop: sky-hd, pos: "48% 50%"}
      - {id: field, svg: figures/haydn-field.svg}
  - id: data
    tiles:
      - {id: starfold, img: /assets/img/visualisations/starfold-dashboard.webp, pos: "0% 0%"}
      - {id: hall, loop: hall-hd}
      - {id: unroll, loop: starfold}
      - {id: janus, loop: ai-hd, pos: "40% 50%"}
  - id: tools
    tiles:
      - {id: explorer, img: /assets/img/heroes/card_explorer.webp, pos: "50% 12%"}
      - {id: travel, img: /assets/img/visualisations/travel-map.webp, pos: "58% 50%"}
      - {id: tellurion, img: /assets/img/tellurion/blackhole-legend-3d.webp, pos: "50% 55%"}
      - {id: nn, img: /assets/img/heroes/card_nn.webp, pos: "50% 45%"}
      - {id: gp, img: /assets/img/heroes/card_gp.webp, pos: "50% 45%"}
      - {id: orbits, img: /assets/img/heroes/card_orbits.webp, pos: "50% 45%"}
      - {id: polytropes, img: /assets/img/heroes/card_polytrope.webp, pos: "50% 40%"}
---
{%- assign C = site.data.copy.visualisations -%}
{%- assign LC = site.data.home.guide_loop_credits -%}
{% include plate.html stage=true loop="vishead" still="/assets/img/heroes/vishead.poster.webp" alt=C.header_alt title=C.title line=C.line %}
<div class="wrap vis" data-album>
  <p class="vis-intro">{{ C.intro | missions }}</p>
  {%- for s in page.sections %}{% assign sc = C.sections | where: "id", s.id | first %}
  <section class="vis-sec" aria-labelledby="vis-sec-{{ s.id }}">
    <header class="vis-head">
      <h2 id="vis-sec-{{ s.id }}">{{ sc.title | missions }}</h2>
      <p>{{ sc.intro | missions }}</p>
    </header>
    <div class="vis-grid vis-grid--{{ s.id }}">
      {%- for t in s.tiles %}{% assign c = C.tiles | where: "id", t.id | first %}
      <article class="vis-tile{% if t.svg %} vis-tile--fig{% endif %}" data-id="{{ t.id }}" style="--area: {{ t.id }}" tabindex="0" aria-labelledby="vis-{{ t.id }}">
        <div class="vis-media{% if t.fit %} vis-media--fit{% endif %}"{% if t.fit %} style="{{ t.fit }}"{% elsif t.pos %} style="--pos: {{ t.pos }}"{% endif %}>
          {%- if t.loop %}{% include loop.html name=t.loop alt=c.alt pos=t.pos poster=t.poster start=t.start %}
          {%- elsif t.img %}<img src="{{ t.img | relative_url }}" alt="{{ c.alt }}" loading="lazy" decoding="async">
          {%- elsif t.svg %}{% include {{ t.svg }} %}{% endif %}
        </div>
        {%- if t.credit %}<a class="ccredit" href="{{ '/credits/' | relative_url }}">{{ LC[t.credit] }}</a>{% endif %}
        <div class="vis-glass"><h3 id="vis-{{ t.id }}">{{ c.title | missions }}</h3><p>{{ c.line | missions }}</p></div>
      </article>
      {%- endfor %}
    </div>
    {%- if s.credit %}<p class="vis-credit"><a href="{{ '/credits/' | relative_url }}">{{ s.credit }}</a></p>{% endif %}
  </section>
  {%- endfor %}
</div>
