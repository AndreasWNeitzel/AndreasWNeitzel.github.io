---
layout: page
permalink: /software/
title: Software
description: Research software by Andreas W. Neitzel, with status, licence and version, and the Starfold benchmark.
lede: Research software I write and maintain, with status, licence and version where recorded.
extra_links:
  sw-2026-starfold:
    - {label: Interactive demo, url: /software/starfold-demo/}
    - {label: Held-out benchmark, url: /software/starfold-benchmark/}
---
{%- assign L = site.data.ledger -%}
<section class="row" aria-labelledby="packages">
  <h2 id="packages">Packages and applications</h2>
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
