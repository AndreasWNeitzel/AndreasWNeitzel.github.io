---
layout: page
permalink: /guide/
title: Field guide
nav_section: Research
crumb: {label: Research, url: /research/}
description: Short explainers of the science, institutions and machines behind my work, from Galactic archaeology to the supercomputers I run on.
lede: The science, institutions and machines behind my work, one minute each, with sources and the parts I was involved in.
---
<div class="guide-grid">
  {%- assign gs = site.guide | sort: "order" -%}
  {%- for g in gs %}
  <a class="card" href="{{ g.url | relative_url }}" data-spotlight>
    <div class="media">{% if g.image and g.image != "" %}<img src="{{ g.image | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async">{% elsif g.photo %}<img src="{{ g.photo | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async">{% else %}<img src="{{ '/assets/img/photos/vlt-golden-hour.webp' | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async">{% endif %}</div>
    <div class="card-body">
      <h3>{{ g.title | missions }}</h3>
      <p>{{ g.lede | missions }}</p>
      <span class="go">Read</span>
    </div>
  </a>
  {%- endfor %}
</div>
