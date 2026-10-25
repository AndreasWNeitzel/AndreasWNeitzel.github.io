---
layout: page
permalink: /talks/
title: Talks
description: Conference talks and posters by Andreas W. Neitzel, with Zenodo DOIs where deposited.
lede: Talks and posters, most recent first. Slides and posters deposited on Zenodo are linked by DOI.
---
{%- assign L = site.data.ledger -%}
<section class="row" aria-labelledby="talklist">
  <h2 id="talklist">Talks and posters</h2>
  <ol class="entries">
    {%- for e in L.presentations %}
    {%- include ledger_entry.html e=e category="presentations" %}
    {%- endfor %}
  </ol>
</section>
