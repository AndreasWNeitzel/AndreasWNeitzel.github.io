---
layout: default
permalink: /about/
title: About
copy: about
---
{%- assign p = site.data.person -%}
{%- assign L = site.data.ledger -%}
{%- assign C = site.data.copy.about -%}
{%- assign H = site.data.home -%}
<div class="wrap">
<section class="id" aria-label="Who I am">
  <div class="ph k-scale"><img src="{{ '/assets/img/heroes/headshot_800.webp' | relative_url }}" srcset="{{ '/assets/img/heroes/headshot_800.webp' | relative_url }} 800w, {{ '/assets/img/heroes/headshot_1200.webp' | relative_url }} 1200w" sizes="(max-width: 860px) 360px, 440px" width="800" height="1000" alt="Portrait of {{ p.name }}" fetchpriority="high"></div>
  <div class="k-up">
    <h1>{{ p.given_names | initials }}<br>{{ p.family_name }}</h1>
    <p class="role">{{ C.role }}</p>
    <p class="bio">{{ C.bio }}</p>
    <p class="facts"><span><b>Based in</b> {{ C.facts.based }}</span><span><b>Citizenship</b> {{ C.facts.citizenship }}</span><span><b>Languages</b> {{ C.facts.languages }}</span></p>
    {% include links.html %}
    <p class="cta"><a class="btn btn--primary" href="{{ '/assets/pdf/cv_neitzel_academic_summary.pdf' | relative_url }}"><svg class="i" aria-hidden="true"><use href="#i-download"/></svg>Academic CV (PDF)</a><a class="btn" href="{{ '/cv/' | relative_url }}">Full record</a></p>
  </div>
</section>
</div>

<section class="section tone-alt" id="field" aria-labelledby="field-title">
  <div class="wrap">
    <div class="section-head k-up"><h2 id="field-title">In the field</h2></div>
    <div class="strip">
      {%- for ph in H.strip %}{% assign cap = C.strip | where: "key", ph.key | first %}
      <figure class="k-scale"><img src="{{ ph.src | relative_url }}" alt="{{ cap.caption }}" loading="lazy" decoding="async"{% if ph.pos %} style="object-position: {{ ph.pos }}"{% endif %}><figcaption>{{ cap.caption | missions }}</figcaption></figure>
      {%- endfor %}
    </div>
  </div>
</section>

<section class="section" id="skills" aria-labelledby="skills-title">
  <div class="wrap">
    <div class="section-head k-up"><h2 id="skills-title">{{ C.skills_title }}</h2></div>
    <div class="skills">
      {%- assign icons = "skill-2026-ml-probabilistic-deep-learning:i-nn,skill-2026-uncertainty-calibration:i-gauge,skill-2026-data-engineering-at-scale:i-db,skill-2026-hpc:i-cpu,skill-2026-python-engineering:i-code,skill-2026-astronomy-data:i-telescope,skill-2026-web-visualisation:i-chart" | split: "," -%}
      {%- for s in L.skills %}
        {%- assign icon = "i-star" -%}
        {%- for pair in icons %}{% assign kv = pair | split: ":" %}{% if kv[0] == s.id %}{% assign icon = kv[1] %}{% endif %}{% endfor -%}
      <article class="skill card k-up">
        <h3><svg class="i" aria-hidden="true"><use href="#{{ icon }}"/></svg>{{ s.title }}</h3>
        <p>{{ s.summary | default: s.tagline | missions }}</p>
      </article>
      {%- endfor %}
    </div>
  </div>
</section>

<section class="section tone-alt" id="record" aria-labelledby="record-title">
  <div class="wrap">
    <div class="section-head k-up"><h2 id="record-title">{{ C.record_title }}</h2></div>
    {% include timeline.html %}
  </div>
</section>
