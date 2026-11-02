---
layout: page
permalink: /software/
title: Software and demos
copy: software
extra_links:
  sw-2026-starfold:
    - {label: Interactive demo, url: /software/starfold-demo/}
    - {label: Held-out benchmark, url: /software/starfold-benchmark/}
codes:
  - {id: janus, title: JANUS, img: /assets/img/heroes/software_xp.webp, url: /research/janus/, go: "The method"}
  - {id: starfold, title: Starfold, img: /assets/img/heroes/software_chem.webp, url: /software/starfold-demo/, go: "Run it on 9,242 stars"}
  - {id: haydnsim, title: HAYDNsim, img: /assets/img/heroes/software_cluster.webp, url: /software/haydnsim/, go: "The pipeline"}
playgrounds:
  - {id: nn, art: nn, url: /playground/neural-network/}
  - {id: orbits, art: orbit, url: /playground/orbits/}
  - {id: gp, art: gp, url: /playground/gaussian-processes/}
  - {id: polytropes, art: polytrope, url: /playground/polytropes/}
demos:
  - {id: starfold-demo, art: clusters, url: /software/starfold-demo/, go: Open}
  - {id: stellar-explorer, art: hr, url: /stellar-explorer/, go: Open}
  - {id: haydnsim, img: /assets/img/heroes/software_cluster.webp, url: /software/haydnsim/, go: Read about it}
  - {id: tellurion, img: /assets/img/tellurion/blackhole-legend-3d.webp, url: /software/tellurion/, go: What it is}
---
{%- assign L = site.data.ledger -%}
{%- assign C = site.data.copy.software -%}
<section class="section section--tight" id="codes" aria-labelledby="codes-title">
  <div class="section-head k-up"><h2 id="codes-title">{{ C.codes_title }}</h2></div>
  <div class="mosaic">
    {%- for cd in page.codes %}{% assign c = C.codes | where: "id", cd.id | first %}
    <a class="card k-card" href="{{ cd.url | relative_url }}">
      <div class="media"><img src="{{ cd.img | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async"></div>
      <div class="card-body"><span class="kicker">{{ c.kicker | missions }}</span><h3>{{ cd.title }}</h3><p>{{ c.text | missions }}</p><span class="go">{{ cd.go }}</span></div>
    </a>
    {%- endfor %}
  </div>
</section>
<section class="section" id="playgrounds" aria-labelledby="pg">
  <div class="section-head k-up"><h2 id="pg">Playgrounds</h2><p>{{ C.playgrounds_lead | missions }}</p></div>
  <div class="mosaic mosaic--pairs">
    {%- for pg in page.playgrounds %}{% assign c = C.playgrounds | where: "id", pg.id | first %}
    <a class="card k-up" href="{{ pg.url | relative_url }}">
      <div class="media art">{% include figures/art-{{ pg.art }}.svg %}</div>
      <div class="card-body"><span class="tag tag--software">playground</span><h3>{{ c.title | missions }}</h3><p>{{ c.text | missions }}</p><span class="go">Open</span></div>
    </a>
    {%- endfor %}
  </div>
</section>
<section class="section" aria-labelledby="try">
  <div class="section-head k-up"><h2 id="try">Demos and apps</h2><p>{{ C.demos_lead | missions }}</p></div>
  <div class="mosaic mosaic--pairs">
    {%- for d in page.demos %}{% assign c = C.demos | where: "id", d.id | first %}
    <a class="card k-up" href="{{ d.url | relative_url }}">
      {%- if d.img %}<div class="media"><img src="{{ d.img | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async"></div>{% else %}<div class="media art">{% include figures/art-{{ d.art }}.svg %}</div>{% endif %}
      <div class="card-body"><span class="tag tag--software">{% if d.id == "tellurion" %}website{% elsif d.id == "haydnsim" %}pipeline{% elsif d.id == "stellar-explorer" %}app{% else %}demo{% endif %}</span><h3>{{ c.title | missions }}</h3><p>{{ c.text | missions }}</p><span class="go">{{ d.go }}</span></div>
    </a>
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
