---
layout: default
permalink: /observing/paranal/
title: Observing at the Very Large Telescope
nav_section: Research
description: My May 2024 visitor-mode observing run at ESO's Paranal Observatory, for an ESPRESSO campaign on the star GJ 570 A.
og_image: /assets/img/og-vlt.jpg
og_image_alt: Andreas W. Neitzel on the platform of ESO's Very Large Telescope at Paranal at sunset
extra_css: [/assets/css/observing.css]
math: true
---
<div class="wrap stack-l">
  <p class="crumbs story-crumbs"><a href="{{ '/research/' | relative_url }}">Research</a> · <a href="{{ '/papers/campante-2026-gj570a/' | relative_url }}">the paper this run produced</a></p>
  <section class="story-hero">
    <img src="{{ '/assets/img/photos/vlt-golden-hour.webp' | relative_url }}" alt="Andreas on the Very Large Telescope platform at Paranal at sunset, with the Unit Telescope enclosures behind him." fetchpriority="high">
    <div class="card-body stack-s">
      <p><span class="tag tag--observing">observing</span> <span class="kicker" style="color:rgb(255 255 255 / .8)">Paranal, Chile · May 2024</span></p>
      <h1>Observing at the Very Large Telescope</h1>
      <p>In May 2024 I was the visitor-mode observer for an ESPRESSO campaign on the star GJ 570 A, part of Tiago L. Campante's programme.</p>
    </div>
  </section>

  <section>
    <div class="prose">
      <h2>What I did</h2>
      <p>Visitor mode means travelling to the telescope and running the observations alongside ESO's staff. At Paranal I operated ESPRESSO on one of the 8.2 m Unit Telescopes and followed GJ 570 A through the nights, with Tiago Campante as principal investigator.</p>
      <h2>What the data showed</h2>
      <p>GJ 570 A, a small, cool star, oscillates with about a sixth of the Sun's strength. Together with a second star observed later in 2024, it shows that stars of this kind oscillate more weakly than expected, and computer simulations of their outer layers do not yet reproduce this. The results are in <a href="{{ '/papers/campante-2026-gj570a/' | relative_url }}">Campante et al. 2026, with a plain-language explainer here</a>.</p>
    </div>
  </section>
  <section>
    <figure class="panel blueprint wide-fig vlt-fig" id="light-path" data-build>
      <div class="vlt-row">
        {% include figures/vlt-lightpath.svg %}
        {% include figures/espresso-spectrum.svg %}
      </div>
    </figure>
  </section>

  <section>
    <div class="section-head"><h2>From the run</h2><p>Photographs from my May 2024 stay at Paranal.</p></div>
    <div class="gallery">
      <figure class="half"><img src="{{ '/assets/img/photos/ut-mirror-cell.webp' | relative_url }}" alt="The underside of a Unit Telescope's mirror cell and mount, seen from the dome floor." loading="lazy"><figcaption>The mount and mirror cell of a Unit Telescope, from the dome floor.</figcaption></figure>
      <figure class="tall"><img style="object-position: 50% 60%" src="{{ '/assets/img/photos/ut-dome-interior.webp' | relative_url }}" alt="Andreas standing beneath the mirror cell of a Unit Telescope inside its dome." loading="lazy"><figcaption>Under the mirror cell of an 8.2 m telescope.</figcaption></figure>
      <figure class="tall"><img style="object-position: 82% 55%" src="{{ '/assets/img/photos/paranal-milky-way.webp' | relative_url }}" alt="The Milky Way over Paranal before dawn." loading="lazy"><figcaption>The Milky Way before dawn.</figcaption></figure>
      <figure class="half"><img src="{{ '/assets/img/photos/atacama-sunset.webp' | relative_url }}" alt="Sunset over the Atacama desert and the Pacific cloud deck, seen from Paranal." loading="lazy"><figcaption>Sunset over the Atacama and the Pacific cloud deck.</figcaption></figure>
      <figure class="wide"><img src="{{ '/assets/img/photos/vlt-daylight.webp' | relative_url }}" alt="Andreas in a hard hat in front of a Unit Telescope enclosure in daylight." loading="lazy"><figcaption>On the platform in daylight.</figcaption></figure>
      <figure><img src="{{ '/assets/img/photos/vlt-golden-hour.webp' | relative_url }}" alt="Andreas on the VLT platform at sunset." loading="lazy"><figcaption>The platform at sunset, before the night's observing.</figcaption></figure>
    </div>
  </section>

  <p class="muted small">More context: <a href="{{ '/guide/eso-vlt/' | relative_url }}">what ESO and the VLT are</a>, and <a href="{{ '/guide/asteroseismology/' | relative_url }}">what asteroseismology measures</a>.</p>
</div>
