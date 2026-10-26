---
layout: default
permalink: /observing/paranal/
title: Observing at the Very Large Telescope
nav_section: Publications
description: My May 2024 visitor-mode run with ESPRESSO at ESO's Very Large Telescope at Paranal, on the K dwarf GJ 570 A, and what the data showed.
og_image: /assets/img/og-vlt.jpg
extra_css: [/assets/css/observing.css]
---
<div class="wrap stack-l">
  <p class="crumbs story-crumbs"><a href="{{ '/publications/' | relative_url }}">Publications</a> · <a href="{{ '/papers/campante-2026-gj570a/' | relative_url }}">the paper this run produced</a></p>
  <section class="story-hero">
    <img src="{{ '/assets/img/photos/vlt-golden-hour.webp' | relative_url }}" alt="Andreas on the Very Large Telescope platform at Paranal at sunset, with the Unit Telescope enclosures behind him." fetchpriority="high">
    <div class="card-body stack-s">
      <p><span class="tag tag--observing">observing</span> <span class="kicker" style="color:rgb(255 255 255 / .8)">Paranal, Chile · 4 to 12 May 2024</span></p>
      <h1>Observing at the Very Large Telescope</h1>
      <p>In May 2024 I spent nine days at ESO's Paranal Observatory in the Atacama desert and ran a campaign with the ESPRESSO spectrograph on the nearby star GJ 570 A. It was Tiago Campante's programme; I was the astronomer on site.</p>
    </div>
  </section>

  <section class="facts-grid" aria-label="Run facts">
    <div class="fact card"><b>6 to 12 May 2024</b><span>six visitor-mode nights, ESO run 113.26FX.002</span></div>
    <div class="fact card"><b>ESPRESSO</b><span>on one 8.2 m Unit Telescope, high-resolution mode</span></div>
    <div class="fact card"><b>GJ 570 A</b><span>a K4 dwarf about 6 parsecs away</span></div>
    <div class="fact card"><b>2,369 spectra</b><span>25 s exposures, one about every 61 s, over five usable nights</span></div>
    <div class="fact card"><b>2.57 cm/s</b><span>peak oscillation amplitude found, against 16.0 cm/s for the Sun</span></div>
  </section>

  <section class="grid-2">
    <div class="prose">
      <h2>What I did</h2>
      <p>Visitor mode means the observer travels to the telescope and runs the observations with ESO's staff, instead of sending instructions for others to execute. For six nights I observed GJ 570 A with ESPRESSO, taking a short exposure about once a minute to follow the star's surface as it moved towards and away from us.</p>
      <p>The weather took its share. High winds and cloud kept the telescope closed on the first night and for half of the fourth, which left five usable nights and 2,369 spectra. I did this on behalf of the principal investigator, Tiago L. Campante, under his programme 0113.D-0255(B); the proposal was his, not mine.</p>
    </div>
    <div class="prose">
      <h2>What the data showed</h2>
      <p>GJ 570 A rings like a bell with periods of three to four minutes, but very quietly: its surface moves by about 2.6 cm per second at the peak, a sixth of the Sun's value. Together with GJ 783 A, observed later in 2024, it shows that small, cool stars oscillate more weakly than the rule for Sun-like stars predicts, and 3D simulations of their outer layers do not reproduce the drop.</p>
      <p>The results are in Campante et al. 2026, published in <i>Astronomy and Astrophysics</i> (<a href="https://doi.org/10.1051/0004-6361/202660350">doi:10.1051/0004-6361/202660350</a>), where I am sixth of 24 authors. <a href="{{ '/papers/campante-2026-gj570a/' | relative_url }}">Read the plain-language explainer</a>.</p>
    </div>
  </section>
  <section>
    <figure class="panel blueprint wide-fig vlt-fig" id="light-path" data-build>
      <div class="vlt-figs">
        {% include figures/vlt-lightpath.svg %}
        {% include figures/espresso-output.svg %}
      </div>
      <figcaption class="credit" style="padding:6px 10px 2px">FIG 2. How the starlight reaches the detector, and what comes out. A spectrograph measures the Doppler shift of the star's absorption lines, so its output is the speed of the stellar surface, one velocity per exposure, not a light curve of brightness. The output panel shows velocities of GJ 570 A from the night of 8 to 9 May 2024 with slow drifts removed, and the power spectrum of all 2,250 usable velocities from the five nights (weighted sine fits; raw power drawn as the highest value in each plotted column; smoothed curve and noise level times three), computed from the public data of Campante et al. 2026 (Zenodo, <a href="https://doi.org/10.5281/zenodo.17236515">doi:10.5281/zenodo.17236515</a>, CC BY 4.0); the dotted line marks their νmax of 4705 μHz.</figcaption>
    </figure>
  </section>

  <section>
    <div class="section-head"><h2>From the run</h2><p>Photographs from my May 2024 stay at Paranal.</p></div>
    <div class="gallery">
      <figure class="wide"><img src="{{ '/assets/img/photos/ut-mirror-cell.webp' | relative_url }}" alt="The underside of a Unit Telescope's mirror cell and mount, seen from the dome floor." loading="lazy"><figcaption>The mount and mirror cell of a Unit Telescope, from the dome floor.</figcaption></figure>
      <figure><img src="{{ '/assets/img/photos/ut-dome-interior.webp' | relative_url }}" alt="Andreas standing beneath the mirror cell of a Unit Telescope inside its dome." loading="lazy"><figcaption>Under the mirror cell of an 8.2 m telescope.</figcaption></figure>
      <figure><img src="{{ '/assets/img/photos/paranal-milky-way.webp' | relative_url }}" alt="The Milky Way over Paranal before dawn." loading="lazy"><figcaption>The Milky Way before dawn.</figcaption></figure>
      <figure class="wide"><img src="{{ '/assets/img/photos/atacama-sunset.webp' | relative_url }}" alt="Sunset over the Atacama desert and the Pacific cloud deck, seen from Paranal." loading="lazy"><figcaption>Sunset over the Atacama and the Pacific cloud deck.</figcaption></figure>
      <figure class="wide"><img src="{{ '/assets/img/photos/vlt-daylight.webp' | relative_url }}" alt="Andreas in a hard hat in front of a Unit Telescope enclosure in daylight." loading="lazy"><figcaption>On the platform in daylight.</figcaption></figure>
      <figure><img src="{{ '/assets/img/photos/vlt-golden-hour.webp' | relative_url }}" alt="Andreas on the VLT platform at sunset." loading="lazy"><figcaption>The platform at sunset, before the night's observing.</figcaption></figure>
    </div>
  </section>

  <p class="muted small">More context: <a href="{{ '/guide/eso-vlt/' | relative_url }}">what ESO and the VLT are</a>, and <a href="{{ '/guide/asteroseismology/' | relative_url }}">what asteroseismology measures</a>.</p>
</div>
