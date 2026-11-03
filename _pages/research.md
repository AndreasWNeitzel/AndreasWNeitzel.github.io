---
layout: default
permalink: /research/
title: Research
copy: research
extra_css: [/assets/css/thesis.css, /assets/css/research-film.css]
lines:
  - id: janus
    loop: ai
    img: /assets/img/heroes/line_janus.webp
    url: /research/janus/
    links:
      - {label: "JANUS, in full", url: /research/janus/}
      - {label: "The talks", url: /talks/}
      - {label: "Machine learning for stars, in a minute", url: /guide/machine-learning-for-stars/}
      - {label: "Train a small one yourself", url: /playground/neural-network/}
  - id: arqueogal
    img: /assets/img/heroes/research_allsky.webp
    url: /research/arqueogal/
    links:
      - {label: "ArqueoGal, in full", url: /research/arqueogal/}
      - {label: "The project record", url: "https://doi.org/10.54499/2024.15303.PEX"}
      - {label: "The integration repository", url: "https://github.com/AndreasWNeitzel/ArqueoGal"}
  - id: populations
    loop: starfold
    img: /assets/img/heroes/software_starfold.webp
    url: /papers/neitzel-2025-manifold-learning/
    links:
      - {label: "The paper, explained", url: /papers/neitzel-2025-manifold-learning/}
      - {label: "Starfold on 9,242 stars", url: /software/starfold-demo/}
      - {label: "The benchmark", url: /software/starfold-benchmark/}
      - {label: "Galactic archaeology, in a minute", url: /guide/galactic-archaeology/}
  - id: seismology
    img: /assets/img/heroes/research_seismo.webp
    url: /papers/neitzel-2022-msc-thesis/
    links:
      - {label: "Six nights at Paranal", url: /observing/paranal/}
      - {label: "The dissertation, explained", url: /papers/neitzel-2022-msc-thesis/}
      - {label: "Asteroseismology, in a minute", url: /guide/asteroseismology/}
  - id: hpc
    loop: hall
    img: /assets/img/heroes/line_hpc.webp
    url: /guide/supercomputers/
    links:
      - {label: "The supercomputers, in a minute", url: /guide/supercomputers/}
      - {label: "What runs on them", url: /research/janus/}
  - id: paranal
    img: /assets/img/photos/vlt-golden-hour.webp
    url: /observing/paranal/
    links:
      - {label: "The observing run", url: /observing/paranal/}
      - {label: "The paper, explained", url: /papers/campante-2026-gj570a/}
      - {label: "ESO and the VLT, in a minute", url: /guide/eso-vlt/}
  - id: haydn
    loop: cluster
    img: /assets/img/heroes/cluster.poster.webp
    url: /software/haydnsim/
    links:
      - {label: "The pipeline", url: /software/haydnsim/}
      - {label: "What is HAYDN?", url: /guide/haydn/}
      - {label: "INAF, in a minute", url: /guide/inaf/}
---
{%- assign C = site.data.copy.research -%}
{%- assign CP = site.data.copy.plates -%}
{%- assign mcredit = "Mock-ups after NASA and ESA references; TESS on NASA 3D Resources mesh; sky ESO/S. Brunier, CC BY 4.0" -%}
{% include research-film.html title="Research" line=CP.research credit=mcredit %}
<div class="wrap">
<section class="section section--tight">
  <div class="rows">
    {%- for ln in page.lines %}{% assign c = C.lines | where: "id", ln.id | first %}
    <article class="row-item k-up" id="{{ ln.id }}">
      <div class="pic">
        {%- assign vpath = "/assets/video/" | append: ln.loop | append: ".av1.mp4" -%}{%- assign vf = nil -%}{% if ln.loop %}{% assign vf = site.static_files | where: "path", vpath | first %}{% endif %}
        {%- if vf %}{% include loop.html name=ln.loop alt="" %}{% else %}<img src="{{ ln.img | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async">{% endif %}
      </div>
      <div class="words">
        <span class="kicker">{{ c.kicker | missions }}</span>
        <h2><a href="{{ ln.url | relative_url }}">{{ c.title | missions }}</a></h2>
        <p>{{ c.text | missions }}</p>
        <p class="textlinks">{% for l in ln.links %}<a href="{{ l.url | relative_url }}">{{ l.label | missions }}</a>{% endfor %}</p>
      </div>
    </article>
    {%- endfor %}
  </div>
</section>

<section class="section" id="explainers" aria-labelledby="explainers-title">
  <div class="section-head k-up"><h2 id="explainers-title">Papers, explained</h2><a class="more" href="{{ '/publications/' | relative_url }}">The list with DOIs <svg class="i" aria-hidden="true"><use href="#i-arrow"/></svg></a></div>
  {% include explainers.html %}
</section>
</div>
