---
layout: page
permalink: /publications/
title: Publications
description: Refereed papers by Andreas W. Neitzel, with DOI and arXiv links, his contribution to each, and plain-language explainers.
lede: Four refereed papers in Astronomy and Astrophysics, one as first author, each with my contribution stated and a plain-language explainer.
---
{%- assign L = site.data.ledger -%}
<section class="section" aria-labelledby="first">
  <div class="section-head"><h2 id="first">First author</h2></div>
  <div class="bib-list">{% bibliography --query @*[lead=first] %}</div>
</section>
<section class="section" aria-labelledby="co">
  <div class="section-head"><h2 id="co">Co-author</h2><p>Each entry states what I did in the paper.</p></div>
  <div class="bib-list">{% bibliography --query @*[lead=co] %}</div>
</section>

<section class="section" id="explainers" aria-labelledby="explainers-title">
  <div class="section-head"><h2 id="explainers-title">Explainers</h2><p>What each paper found and what I did, for readers outside astronomy.</p></div>
  <div class="mosaic">
    {%- assign ps = site.papers | sort: "order" -%}
    {%- for x in ps %}
    <a class="card{% if forloop.first %} wide{% endif %}" href="{{ x.url | relative_url }}" data-spotlight>
      {%- if x.figure %}<div class="media light"><img src="{{ x.figure | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async"></div>{% else %}<div class="media art">{% include figures/art-clusters.svg %}</div>{% endif %}
      <div class="card-body">
        <span class="tag tag--paper">{{ x.year }} · {{ x.role }}</span>
        <h3>{{ x.headline | missions }}</h3>
        <p>{{ x.title | missions | truncate: 120 }}</p>
        <span class="go">Read the explainer</span>
      </div>
    </a>
    {%- endfor %}
  </div>
</section>

{%- assign other = L.publications | where_exp: "e", "e.kind == 'data' or e.kind == 'thesis'" -%}
{%- if other.size > 0 %}
<section class="section" aria-labelledby="other">
  <div class="section-head"><h2 id="other">Thesis and data</h2></div>
  <ol class="entries">
    {%- for e in other %}{% include ledger_entry.html e=e category="publications" %}{% endfor %}
  </ol>
</section>
{%- endif %}

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
