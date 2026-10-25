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
<section class="section" aria-labelledby="try">
  <div class="section-head"><h2 id="try">Try in the browser</h2></div>
  <div class="mosaic">
    <a class="card wide" href="{{ '/playground/neural-network/' | relative_url }}" data-spotlight>
      <div class="media art">{% include figures/art-nn.svg %}</div>
      <div class="card-body"><span class="tag tag--software">Playground</span><h3>Train a neural network on <i>Gaia</i> spectra</h3><p>Real XP spectra of 4,000 stars; watch the network learn metallicity live.</p><span class="go">Open</span></div>
    </a>
    <a class="card" href="{{ '/software/starfold-demo/' | relative_url }}" data-spotlight>
      <div class="media art">{% include figures/art-clusters.svg %}</div>
      <div class="card-body"><span class="tag tag--software">Demo</span><h3>Starfold on a recorded run</h3><p>Inspect every point and replay the 32 refits.</p><span class="go">Open</span></div>
    </a>
    <a class="card" href="{{ '/stellar-explorer/' | relative_url }}" data-spotlight>
      <div class="media art">{% include figures/art-hr.svg %}</div>
      <div class="card-body"><span class="tag tag--software">App</span><h3>Stellar Explorer</h3><p>A star of the Sun's mass from birth to white dwarf, from a MESA and GYRE track.</p><span class="go">Open</span></div>
    </a>
    <a class="card" href="https://tellurion.dev/" data-spotlight>
      <div class="media art">{% include figures/art-orbit.svg %}</div>
      <div class="card-body"><span class="tag tag--software">Web</span><h3>Tellurion</h3><p>Nearly 400 interactive physics and astronomy simulations, from a double pendulum to colliding galaxies.</p><span class="go">Open tellurion.dev</span></div>
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
