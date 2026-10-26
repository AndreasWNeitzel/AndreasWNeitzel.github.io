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
<div class="talks-layout">
  <div class="talks-main">
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
  </div>
  <aside class="talks-photos" aria-label="Photographs from talks">
    <figure class="figure"><img src="{{ '/assets/img/photos/aarhus-2026-janus-talk.webp' | relative_url }}" alt="Andreas at the lectern in an Aarhus University auditorium, presenting a slide on which stellar abundances JANUS measures, with the audience in the foreground." loading="lazy" decoding="async" style="object-position: 30% 50%"><figcaption>JANUS talk at TASC10/KASC17, Aarhus University, July 2026.</figcaption></figure>
    <figure class="figure"><img src="{{ '/assets/img/photos/tasc8-kasc15-talk.webp' | relative_url }}" alt="Andreas presenting with a microphone in a Faculty of Sciences auditorium, with the Portuguese and EU flags behind him." loading="lazy" decoding="async" style="object-position: 58% 40%"><figcaption>TASC8/KASC15 workshop, Faculty of Sciences, University of Porto, July 2024.</figcaption></figure>
    <figure class="figure"><img src="{{ '/assets/img/photos/dfa-week-2026-title.webp' | relative_url }}" alt="Andreas giving his talk on photometric simulations of dense star clusters for HAYDN at DFA Week 2026, with the title slide on screen." loading="lazy" decoding="async" style="object-position: 70% 50%"><figcaption>Photometric simulations of dense star clusters for the proposed <i>HAYDN</i> mission, DFA Week 2026, Porto.</figcaption></figure>
  </aside>
</div>
