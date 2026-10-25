---
layout: page
permalink: /cv/
title: Curriculum vitae
description: Education, positions, funding, awards, service and teaching of Andreas W. Neitzel, with a two-page PDF.
---
{%- assign L = site.data.ledger -%}
<div class="row">
  <p class="no-print"><a class="button" href="{{ '/assets/pdf/cv_neitzel_academic_summary.pdf' | relative_url }}">Download the academic CV (PDF)</a></p>
  <p class="prose no-print">The sections below give the same record.</p>
</div>
{%- assign sections = "education:Education,positions:Positions,funding:Funding,awards:Awards,service:Service,teaching:Teaching and supervision,outreach:Outreach,memberships:Memberships" | split: "," -%}
{%- for s in sections %}
  {%- assign parts = s | split: ":" -%}
  {%- assign key = parts[0] -%}
  {%- assign items = L[key] -%}
  {%- if items and items.size > 0 %}
<section class="row" aria-labelledby="{{ key }}">
  <h2 id="{{ key }}">{{ parts[1] }}</h2>
  <ol class="entries">
    {%- for e in items %}
    {%- include ledger_entry.html e=e category=key details=true %}
    {%- endfor %}
  </ol>
</section>
  {%- endif %}
{%- endfor %}
