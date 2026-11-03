---
layout: default
permalink: /publications/
title: Publications
copy: publications
extra_links:
  pub-2022-msc-thesis:
    - {label: Plain-language explainer, url: /papers/neitzel-2022-msc-thesis/}
extra_css: [/assets/css/thesis.css]
---
{%- assign L = site.data.ledger -%}
{%- assign C = site.data.copy.publications -%}
{%- assign CP = site.data.copy.plates -%}
{% include plate.html still="/assets/img/heroes/publications.webp" alt="The published figures as printed sheets on a desk" title="Publications" line=CP.publications %}
<div class="wrap">
<section class="section section--tight" id="explainers" aria-labelledby="explainers-title">
  <div class="section-head k-up"><h2 id="explainers-title">Explainers</h2><p>{{ C.explainers_lead }}</p></div>
  {% include explainers.html %}
</section>
<section class="section" aria-labelledby="first">
  <div class="section-head k-up"><h2 id="first">First author</h2></div>
  <div class="bib-list">{% bibliography --query @*[lead=first] %}</div>
</section>
<section class="section" aria-labelledby="co">
  <div class="section-head k-up"><h2 id="co">Co-author</h2></div>
  <div class="bib-list">{% bibliography --query @*[lead=co] %}</div>
</section>
{%- assign inprep = L.publications | where: "kind", "in-preparation" -%}
{%- if inprep.size > 0 %}
<section class="section" aria-labelledby="inprep">
  <div class="section-head k-up"><h2 id="inprep">In preparation</h2></div>
  <ol class="entries">
    {%- for e in inprep %}{% include ledger_entry.html e=e category="publications" label="in preparation" when="2026" %}{% endfor %}
  </ol>
</section>
{%- endif %}
{%- assign other = L.publications | where_exp: "e", "e.kind == 'data' or e.kind == 'thesis'" -%}
{%- if other.size > 0 %}
<section class="section" aria-labelledby="other">
  <div class="section-head k-up"><h2 id="other">Thesis and data</h2></div>
  <ol class="entries">
    {%- for e in other %}{% assign extra = page.extra_links[e.id] %}{% include ledger_entry.html e=e category="publications" extra=extra %}{% endfor %}
  </ol>
</section>
{%- endif %}
</div>
{%- assign refereed = L.publications | where_exp: "e", "e.kind == 'article' or e.kind == 'letter'" %}
<script type="application/ld+json">
[
{%- for e in refereed %}
  {
    "@context": "https://schema.org",
    "@type": "ScholarlyArticle",
    {%- if e.identifiers.doi %}
    "@id": "https://doi.org/{{ e.identifiers.doi }}",
    "sameAs": ["https://doi.org/{{ e.identifiers.doi }}"{% if e.identifiers.arxiv %}, "https://arxiv.org/abs/{{ e.identifiers.arxiv }}"{% endif %}],
    {%- else %}
    "@id": "https://arxiv.org/abs/{{ e.identifiers.arxiv }}",
    {%- endif %}
    "headline": {{ e.title | jsonify }},
    "datePublished": "{{ e.date | slice: 0, 4 }}",
    "isPartOf": {"@type": "Periodical", "name": "Astronomy and Astrophysics"},
    "author": [
      {%- for a in e.people %}
      {% assign self = false %}{% if a contains "Neitzel" %}{% unless a contains "et al." %}{% assign self = true %}{% endunless %}{% endif %}{% if self %}{"@id": "{{ site.url }}/#person"}{% else %}{"@type": "Person", "name": {{ a | jsonify }}}{% endif %}{% unless forloop.last %},{% endunless %}
      {%- endfor %}
    ]
  }{% unless forloop.last %},{% endunless %}
{%- endfor %}
]
</script>
