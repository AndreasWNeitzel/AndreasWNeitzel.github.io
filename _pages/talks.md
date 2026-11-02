---
layout: default
permalink: /talks/
title: Talks and posters
copy: talks
---
{%- assign L = site.data.ledger -%}
{%- assign C = site.data.copy.talks -%}
{%- assign CP = site.data.copy.plates -%}
{%- assign tri = site.data.home.portals | where: "key", "talks" | first -%}
{%- assign intl = "TASC,KASC,IMAS,Iberian" | split: "," -%}
{%- capture intl_ids -%}{% for e in L.presentations %}{% for w in intl %}{% if e.venue contains w %}{{ e.id }},{% break %}{% endif %}{% endfor %}{% endfor %}{%- endcapture -%}
{%- assign cpo = site.data.copy.home.portals | where: "key", "talks" | first -%}
{% include plate.html tri=tri.images alts=cpo.alts alt="" title="Talks" line=CP.talks %}
<div class="wrap">
<section class="section section--tight" aria-labelledby="intl">
  <div class="section-head k-up"><h2 id="intl">{{ C.intl_title }}</h2><p>{{ C.intl_lead | missions }}</p></div>
  <ol class="entries">
    {%- for e in L.presentations %}{% if intl_ids contains e.id %}{% include ledger_entry.html e=e category="presentations" %}{% endif %}{% endfor %}
  </ol>
</section>
<section class="section" aria-labelledby="natl">
  <div class="section-head k-up"><h2 id="natl">{{ C.natl_title }}</h2></div>
  <ol class="entries">
    {%- for e in L.presentations %}{% unless intl_ids contains e.id %}{% include ledger_entry.html e=e category="presentations" %}{% endunless %}{% endfor %}
  </ol>
</section>
</div>
