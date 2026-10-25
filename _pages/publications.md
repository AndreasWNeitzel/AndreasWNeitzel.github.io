---
layout: page
permalink: /publications/
title: Publications
description: Refereed papers by Andreas W. Neitzel, with DOI and arXiv links.
lede: Refereed papers, first-author first. Each entry links to the journal record by DOI and to arXiv where a preprint exists.
---
{%- assign L = site.data.ledger -%}
<section class="row" aria-labelledby="refereed">
  <h2 id="refereed">Refereed papers</h2>
  {% bibliography %}
</section>
{%- assign prep = L.publications | where: "kind", "in-preparation" -%}
{%- if prep.size > 0 %}
<section class="row" aria-labelledby="inprep">
  <h2 id="inprep">In preparation</h2>
  <ol class="entries">
    {%- for e in prep %}
    {%- include ledger_entry.html e=e category="publications" label="in preparation" %}
    {%- endfor %}
  </ol>
</section>
{%- endif %}
{%- assign theses = L.publications | where: "kind", "thesis" -%}
{%- if theses.size > 0 %}
<section class="row" aria-labelledby="thesis">
  <h2 id="thesis">Thesis</h2>
  <ol class="entries">
    {%- for e in theses %}
    {%- include ledger_entry.html e=e category="publications" %}
    {%- endfor %}
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
    "@id": "https://doi.org/{{ e.identifiers.doi }}",
    "sameAs": ["https://doi.org/{{ e.identifiers.doi }}"{% if e.identifiers.arxiv %}, "https://arxiv.org/abs/{{ e.identifiers.arxiv }}"{% endif %}],
    "headline": {{ e.title | jsonify }},
    "datePublished": "{{ e.date | slice: 0, 4 }}",
    "isPartOf": {"@type": "Periodical", "name": "Astronomy and Astrophysics"},
    "author": [
      {%- for a in e.people %}
      {% if a contains "Neitzel" and a contains "et al." == false %}{"@id": "{{ site.url }}/#person"}{% else %}{"@type": "Person", "name": {{ a | jsonify }}}{% endif %}{% unless forloop.last %},{% endunless %}
      {%- endfor %}
    ]
  }{% unless forloop.last %},{% endunless %}
{%- endfor %}
]
</script>
