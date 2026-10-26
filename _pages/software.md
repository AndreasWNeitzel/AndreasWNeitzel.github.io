---
layout: page
permalink: /software/
title: Software and demos
description: Research software, browser apps and interactive demos by Andreas W. Neitzel, with status, licence and version.
lede: Research software and browser apps I wrote, each with what it does, its status, and a way to try it.
extra_links:
  sw-2026-starfold:
    - {label: Interactive demo, url: /software/starfold-demo/}
    - {label: Held-out benchmark, url: /software/starfold-benchmark/}
---
{%- assign L = site.data.ledger -%}
<section class="section" id="playgrounds" aria-labelledby="pg">
  <div class="section-head"><h2 id="pg">Playgrounds</h2><p>Methods from my coursework and research, rebuilt to run in the browser on real data.</p></div>
  <div class="mosaic mosaic--pairs">
    <a class="card" href="{{ '/playground/neural-network/' | relative_url }}" data-spotlight>
      <div class="media art">{% include figures/art-nn.svg %}</div>
      <div class="card-body"><span class="tag tag--software">playground</span><h3>Train a neural network on <i>Gaia</i> spectra</h3><p>Real XP spectra of 4,000 stars; watch the network learn metallicity live.</p><span class="go">Open</span></div>
    </a>
    <a class="card" href="{{ '/playground/orbits/' | relative_url }}" data-spotlight>
      <div class="media art">{% include figures/art-orbit.svg %}</div>
      <div class="card-body"><span class="tag tag--software">playground</span><h3>Orbits, from satellites to the Milky Way</h3><p>Leapfrog against Runge-Kutta and Euler around the Earth, then six <i>Gaia</i> stars through the Galaxy.</p><span class="go">Open</span></div>
    </a>
    <a class="card" href="{{ '/playground/polytropes/' | relative_url }}" data-spotlight>
      <div class="media art">{% include figures/art-polytrope.svg %}</div>
      <div class="card-body"><span class="tag tag--software">playground</span><h3>Build a star</h3><p>Solve the Lane-Emden equation, scale it to a real star and see where a polytrope stops describing one.</p><span class="go">Open</span></div>
    </a>
  </div>
</section>
<section class="section" aria-labelledby="try">
  <div class="section-head"><h2 id="try">Demos and apps</h2></div>
  <div class="mosaic mosaic--pairs">
    <a class="card" href="{{ '/software/starfold-demo/' | relative_url }}" data-spotlight>
      <div class="media art">{% include figures/art-clusters.svg %}</div>
      <div class="card-body"><span class="tag tag--software">demo</span><h3>Starfold on 9,242 Milky Way stars</h3><p>APOGEE chemistry and <i>Gaia</i> orbits: inspect any star and replay the 32 refits.</p><span class="go">Open</span></div>
    </a>
    <a class="card" href="{{ '/stellar-explorer/' | relative_url }}" data-spotlight>
      <div class="media art">{% include figures/art-hr.svg %}</div>
      <div class="card-body"><span class="tag tag--software">app</span><h3>Stellar Explorer</h3><p>A star of the Sun's mass from birth to white dwarf, from a MESA and GYRE track.</p><span class="go">Open</span></div>
    </a>
    <a class="card" href="{{ '/software/haydnsim/' | relative_url }}" data-spotlight>
      <div class="media"><img src="{{ '/assets/img/guide/haydn.webp' | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async"></div>
      <div class="card-body"><span class="tag tag--software">pipeline</span><h3>HAYDNsim</h3><p>Synthetic crowded clusters and per-star noise forecasts for the proposed <i>HAYDN</i> mission.</p><span class="go">Read about it</span></div>
    </a>
    <a class="card" href="{{ '/software/tellurion/' | relative_url }}" data-spotlight>
      <div class="media"><img src="{{ '/assets/img/tellurion/blackhole-legend-3d.webp' | relative_url }}" alt="" role="presentation" loading="lazy" decoding="async" width="800" height="500"></div>
      <div class="card-body"><span class="tag tag--software">website</span><h3>Tellurion</h3><p>My separate website of interactive physics and astronomy simulations, written as a teaching resource.</p><span class="go">What it is</span></div>
    </a>
  </div>
</section>
<section class="section" aria-labelledby="packages">
  <div class="section-head"><h2 id="packages">Packages and applications</h2></div>
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
