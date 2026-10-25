---
layout: page
permalink: /software/
title: Software
description: Research software by Andreas W. Neitzel, with status, licence, version and an honest benchmark.
lede: Research software I write and maintain, with status, licence and version where they are recorded.
extra_links:
  sw-2026-starfold:
    - {label: Held-out benchmark, url: /software/starfold-benchmark/}
---
{%- assign L = site.data.ledger -%}
<section class="row" aria-labelledby="packages">
  <h2 id="packages">Packages and applications</h2>
  <ol class="entries">
    {%- for e in L.software %}
    {%- if e.kind == "docs" %}{% continue %}{% endif %}
    {%- assign extra = page.extra_links[e.id] -%}
    {%- include ledger_entry.html e=e category="software" extra=extra %}
    {%- endfor %}
  </ol>
</section>
