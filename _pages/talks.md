---
layout: page
permalink: /talks/
title: Talks and posters
copy: talks
---
{%- assign L = site.data.ledger -%}
{%- assign C = site.data.copy.talks -%}
{%- assign intl = "TASC,KASC,IMAS,Iberian" | split: "," -%}
{%- capture intl_ids -%}{% for e in L.presentations %}{% for w in intl %}{% if e.venue contains w %}{{ e.id }},{% break %}{% endif %}{% endfor %}{% endfor %}{%- endcapture -%}
<div class="talks-layout">
  <div class="talks-main">
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
  <aside class="talks-photos" aria-label="Photographs from talks">
    <figure class="k-scale"><img src="{{ '/assets/img/heroes/talk_aarhus.webp' | relative_url }}" alt="{{ site.data.copy.home.portals[2].alts[0] }}" loading="lazy" decoding="async" style="object-position: 30% 55%"><figcaption>{{ C.photos[0] | missions }}</figcaption></figure>
    <figure class="k-scale"><img src="{{ '/assets/img/heroes/hero_1000.webp' | relative_url }}" alt="{{ site.data.copy.home.photo_alt }}" loading="lazy" decoding="async" style="object-position: 70% 40%"><figcaption>{{ C.photos[1] | missions }}</figcaption></figure>
    <figure class="k-scale"><img src="{{ '/assets/img/heroes/talk_dfa_wide.webp' | relative_url }}" alt="{{ site.data.copy.home.portals[2].alts[2] }}" loading="lazy" decoding="async" style="object-position: 80% 50%"><figcaption>{{ C.photos[2] | missions }}</figcaption></figure>
  </aside>
</div>
