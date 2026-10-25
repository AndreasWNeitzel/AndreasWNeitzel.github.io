---
layout: page
permalink: /playground/neural-network/
title: Neural-network playground
description: Train a small neural network in your browser to estimate the metallicity of 4,000 real stars from their Gaia DR3 spectra.
lede: Train a small neural network, here in your browser, to estimate how rich in heavy elements a star is from the way its light spreads across colours.
---
<link rel="stylesheet" href="{{ '/assets/css/playground.css' | relative_url }}">
<div class="pg-page">
<div class="pg-intro prose">
  <p>The network is a multilayer perceptron that reads the first 24 Hermite coefficients of a star's <em>Gaia</em> DR3 BP and RP spectra, each divided by the star's brightness, and estimates the metallicity [M/H] that <span class="pg-nb">GSP-Spec</span> measured for that star; it learns from 3,200 stars and is checked against 800 others that it never trains on.</p>
</div>

<section class="pg" id="nn-playground" aria-label="Neural-network playground" data-header="{{ '/assets/data/playground/gaia_xp_mh.json' | relative_url }}" data-worker="{{ '/assets/js/playground/nn-worker.js' | relative_url }}">
  <div class="pg-panel pg-controls">
    <div class="pg-run">
      <button type="button" class="btn btn--primary pg-train" disabled>Train</button>
      <button type="button" class="btn pg-step" title="Train for one epoch" disabled>Step</button>
      <button type="button" class="btn pg-reset" title="Start again from the same initial weights" disabled>Reset</button>
      <p class="pg-readout" aria-live="polite" aria-atomic="true"><span class="pg-epoch">Epoch 0</span> <span class="pg-rmse">Validation RMSE not measured yet</span></p>
    </div>
    <form class="pg-settings" aria-label="Network settings">
      <label class="pg-field">Hidden layers<span class="pg-select"><select name="layers"><option>1</option><option selected>2</option><option>3</option></select></span></label>
      <label class="pg-field">Units per layer<span class="pg-select"><select name="units"><option>4</option><option>8</option><option selected>16</option><option>24</option><option>32</option><option>48</option><option>64</option></select></span></label>
      <label class="pg-field">Activation<span class="pg-select"><select name="activation"><option value="tanh" selected>tanh</option><option value="relu">ReLU</option><option value="gelu">GELU</option></select></span></label>
      <label class="pg-field">Learning rate<span class="pg-select"><select name="lr"><option>0.0001</option><option>0.0003</option><option>0.001</option><option selected>0.003</option><option>0.01</option><option>0.03</option><option>0.1</option></select></span></label>
      <label class="pg-field">Batch size<span class="pg-select"><select name="batch"><option>16</option><option>32</option><option selected>64</option><option>128</option><option>256</option></select></span></label>
      <label class="pg-field">L2 penalty<span class="pg-select"><select name="l2"><option value="0" selected>0</option><option value="0.00001">0.00001</option><option value="0.0001">0.0001</option><option value="0.001">0.001</option><option value="0.01">0.01</option></select></span></label>
    </form>
    <p class="pg-note" hidden></p>
  </div>

  <div class="pg-grid">
    <figure class="pg-panel panel pg-net">
      <figcaption class="pg-head">
        <span class="pg-title">The network</span>
        <span class="pg-key"><span><i class="k-pos"></i>positive weight</span><span><i class="k-neg"></i>negative weight</span></span>
      </figcaption>
      <div class="pg-stage"><canvas role="img" aria-label="Diagram of the network"></canvas></div>
    </figure>

    <figure class="pg-panel pg-loss">
      <figcaption class="pg-head">
        <span class="pg-title">Error after each epoch</span>
        <span class="pg-key"><span><i class="k-train"></i>training</span><span><i class="k-val"></i>validation</span></span>
      </figcaption>
      <div class="pg-stage"><canvas role="img" aria-label="Mean squared error of the training and validation stars after each epoch, on a log scale"></canvas><div class="pg-tip" hidden></div></div>
      <p class="pg-caption">Mean squared error in dex², log scale, against epoch.</p>
    </figure>

    <figure class="pg-panel pg-parity">
      <figcaption class="pg-head"><span class="pg-title">Estimate against catalogue [M/H]</span></figcaption>
      <div class="pg-stage"><canvas role="img" aria-label="Network estimate of [M/H] against the GSP-Spec value for the 800 validation stars, coloured by temperature"></canvas><div class="pg-tip" hidden></div></div>
      <div class="pg-ramp"><span>Teff</span><span class="pg-ramp-bar"></span><span class="pg-ramp-ticks"></span></div>
    </figure>

    <section class="pg-panel pg-input" aria-label="One star's input">
      <div class="pg-head"><span class="pg-title">One star, as the network receives it</span></div>
      <div class="pg-stars" role="group" aria-label="Choose a star"></div>
      <p class="pg-facts"></p>
      <p class="pg-estimate"></p>
      <div class="pg-pair">
        <figure class="pg-sub pg-bars">
          <figcaption class="pg-subhead">
            <span class="pg-subtitle">Its 48 input numbers</span>
            <span class="pg-seg" role="group" aria-label="Scale of the bars"><button type="button" class="pg-mode" data-mode="network" aria-pressed="true">Network input</button><button type="button" class="pg-mode" data-mode="flux" aria-pressed="false">Divided by brightness</button></span>
          </figcaption>
          <div class="pg-stage"><canvas role="img" aria-label="The selected star's 24 BP and 24 RP coefficients as bars"></canvas></div>
          <p class="pg-caption"><span class="pg-bars-note">Each coefficient divided by the star's brightness, then rescaled so that 0 is the training average and 1 its spread.</span> Faded bars lie beyond the coefficients the catalogue lists as relevant for this star.</p>
        </figure>
        <figure class="pg-sub pg-spectrum">
          <figcaption class="pg-subhead"><span class="pg-subtitle">Spectra of the three example giants</span></figcaption>
          <div class="pg-stage"><canvas role="img" aria-label="Spectra of the three example giants, flux against wavelength from 336 to 1020 nm"></canvas></div>
          <p class="pg-caption">Flux relative to each star's mean, sampled from all 110 coefficients with GaiaXPy.<span class="pg-spec-note" hidden> The selected star is not one of the three.</span></p>
        </figure>
      </div>
    </section>
  </div>
  <p class="pg-status" role="status">Loading 4,000 stars (0.5 MB).</p>
  <noscript><p class="pg-status">The playground needs JavaScript. The data it uses are described below.</p></noscript>
</section>

<section class="prose" aria-labelledby="looking">
  <h2 id="looking">What you are looking at</h2>
  <p>The diagram draws the network. A star enters as 48 numbers, its BP coefficients in the upper band and its RP coefficients in the lower one, and passes through the hidden layers to a single output, the estimated [M/H].</p>
  <p>Each line is a weight, coloured by its sign and drawn thicker the larger it is; to stay legible, the diagram draws at most 400 lines, chosen by the size of their weights. Unless your device asks for reduced motion, dots trace the selected star through the layers, and each node's colour shows how strongly it responds to that star.</p>
  <p>The error curve gives the mean squared difference between the network's estimates and the <span class="pg-nb">GSP-Spec</span> values after each epoch, one pass through the 3,200 training stars. The validation stars never adjust the weights, so their curve shows how well the network generalises. When the validation curve flattens or turns upwards while the training curve keeps falling, the network has begun to fit noise in its training stars; an L2 penalty, which pulls the weights towards zero, usually delays that.</p>
  <p>The square plot sets each validation star's estimate against its <span class="pg-nb">GSP-Spec</span> value, which comes from a separate instrument on <em>Gaia</em>, the Radial Velocity Spectrometer. A perfect estimate would sit on the diagonal, and colour gives the star's temperature. Select a point to follow that star through the network and to see its input below.</p>
  <p>Train runs until you pause it, for at most 2,000 epochs, and Step trains for one epoch. Reset starts again from the same initial weights, so two runs that differ in one setting can be compared. Changing the layers, the units or the activation builds a new network, while the learning rate, the batch size and the L2 penalty take effect at once.</p>
  <p>The bars are the selected star's 48 input numbers. The curves are the spectra of three red giants of similar temperature and colour. Absorption lines of metals crowd the blue end of a spectrum, and the giant with [M/H] +0.25 has less blue light, relative to its mean, than the other two.</p>
  <p>This page is a teaching demonstration. <a href="https://doi.org/10.3847/1538-4365/acd53e">Andrae, Rix and Chandra (2023, ApJS 267, 8)</a> estimated metallicities from the same <em>Gaia</em> spectra for about 175 million stars, with a different method and a much larger training set.</p>
</section>

<section class="prose" aria-labelledby="credits">
  <h2 id="credits">Data and credits</h2>
  <p>The 4,000 stars are the first, in the random order that <em>Gaia</em> DR3 provides, whose <span class="pg-nb">GSP-Spec</span> parameters raise no warning in the first 13 quality flags (Recio-Blanco et al. 2023). That cut leaves few metal-poor stars, so [M/H] here runs only from −0.88 to +0.73 dex. The labels are the published catalogue values, with no calibration applied, and the split into 3,200 training and 800 validation stars is fixed.</p>
  <p>The labels and the selection come from the ESA <em>Gaia</em> archive. The XP coefficients come from the same <em>Gaia</em> DR3 table at the Gaia@AIP data centre, because the ESA archive serves that table only through its DataLink service. Each star's coefficients are divided by the sum of its first BP and first RP coefficient, a measure of its brightness, and the first 24 of the 55 in each band are kept.</p>
  <p>This page uses data from the European Space Agency mission <em>Gaia</em> (<a href="https://doi.org/10.1051/0004-6361/202243940">Gaia Collaboration, Vallenari et al. 2023, A&amp;A 674, A1</a>), processed by the <em>Gaia</em> Data Processing and Analysis Consortium (DPAC). The XP spectra are described by <a href="https://doi.org/10.1051/0004-6361/202243680">De Angeli et al. (2023, A&amp;A 674, A2)</a> and <a href="https://doi.org/10.1051/0004-6361/202243880">Montegriffo et al. (2023, A&amp;A 674, A3)</a>, and the <span class="pg-nb">GSP-Spec</span> parameters by <a href="https://doi.org/10.1051/0004-6361/202243750">Recio-Blanco et al. (2023, A&amp;A 674, A29)</a>.</p>
  <p>The example spectra were sampled with GaiaXPy, developed by members of DPAC. <em>Gaia</em> data are © ESA/Gaia/DPAC and released under <a href="https://creativecommons.org/licenses/by-sa/3.0/igo/">CC BY-SA 3.0 IGO</a>, and the derived files below are shared under the same licence.</p>
  <p>Download the <a href="{{ '/assets/data/playground/gaia_xp_mh.bin' | relative_url }}">data</a> (0.5 MB), its <a href="{{ '/assets/data/playground/gaia_xp_mh.json' | relative_url }}">header</a> and its <a href="{{ '/assets/data/playground/gaia_xp_mh.meta.json' | relative_url }}">provenance</a>, which records the queries, their dates and the cuts. Training runs in your browser, and nothing you do here is sent anywhere.</p>
</section>
</div>
<script src="{{ '/assets/js/tokens.js' | relative_url }}" defer></script>
<script type="module" src="{{ '/assets/js/playground/nn-playground.js' | relative_url }}"></script>
