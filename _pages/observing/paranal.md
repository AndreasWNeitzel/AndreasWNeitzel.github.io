---
layout: default
permalink: /observing/paranal/
title: Observing at the Very Large Telescope
nav_section: Research
description: Why ESPRESSO at ESO's Paranal Observatory was pointed at the K dwarf GJ 570 A in May 2024, what I did as the visiting observer, and what the data showed.
og_image: /assets/img/og-vlt.jpg
og_image_alt: Andreas W. Neitzel on the platform of ESO's Very Large Telescope at Paranal at sunset
extra_css: [/assets/css/observing.css]
math: true
---
<div class="wrap stack-l">
  <p class="crumbs story-crumbs"><a href="{{ '/research/' | relative_url }}">Research</a> · <a href="{{ '/papers/campante-2026-gj570a/' | relative_url }}">the paper this run produced</a></p>
  <section class="story-hero">
    <img src="{{ '/assets/img/photos/vlt-golden-hour.webp' | relative_url }}" alt="Andreas on the Very Large Telescope platform at Paranal at sunset, with the Unit Telescope enclosures behind him." fetchpriority="high" style="object-position: 50% 100%">
    <div class="card-body stack-s">
      <p><span class="tag tag--observing">observing</span> <span class="kicker" style="color:rgb(255 255 255 / .8)">Paranal, Chile · May 2024</span></p>
      <h1>Observing at the Very Large Telescope</h1>
      <p>In May 2024 I was the visiting observer at Paranal for an ESPRESSO campaign on the star GJ 570 A, part of Tiago L. Campante's programme, to measure oscillations in a cool dwarf star.</p>
    </div>
  </section>

  <section>
    <div class="story-cols">
      <div class="prose">
        <h2>What the campaign was for</h2>
      <p>Stars oscillate. Gas churning below the surface drives sound waves through the interior, and the pitches of the tones reveal a star's mass, radius and age. This is asteroseismology. In stars like the Sun it is routine, but in K dwarfs, which are smaller and cooler, the surface moves by only a few centimetres per second, and space telescopes that watch brightness have caught the effect in very few of them.</p>
      <p>A spectrograph can look for the same oscillation as a Doppler shift, the surface moving towards and away from us. ESPRESSO, on the Very Large Telescope, is stable enough to see shifts that small. GJ 570 A is a nearby K dwarf bright enough for 25-second exposures. How strongly such a star oscillates tests our models of convection, and it tells the PLATO mission what it can expect from stars of this kind.</p>
      </div>
      <div class="prose">
        <h2>What I did</h2>
      <p>Visitor mode means the observer travels to the telescope and runs the observations on site, alongside ESO's staff. The programme was Tiago Campante's, and I was the observer at Paranal for GJ 570 A, from 4 May 2024, with six scheduled nights from 6 to 12 May.</p>
      <p>Each night the aim was a continuous series of short exposures of one star, about one a minute, so that the oscillations could be followed without gaps. Wind and cloud kept the dome closed on the first night and for half of the fourth, so the series that went into the analysis comes from the remaining nights.</p>
      </div>
      <div class="prose">
        <h2>What came of it</h2>
      <p>GJ 570 A does oscillate, with periods of three to four minutes, but at only about a sixth of the Sun's strength. Together with a second K dwarf observed in September 2024, it shows that small, cool stars oscillate more weakly than the rule for Sun-like stars predicts, and current 3D simulations of their outer layers do not reproduce the drop.</p>
      <p>The results are in Campante et al. 2026, published in <i>Astronomy and Astrophysics</i>, where I am sixth of 24 authors and credited with the GJ 570 A observations. <a href="{{ '/papers/campante-2026-gj570a/' | relative_url }}">The plain-language explainer is here</a>.</p>
      </div>
    </div>
  </section>
  <section>
    <figure class="panel blueprint wide-fig vlt-fig" id="light-path" data-build data-credit="own">
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
      <figure class="tall"><img style="object-position: 50% 60%" src="{{ '/assets/img/photos/ut-under-mirror-cell.webp' | relative_url }}" alt="Andreas standing beneath the mirror cell of a Unit Telescope inside its dome." loading="lazy"><figcaption>Under the mirror cell of an 8.2 m telescope.</figcaption></figure>
      <figure class="tall"><img style="object-position: 82% 55%" src="{{ '/assets/img/photos/paranal-milky-way.webp' | relative_url }}" alt="The Milky Way over Paranal before dawn." loading="lazy"><figcaption>The Milky Way before dawn.</figcaption></figure>
      <figure class="half"><img src="{{ '/assets/img/photos/atacama-sunset.webp' | relative_url }}" alt="Sunset over the Atacama desert and the Pacific cloud deck, seen from Paranal." loading="lazy"><figcaption>Sunset over the Atacama and the Pacific cloud deck.</figcaption></figure>
      <figure class="wide"><img src="{{ '/assets/img/photos/vlt-daylight.webp' | relative_url }}" alt="Andreas in a hard hat in front of a Unit Telescope enclosure in daylight." loading="lazy"><figcaption>On the platform in daylight.</figcaption></figure>
      <figure><img src="{{ '/assets/img/photos/vlt-golden-hour.webp' | relative_url }}" alt="Andreas on the VLT platform at sunset." loading="lazy"><figcaption>The platform at sunset, before the night's observing.</figcaption></figure>
    </div>
  </section>

  <p class="muted small">More context: <a href="{{ '/guide/eso-vlt/' | relative_url }}">what ESO and the VLT are</a>, and <a href="{{ '/guide/asteroseismology/' | relative_url }}">what asteroseismology measures</a>.</p>
</div>
