---
layout: default
permalink: /software/
title: Software and demos
copy: software
extra_links:
  sw-2026-starfold:
    - {label: Interactive demo, url: /software/starfold-demo/}
    - {label: Held-out benchmark, url: /software/starfold-benchmark/}
codes:
  - {id: janus, title: JANUS, loop: ai, img: /assets/img/heroes/line_janus.webp, url: /research/janus/, links: [{label: "The method", url: /research/janus/}, {label: "The talks", url: /talks/}]}
  - {id: starfold, title: Starfold, loop: starfold, img: /assets/img/heroes/software_starfold.webp, url: /software/starfold-demo/, links: [{label: "Run it on 9,242 stars", url: /software/starfold-demo/}, {label: "The held-out benchmark", url: /software/starfold-benchmark/}, {label: "Source code", url: "https://github.com/AndreasWNeitzel/starfold"}]}
  - {id: haydnsim, title: HAYDNsim, loop: haydn, img: /assets/img/heroes/software_haydn.webp, url: /software/haydnsim/, links: [{label: "The pipeline", url: /software/haydnsim/}, {label: "What is HAYDN?", url: /guide/haydn/}]}
playgrounds:
  - {id: nn, art: nn, img: /assets/img/heroes/card_nn.webp, url: /playground/neural-network/}
  - {id: orbits, art: orbit, img: /assets/img/heroes/card_orbits.webp, url: /playground/orbits/}
  - {id: gp, art: gp, img: /assets/img/heroes/card_gp.webp, url: /playground/gaussian-processes/}
  - {id: polytropes, art: polytrope, img: /assets/img/heroes/card_polytrope.webp, url: /playground/polytropes/}
demos:
  - {id: starfold-demo, img: /assets/img/heroes/software_starfold.webp, url: /software/starfold-demo/}
  - {id: stellar-explorer, art: hr, img: /assets/img/heroes/card_explorer.webp, url: /stellar-explorer/}
  - {id: tellurion, img: /assets/img/tellurion/blackhole-legend-3d.webp, url: /software/tellurion/}
---
{%- assign L = site.data.ledger -%}
{%- assign C = site.data.copy.software -%}
{%- assign CP = site.data.copy.plates -%}
{% include plate.html stage=true loop="softhead" still="/assets/img/heroes/softhead.poster.webp" alt=site.data.copy.software.header_alt title="Software" line=CP.software loop_start="11" %}
<div class="wrap">
<section class="section section--tight" id="codes" aria-labelledby="codes-title">
  <div class="section-head k-up"><h2 id="codes-title">{{ C.codes_title }}</h2></div>
  <div class="rows rows--same">
    {%- for cd in page.codes %}{% assign c = C.codes | where: "id", cd.id | first %}
    <article class="row-item k-up">
      <div class="pic">
        {%- assign vpath = "/assets/video/" | append: cd.loop | append: ".av1.mp4" -%}{%- assign vf = site.static_files | where: "path", vpath | first -%}
        {%- if vf %}{% include loop.html name=cd.loop alt="" %}{% else %}<img src="{{ cd.img | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async">{% endif %}
      </div>
      <div class="words">
        <span class="kicker">{{ c.kicker | missions }}</span>
        <h2><a href="{{ cd.url | relative_url }}">{{ cd.title }}</a></h2>
        <p>{{ c.text | missions }}</p>
        <p class="textlinks">{% for l in cd.links %}<a href="{{ l.url | relative_url }}">{{ l.label | missions }}</a>{% endfor %}</p>
      </div>
    </article>
    {%- endfor %}
  </div>
</section>
<section class="section" id="playgrounds" aria-labelledby="pg">
  <div class="section-head k-up"><h2 id="pg">Playgrounds</h2><p>{{ C.playgrounds_lead | missions }}</p></div>
  <div class="explainers">
    {%- for pg in page.playgrounds %}{% assign c = C.playgrounds | where: "id", pg.id | first %}
    <a class="explainer k-up" href="{{ pg.url | relative_url }}">
      {%- if pg.img %}<div class="pic"><img src="{{ pg.img | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async"></div>{% else %}<div class="pic art">{% include figures/art-{{ pg.art }}.svg %}</div>{% endif %}
      <h3>{{ c.title | missions }}</h3><p>{{ c.text | missions }}</p>
    </a>
    {%- endfor %}
  </div>
</section>
<section class="section" aria-labelledby="try">
  <div class="section-head k-up"><h2 id="try">Demos and apps</h2><p>{{ C.demos_lead | missions }}</p></div>
  <div class="explainers">
    {%- for d in page.demos %}{% assign c = C.demos | where: "id", d.id | first %}
    <a class="explainer k-up" href="{{ d.url | relative_url }}">
      {%- if d.img %}<div class="pic"><img src="{{ d.img | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async"></div>{% else %}<div class="pic art">{% include figures/art-{{ d.art }}.svg %}</div>{% endif %}
      <h3>{{ c.title | missions }}</h3><p>{{ c.text | missions }}</p>
    </a>
    {%- endfor %}
  </div>
</section>
<section class="section" id="tools" aria-labelledby="tools-title">
  <div class="section-head k-up"><h2 id="tools-title">{{ C.tools_title }}</h2><p>{{ C.tools_lead | missions }}</p></div>
  <div class="rows rows--same">
    {%- for t in site.data.tools %}
    {%- assign vpath = "/assets/video/" | append: t.loop | append: ".av1.mp4" -%}{%- assign vf = site.static_files | where: "path", vpath | first -%}
    {%- unless vf %}{% continue %}{% endunless %}
    {%- assign turl = "/software/tools/" | append: t.id | append: "/" %}
    <article class="row-item k-up">
      <div class="pic">{% include loop.html name=t.loop alt="" pos=t.pos %}</div>
      <div class="words">
        <span class="kicker">{{ t.kicker | missions }}</span>
        <h2><a href="{{ turl | relative_url }}">{{ t.title }}</a></h2>
        <p class="by">By {{ t.credit | initials }}</p>
        <p>{{ t.card | missions }}</p>
        <p class="textlinks"><a href="{{ turl | relative_url }}">How I used it</a>{% for l in t.links %}<a href="{{ l.url }}">{{ l.label | missions }}</a>{% endfor %}</p>
      </div>
    </article>
    {%- endfor %}
  </div>
</section>
<section class="section" aria-labelledby="packages">
  <div class="section-head k-up"><h2 id="packages">{{ C.packages_title }}</h2></div>
  <ol class="entries">
    {%- for e in L.software %}
    {%- if e.kind == "docs" %}{% continue %}{% endif %}
    {%- assign extra = page.extra_links[e.id] -%}
    {%- include ledger_entry.html e=e category="software" extra=extra %}
    {%- endfor %}
  </ol>
</section>
</div>
{%- assign sf = L.software | where: "id", "sw-2026-starfold" | first %}
{%- if sf %}
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareSourceCode",
  "name": "Starfold",
  "codeRepository": "{{ sf.identifiers.repo }}",
  "programmingLanguage": "Python",
  "license": "https://opensource.org/licenses/MIT",
  "version": "{{ sf.version }}",
  "author": {"@id": "{{ site.url }}/#person"},
  "url": "{{ site.url }}/software/"
}
</script>
{%- endif %}
