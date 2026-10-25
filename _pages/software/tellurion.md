---
layout: page
permalink: /software/tellurion/
title: Tellurion
nav_section: Software
crumb: {label: Software, url: /software/}
description: Tellurion is a separate, free website of interactive physics and astronomy simulations, written by Andreas W. Neitzel as a teaching resource.
lede: A separate website of mine, with free interactive physics and astronomy simulations that I wrote as a teaching resource during my PhD.
---
{%- assign t = site.data.ledger.software | where: "id", "sw-2026-05-tellurion" | first -%}
<section class="tl-top" aria-label="What Tellurion is">
  <figure class="tl-hero">
    <a href="https://tellurion.dev/playgrounds/_legends/blackhole-legend-3d/"><img src="{{ '/assets/img/tellurion/ui-blackhole-legend-3d.webp' | relative_url }}" width="1440" height="900" decoding="async"
      alt="The black-hole page of Tellurion: a lensed accretion disc around the shadow of a black hole, with the photon sphere and the innermost stable orbit marked, and controls and live readouts on the right."></a>
    <figcaption class="credit">An example page, the black-hole simulation, as it runs on tellurion.dev.</figcaption>
  </figure>
  <div class="tl-about">
    <p>A tellurion is the eighteenth-century brass model that shows how the Earth, the Moon and the Sun move together, an instrument you learn from by turning it. The website applies that idea to physics courses: each page is one simulation you drive yourself, with live readouts and the textbook it follows.</p>
    <p>{{ t.summary }}</p>
    <dl class="tl-facts">
      <div><dt>Built with</dt><dd>{{ t.details[0] }}</dd></div>
      <div><dt>Tested by</dt><dd>{{ t.details[1] }}</dd></div>
      <div><dt>Courses</dt><dd>{{ t.details[2] }}</dd></div>
      <div><dt>Licence</dt><dd>{{ t.licence }}</dd></div>
    </dl>
    <p class="tl-cta"><a class="btn btn--primary" href="{{ t.identifiers.url }}">Go to tellurion.dev</a> <a class="btn" href="{{ t.identifiers.repo }}">Source on GitHub</a></p>
  </div>
</section>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Tellurion",
  "url": "{{ t.identifiers.url }}",
  "applicationCategory": "EducationalApplication",
  "operatingSystem": "Any (web browser)",
  "isAccessibleForFree": true,
  "license": "https://opensource.org/licenses/MIT",
  "author": {"@id": "{{ site.url }}/#person"},
  "sameAs": ["{{ t.identifiers.repo }}"]
}
</script>
