---
layout: default
permalink: /about/
title: About
description: Who Andreas W. Neitzel is, where the work has taken him, what he works with, and the full timeline of papers, talks, funding and computing.
lede: PhD researcher at IA and the University of Porto, working on machine learning for Galactic archaeology.
---
{%- assign p = site.data.person -%}
{%- assign L = site.data.ledger -%}
{%- assign H = site.data.home -%}
<div class="wrap">
<header class="about-id">
  <img class="about-portrait" src="{{ '/assets/img/photos/portrait-2026.webp' | relative_url }}" width="640" height="640" alt="Portrait of {{ p.name }}" fetchpriority="high">
  <div class="about-who">
    <p class="crumbs">About</p>
    <h1 class="name">{{ p.name | initials }}</h1>
    <p class="role">PhD researcher in astrophysics and machine learning · IA and the University of Porto</p>
    <dl class="about-facts-row">
      <div><dt>Based in</dt><dd>{{ p.location }}</dd></div>
      <div><dt>Citizenship</dt><dd>EU (Portugal, Germany)</dd></div>
      <div><dt>Languages</dt><dd>Portuguese, English (C2), German (A2), Spanish (A2)</dd></div>
      <div><dt>Email</dt><dd><a href="mailto:{{ p.emails.academic }}">{{ p.emails.academic }}</a></dd></div>
      <div><dt>ORCID</dt><dd><a href="https://orcid.org/{{ p.identifiers.orcid }}" rel="me">{{ p.identifiers.orcid }}</a></dd></div>
    </dl>
    <p class="cta"><a class="btn btn--primary" href="{{ '/assets/pdf/cv_neitzel_academic_summary.pdf' | relative_url }}"><svg class="i" aria-hidden="true"><use href="#i-download"/></svg>Academic CV (PDF)</a><a class="btn" href="{{ '/cv/' | relative_url }}">Full record</a></p>
  </div>
</header>
<section class="section about-bio" aria-label="Biography">
  <div class="prose">
    <p>I am a fourth-year PhD candidate at IA and the University of Porto, supervised by Tiago L. Campante, Diego Bossini and Andrea Miglio. My work chains neural networks on <i>Gaia</i> spectra, unsupervised population methods and asteroseismology from <i>TESS</i> and <i>Kepler</i>. I hold the FCT allocations on Deucalion and MareNostrum 5 as responsible investigator.</p>
    <p>Before the PhD I did the MSc in Astronomy and Astrophysics in Porto, with an <i>Ariel</i> dissertation, and the BSc in Physics. I spent six months of 2025 and 2026 at INAF-OAS Bologna writing HAYDNsim, the noise-simulation pipeline for the proposed <i>HAYDN</i> mission, and observed with ESPRESSO at the VLT in May 2024.</p>
    <p>{{ s.summary | default: s.tagline | missions }}</p>
    <p class="now"><span class="tag tag--now">now</span><span>{{ H.now }}</span></p>
  </div>
</section>
<section class="section" id="skills" aria-labelledby="skills-title">
  <div class="section-head"><h2 id="skills-title">What I work with</h2></div>
  <div class="skills">
    {%- assign icons = "skill-2026-ml-probabilistic-deep-learning:i-nn,skill-2026-uncertainty-calibration:i-gauge,skill-2026-data-engineering-at-scale:i-db,skill-2026-hpc:i-cpu,skill-2026-python-engineering:i-code,skill-2026-astronomy-data:i-telescope,skill-2026-web-visualisation:i-chart" | split: "," -%}
    {%- for s in L.skills %}
      {%- assign icon = "i-star" -%}
      {%- for pair in icons %}{% assign kv = pair | split: ":" %}{% if kv[0] == s.id %}{% assign icon = kv[1] %}{% endif %}{% endfor -%}
    <article class="skill card">
      <h3><svg class="i" aria-hidden="true"><use href="#{{ icon }}"/></svg>{{ s.title }}</h3>
      <p>{{ s.summary | default: s.tagline | missions }}</p>
    </article>
    {%- endfor %}
  </div>
</section>
<section class="section" id="photos" aria-labelledby="photos-title">
  <div class="section-head"><h2 id="photos-title">In the field</h2><p>My photographs from Paranal and the conference hall.</p></div>
  <ul class="evidence" aria-label="Photographs">
    {%- for ph in H.evidence %}
    <li><a href="{{ ph.url | relative_url }}"><img src="{{ ph.src | relative_url }}" alt="{{ ph.alt }}" loading="lazy" decoding="async"><span>{{ ph.caption }}</span></a></li>
    {%- endfor %}
  </ul>
</section>


<section class="section" id="all" aria-labelledby="all-title">
  <div class="section-head">
    <h2 id="all-title">Everything, by date</h2>
    <p>Papers, talks, funding, computing, observing, software and service from the public record.</p>
  </div>
  {% include timeline.html %}
</section>
</div>
