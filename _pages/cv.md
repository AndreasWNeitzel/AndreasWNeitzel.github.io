---
layout: page
permalink: /cv/
title: Curriculum vitae
description: Education, funding, computing allocations, positions, observing, service and teaching of Andreas W. Neitzel, with a two-page PDF.
lede: The full public record, section by section. The two-page academic CV has the same facts in print form.
---
{%- assign L = site.data.ledger -%}
<p class="no-print" style="display:flex;gap:8px;flex-wrap:wrap;margin-block:4px 8px">
  <a class="btn btn--primary" href="{{ '/assets/pdf/cv_neitzel_academic_summary.pdf' | relative_url }}"><svg class="i" aria-hidden="true"><use href="#i-download"/></svg>Academic CV, 2 pages (PDF)</a>
  <a class="btn" href="{{ '/publications/' | relative_url }}">Publications</a>
  <a class="btn" href="{{ '/talks/' | relative_url }}">Talks</a>
</p>
<div class="cv-grid section">
  {%- assign sections = "funding:Funding and computing allocations:full,education:Education:,positions:Positions:,events:Observing and schools:,awards:Awards:,memberships:Memberships:,service:Service:,teaching:Teaching and supervision:,outreach:Outreach:" | split: "," -%}
  {%- for s in sections %}
    {%- assign parts = s | split: ":" -%}
    {%- assign key = parts[0] -%}
    {%- assign items = L[key] -%}
    {%- if key == "events" %}{% assign items = L.events | where_exp: "e", "e.location != 'Remote'" %}{% endif -%}
    {%- if items and items.size > 0 %}
  <section class="{{ parts[2] }}" aria-labelledby="{{ key }}">
    <h2 id="{{ key }}">{{ parts[1] }}</h2>
    <ol class="entries">
      {%- for e in items %}{% include ledger_entry.html e=e category=key %}{% endfor %}
    </ol>
  </section>
    {%- endif %}
  {%- endfor %}
</div>
