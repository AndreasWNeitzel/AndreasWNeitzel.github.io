---
layout: page
permalink: /research/
title: Research
copy: research
extra_css: [/assets/css/fig1.css, /assets/css/thesis.css]
lines:
  - id: janus
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
    img: /assets/img/heroes/software_chem.webp
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
    img: /assets/img/heroes/line_hpc.webp
    url: /guide/supercomputers/
    links:
      - {label: "The supercomputers, in a minute", url: /guide/supercomputers/}
      - {label: "What runs on them", url: /research/janus/}
  - id: paranal
    img: /assets/img/heroes/eso_golden.webp
    url: /observing/paranal/
    links:
      - {label: "The observing run", url: /observing/paranal/}
      - {label: "The paper, explained", url: /papers/campante-2026-gj570a/}
      - {label: "ESO and the VLT, in a minute", url: /guide/eso-vlt/}
  - id: haydn
    img: /assets/img/heroes/software_cluster.webp
    url: /software/haydnsim/
    links:
      - {label: "The pipeline", url: /software/haydnsim/}
      - {label: "What is HAYDN?", url: /guide/haydn/}
      - {label: "INAF, in a minute", url: /guide/inaf/}
---
{%- assign C = site.data.copy.research -%}
<div class="k-scale">{% include fig1.html %}</div>

<div class="section">
<div class="lines">
  {%- for ln in page.lines %}{% assign c = C.lines | where: "id", ln.id | first %}
  <article class="line k-card" id="{{ ln.id }}">
    <div class="line-pic"><img src="{{ ln.img | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async"></div>
    <div class="card-body">
      <span class="kicker">{{ c.kicker | missions }}</span>
      <h2><a class="line-link" href="{{ ln.url | relative_url }}">{{ c.title | missions }}</a></h2>
      <p>{{ c.text | missions }}</p>
      <p class="textlinks">{% for l in ln.links %}<a href="{{ l.url | relative_url }}">{{ l.label | missions }}</a>{% endfor %}</p>
    </div>
  </article>
  {%- endfor %}
</div>
</div>

<section class="section" id="explainers" aria-labelledby="explainers-title">
  <div class="section-head k-up"><h2 id="explainers-title">Papers, explained</h2><p>{{ C.explainers_lead }} <a href="{{ '/publications/' | relative_url }}">The full list with DOIs is on the Publications page.</a></p></div>
  <div class="mosaic mosaic--pairs">
    {%- assign ps = site.papers | sort: "order" -%}
    {%- for x in ps %}
    <div class="card-wrap{% if x.card_wide %} wide{% endif %} k-up">
      <a class="card" href="{{ x.url | relative_url }}">
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

<p class="prose k-up"><a href="{{ '/guide/' | relative_url }}">{{ C.guide_line | missions }}</a></p>
