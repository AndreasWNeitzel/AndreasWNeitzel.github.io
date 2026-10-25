---
layout: page
permalink: /talks/
title: Talks and posters
description: Conference talks and posters by Andreas W. Neitzel, international and national, with Zenodo DOIs for slides and posters.
lede: Talks and posters since 2022, international meetings first, with slides and posters on Zenodo where deposited.
---
{%- assign L = site.data.ledger -%}
{%- assign intl = "TASC,KASC,IMAS,Iberian" | split: "," -%}
{%- capture intl_ids -%}{% for e in L.presentations %}{% for w in intl %}{% if e.venue contains w %}{{ e.id }},{% break %}{% endif %}{% endfor %}{% endfor %}{%- endcapture -%}
<figure class="figure" style="margin-block:8px 0">
  <img src="{{ '/assets/img/photos/dfa-week-2026-title.webp' | relative_url }}" alt="Andreas giving his talk on photometric simulations of dense star clusters for HAYDN at DFA Week 2026, with the title slide on screen." style="max-block-size:420px;object-fit:cover">
  <figcaption>Presenting photometric simulations of dense star clusters for the proposed <i>HAYDN</i> mission, DFA Week 2026, Porto.</figcaption>
</figure>
<section class="section" aria-labelledby="intl">
  <div class="section-head"><h2 id="intl">International</h2><p>TESS and Kepler asteroseismology workshops (TASC/KASC) and the Iberian Meetings on Asteroseismology (IMAS).</p></div>
  <ol class="entries">
    {%- for e in L.presentations %}{% if intl_ids contains e.id %}{% include ledger_entry.html e=e category="presentations" %}{% endif %}{% endfor %}
  </ol>
</section>
<section class="section" aria-labelledby="natl">
  <div class="section-head"><h2 id="natl">National and institutional</h2></div>
  <ol class="entries">
    {%- for e in L.presentations %}{% unless intl_ids contains e.id %}{% include ledger_entry.html e=e category="presentations" %}{% endunless %}{% endfor %}
  </ol>
</section>
