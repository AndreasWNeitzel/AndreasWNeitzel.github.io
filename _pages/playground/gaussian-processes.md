---
layout: page
permalink: /playground/gaussian-processes/
crumb: {label: Software, url: /software/}
title: Gaussian-process playground
description: Draw random functions from four kernels, pin them down with observations, and fit a quasi-periodic Gaussian process to 223 real HARPS radial velocities of HD 41248 with a Metropolis sampler, in your browser.
lede: Draw random functions from a kernel, pin them down with observations, then fit a quasi-periodic Gaussian process to the real radial velocities of an active star.
math: true
---
<link rel="stylesheet" href="{{ '/assets/css/playground.css' | relative_url }}">
<link rel="stylesheet" href="{{ '/assets/css/gp-playground.css' | relative_url }}">
<div class="pg-page">
<section class="pg gp" id="gp-playground" aria-label="Gaussian-process playground" data-rv="{{ '/assets/data/playground/hd41248_harps.json' | relative_url }}" data-worker="{{ '/assets/js/playground/gp-worker.js' | relative_url }}">
  <div class="gp-modes">
    <div class="gp-switch" role="tablist" aria-label="Mode">
      <button type="button" class="btn btn--sm" role="tab" id="gp-tab-kernels" aria-selected="true" aria-controls="gp-kernels" data-mode="kernels">Kernels</button>
      <button type="button" class="btn btn--sm" role="tab" id="gp-tab-star" aria-selected="false" aria-controls="gp-star" data-mode="star">A star: HD 41248</button>
    </div>
    <p class="gp-mode-text" data-for="kernels">Random functions from four covariance functions, pinned down by observations you add; the marginal likelihood says which length scale and noise the points prefer.</p>
    <p class="gp-mode-text" data-for="star" hidden>A quasi-periodic Gaussian process for the activity in 223 HARPS velocities of HD 41248, its four kernel parameters and a jitter sampled by a Metropolis chain.</p>
  </div>

  <div class="gp-dash" id="gp-kernels" role="tabpanel" aria-labelledby="gp-tab-kernels">
    <div class="gp-ctrl">
      <div class="pg-panel pg-run">
        <div class="pg-buttons">
          <button type="button" class="btn btn--primary btn--sm gp-k-draw" title="Draw five new random functions">New draws</button>
          <button type="button" class="btn btn--sm gp-k-clear" title="Remove every observation">Clear points</button>
        </div>
        <div class="pg-live" aria-live="polite" aria-atomic="true">
          <dl class="pg-readout">
            <div><dt>Observations</dt><dd><span class="gp-k-count">0</span></dd></div>
            <div><dt>log marginal likelihood</dt><dd><span class="gp-k-lml">n/a</span></dd></div>
          </dl>
          <p class="pg-state gp-k-state">Click in the figure to add an observation, and on a point to remove it.</p>
        </div>
      </div>
      <form class="pg-panel pg-settings gp-k-settings" aria-label="Kernel settings">
        <label class="pg-field pg-field--wide"><span class="pg-label">Kernel</span><span class="pg-select"><select name="kernel"><option value="se" selected>Squared exponential</option><option value="per">Periodic</option><option value="qp">Quasi-periodic</option><option value="m32">Matérn 3/2</option></select></span></label>
        <label class="pg-field pg-field--wide gp-range" data-param="l"><span class="pg-label"><span>Length scale ℓ</span><output name="l-out">1.00</output></span><input type="range" name="l" min="-1" max="1" step="0.02" value="0" aria-label="Length scale, logarithmic"></label>
        <label class="pg-field pg-field--wide gp-range" data-param="P" hidden><span class="pg-label"><span>Period P</span><output name="P-out">2.0</output></span><input type="range" name="P" min="0.5" max="5" step="0.1" value="2" aria-label="Period"></label>
        <label class="pg-field pg-field--wide gp-range" data-param="lam" hidden><span class="pg-label"><span>Smoothing λ</span><output name="lam-out">1.00</output></span><input type="range" name="lam" min="-1" max="1" step="0.02" value="0" aria-label="Smoothing within a period, logarithmic"></label>
        <label class="pg-field pg-field--wide gp-range" data-param="sf"><span class="pg-label"><span>Amplitude σ<sub>f</sub></span><output name="sf-out">1.00</output></span><input type="range" name="sf" min="-0.6" max="0.6" step="0.02" value="0" aria-label="Amplitude, logarithmic"></label>
        <label class="pg-field pg-field--wide gp-range" data-param="sn"><span class="pg-label"><span>Noise σ<sub>n</sub></span><output name="sn-out">0.10</output></span><input type="range" name="sn" min="-2" max="0.3" step="0.02" value="-1" aria-label="Observation noise, logarithmic"></label>
        <p class="pg-hint">Length scales, amplitude and noise move on logarithmic scales. The period and the smoothing appear for the periodic kernels.</p>
      </form>
    </div>
    <figure class="pg-panel panel gp-main gp-k-main">
      <figcaption class="pg-head">
        <span class="pg-title gp-k-title">Five functions drawn from the prior</span>
        <span class="pg-key"><span><i class="k-mean"></i>mean</span><span><i class="k-band"></i>2σ band</span><span><i class="k-draw"></i>draws</span><span><i class="k-obs"></i>observation</span></span>
      </figcaption>
      <div class="pg-stage"><canvas role="img" aria-label="Random functions drawn from the kernel on 0 to 10, with the mean and the 2 sigma band"></canvas><div class="pg-tip" hidden></div></div>
    </figure>
    <figure class="pg-panel gp-a gp-k-kernel">
      <figcaption class="pg-head"><span class="pg-title">Covariance against separation</span></figcaption>
      <div class="pg-stage"><canvas role="img" aria-label="The kernel as a function of the separation between two inputs, from 0 to 10"></canvas></div>
    </figure>
    <figure class="pg-panel gp-b gp-k-lml">
      <figcaption class="pg-head"><span class="pg-title">log marginal likelihood over ℓ and σ<sub>n</sub></span><span class="pg-key">click to set</span></figcaption>
      <div class="pg-stage"><canvas role="img" aria-label="Map of the log marginal likelihood of the observations over the length scale and the noise, with the current values ringed"></canvas><div class="pg-tip" hidden></div></div>
    </figure>
  </div>

  <div class="gp-dash" id="gp-star" role="tabpanel" aria-labelledby="gp-tab-star" hidden>
    <div class="gp-ctrl">
      <div class="pg-panel pg-run">
        <div class="pg-buttons">
          <button type="button" class="btn btn--primary btn--sm gp-s-run" disabled>Run</button>
          <button type="button" class="btn btn--sm gp-s-step" title="Make 100 proposals" disabled>100 steps</button>
          <button type="button" class="btn btn--sm gp-s-reset" title="Start the chain again" disabled>Reset</button>
        </div>
        <div class="pg-live" aria-live="polite" aria-atomic="true">
          <dl class="pg-readout">
            <div><dt>Steps</dt><dd><span class="gp-s-steps">0</span></dd></div>
            <div><dt>Accepted</dt><dd><span class="gp-s-acc">n/a</span></dd></div>
          </dl>
          <p class="pg-state gp-s-state">Loading 223 velocities.</p>
        </div>
      </div>
      <form class="pg-panel pg-settings gp-s-settings" aria-label="Sampler settings">
        <label class="pg-field"><span class="pg-label">Proposal scale</span><span class="pg-select"><select name="scale"><option value="0.25">0.25</option><option value="0.5">0.5</option><option value="1" selected>1</option><option value="2">2</option><option value="4">4</option></select></span></label>
        <label class="pg-field"><span class="pg-label">Burn-in discarded</span><span class="pg-select"><select name="burn"><option value="0">none</option><option value="0.1">10%</option><option value="0.25" selected>25%</option><option value="0.5">50%</option></select></span></label>
        <label class="pg-field pg-field--wide"><span class="pg-label">Start the chain</span><span class="pg-select"><select name="start"><option value="fixed" selected>at the fixed point</option><option value="prior">at a random draw from the prior</option></select></span></label>
        <p class="pg-hint">Scale and burn-in apply at once; the start applies at the next Reset.</p>
      </form>
      <section class="pg-panel gp-params gp-s-params" aria-label="Parameters, priors and posterior">
        <table class="gp-table">
          <thead><tr><th scope="col"><span class="sr-only">Parameter</span></th><th scope="col">Now</th><th scope="col">Posterior</th></tr></thead>
          <tbody></tbody>
        </table>
        <p class="gp-s-note">Median and 16 to 84% interval after burn-in; priors below.</p>
      </section>
    </div>
    <figure class="pg-panel panel gp-main gp-s-main">
      <figcaption class="pg-head">
        <span class="pg-title gp-s-title">HD 41248, HARPS velocities</span>
        <label class="pg-inline"><span class="pg-label">Window</span><span class="pg-select pg-select--sm"><select class="gp-s-window" aria-label="Part of the series to show"><option>Loading</option></select></span></label>
        <span class="pg-key gp-key--row"><span><i class="k-data"></i>velocity</span><span><i class="k-mean"></i>marginal mean</span><span><i class="k-band"></i>2σ band</span><span><i class="k-curve"></i>12 posterior samples</span></span>
      </figcaption>
      <div class="pg-stage"><canvas role="img" aria-label="Radial velocities of HD 41248 in a 150 day window with the marginalised Gaussian-process prediction, and an overview of the whole series"></canvas><div class="pg-tip" hidden></div></div>
      <figcaption class="pg-caption">Velocities about the mean against days since the first observation (31 October 2003), with their catalogue uncertainties. Click in the strip to move the 150 day window; the band is the activity signal alone, without the jitter.</figcaption>
    </figure>
    <figure class="pg-panel gp-a gp-s-trace">
      <figcaption class="pg-head"><span class="pg-title gp-s-trace-title">Trace</span><span class="pg-key">burn-in shaded</span></figcaption>
      <div class="pg-stage"><canvas role="img" aria-label="Trace plots of the two parameters chosen for the pair plot"></canvas></div>
    </figure>
    <figure class="pg-panel gp-b gp-s-pair">
      <figcaption class="pg-head"><span class="pg-title gp-s-pair-title">Pair plot</span><span class="gp-axes"><label class="pg-inline"><span class="pg-label">x</span><span class="pg-select pg-select--sm"><select class="gp-s-px" aria-label="Parameter on the x axis"><option value="eta3">η3</option></select></span></label><label class="pg-inline"><span class="pg-label">y</span><span class="pg-select pg-select--sm"><select class="gp-s-py" aria-label="Parameter on the y axis"><option value="eta1">η1</option></select></span></label></span></figcaption>
      <div class="pg-stage"><canvas role="img" aria-label="Scatter of two parameters over the posterior states after burn-in, with marginal histograms"></canvas><div class="pg-tip" hidden></div></div>
    </figure>
  </div>

  <section class="pg-panel gp-details" aria-label="The model">
    <div class="gp-cols" data-for="kernels">
      <div class="gp-col">
        <span class="pg-title">The kernel</span>
        <span class="tex tex-display gp-k-formula" data-tex="k(x, x') = \sigma_f^2 \exp\left(-\frac{(x - x')^2}{2\ell^2}\right)">k(x, x') = σf² exp(−(x − x')² / 2ℓ²)</span>
        <p>A Gaussian process is a distribution over functions: any finite set of function values is jointly Gaussian, with mean zero here and the covariance given by the kernel. The five draws are samples from that joint distribution on a grid of 240 points.</p>
      </div>
      <div class="gp-col">
        <span class="pg-title">Conditioning on observations</span>
        <span class="tex tex-display" data-tex="\boldsymbol{\mu}_* = K_*^{\mathsf T} (K + \sigma_n^2 I)^{-1} \mathbf{y}, \qquad \Sigma_* = K_{**} - K_*^{\mathsf T} (K + \sigma_n^2 I)^{-1} K_*">μ* = K*ᵀ (K + σn² I)⁻¹ y,  Σ* = K** − K*ᵀ (K + σn² I)⁻¹ K*</span>
        <span class="tex tex-display" data-tex="\ln p(\mathbf{y}) = -\tfrac{1}{2}\, \mathbf{y}^{\mathsf T} (K + \sigma_n^2 I)^{-1} \mathbf{y} - \tfrac{1}{2} \ln\left|K + \sigma_n^2 I\right| - \tfrac{n}{2} \ln 2\pi">ln p(y) = −½ yᵀ (K + σn² I)⁻¹ y − ½ ln|K + σn² I| − (n/2) ln 2π</span>
        <p>Observations enter with the same noise σ<sub>n</sub>. The log marginal likelihood trades fit against complexity, so the map on the right is where the hyperparameters would be learnt from the points.</p>
      </div>
    </div>
    <div class="gp-cols" data-for="star" hidden>
      <div class="gp-col">
        <span class="pg-title">The model</span>
        <span class="tex tex-display" data-tex="k(t_i, t_j) = \eta_1^2 \exp\left[-\frac{(t_i - t_j)^2}{2\eta_2^2} - \frac{2 \sin^2\left(\pi (t_i - t_j) / \eta_3\right)}{\eta_4^2}\right] + \left(\sigma_i^2 + s^2\right) \delta_{ij}">k(ti, tj) = η1² exp[−(ti − tj)² / 2η2² − 2 sin²(π (ti − tj) / η3) / η4²] + (σi² + s²) δij</span>
        <span class="tex tex-display" data-tex="\ln p(\mathbf{y} \mid \boldsymbol{\theta}) = -\tfrac{1}{2}\, \mathbf{y}^{\mathsf T} K^{-1} \mathbf{y} - \tfrac{1}{2} \ln|K| - \tfrac{n}{2} \ln 2\pi">ln p(y | θ) = −½ yᵀ K⁻¹ y − ½ ln|K| − (n/2) ln 2π</span>
        <p>The quasi-periodic kernel of Haywood et al. (2014): η<sub>1</sub> is the amplitude of the activity signal, η<sub>2</sub> the lifetime of the active regions, η<sub>3</sub> the rotation period and η<sub>4</sub> how far from a sinusoid one rotation may stray. The catalogue uncertainties σ<sub>i</sub> and the jitter s sit on the diagonal only. The likelihood comes from a Cholesky factorisation of K.</p>
      </div>
      <div class="gp-col">
        <span class="pg-title">Priors and the sampler</span>
        <ul>
          <li>η1 log-uniform 0.1 to 50 m/s, η2 log-uniform 1 to 1,000 d</li>
          <li>η3 uniform 10 to 40 d, η4 log-uniform 0.1 to 10, s log-uniform 0.1 to 20 m/s</li>
          <li>fixed start: η1 5 m/s, η2 50 d, η3 20 d, η4 1, s 2 m/s</li>
          <li>Gaussian random walk in (ln η1, ln η2, η3, ln η4, ln s), steps 0.127, 0.236, 0.534, 0.168, 0.145 times the proposal scale</li>
        </ul>
        <span class="tex tex-display" data-tex="\text{accept } \boldsymbol{\theta}' \text{ if } \ln u < \ln p(\boldsymbol{\theta}' \mid \mathbf{y}) - \ln p(\boldsymbol{\theta} \mid \mathbf{y}), \quad u \sim U(0, 1)">accept θ' if ln u < ln p(θ' | y) − ln p(θ | y), u ~ U(0, 1)</span>
        <p>Proposals outside the prior bounds are rejected. Every state is stored, repeats included, so the chain is a sample from the posterior; only accepted moves would not be. The step sizes follow the 2.38/√d rule of Roberts, Gelman and Gilks (1997) applied to the spread of a 60,000-step pilot run.</p>
      </div>
    </div>
  </section>
  <noscript><p class="pg-state">The playground needs JavaScript. The data it uses are described below.</p></noscript>
</section>

<details class="pg-more">
  <summary>What you are looking at</summary>
  <div class="prose">
    <p><b>Kernels.</b> The main figure shows five random functions drawn from the chosen kernel on x from 0 to 10, with the mean and the band two standard deviations either side. With no observations that is the prior: the mean is zero and the band has the width of the amplitude. The squared exponential gives smooth functions, Matérn 3/2 rougher ones, the periodic kernel repeats exactly and the quasi-periodic kernel repeats while slowly forgetting, which is the behaviour of spots rotating across a stellar surface.</p>
    <p>Click in the figure to add an observation (up to 40) and the posterior replaces the prior: the mean bends through the points, the band narrows near them and widens again as the function is left to itself. New draws samples five fresh functions from whichever distribution is shown. The small panel plots the kernel against the separation of two inputs, the shape that every column of the covariance matrix shares.</p>
    <p>The map is the log marginal likelihood of the observations over the length scale and the noise, 28 by 28 cells, darker where the points are more probable; the colour runs from the tenth percentile of the map to its maximum, which a cross marks. Short length scales with little noise fit every point but pay for the complexity; long ones explain the points as noise. Click a cell to adopt its values and watch the figure change.</p>
    <p><b>A star.</b> The second mode fits the quasi-periodic kernel to 223 HARPS velocities of HD 41248 (velocity about the mean against days since the first observation), the activity signal of a star without a confirmed planet. Run starts a Metropolis chain over the five parameters; the readouts give the steps taken and the share of proposals accepted, and the table gives each parameter and the log posterior now, with the median and the 16 to 84 percent interval after burn-in.</p>
    <p>The trace follows the two parameters of the pair plot over the whole chain, with the burn-in shaded. The pair plot is one panel of a corner plot: every state after burn-in, with the marginal histograms along the top and the right and the current state ringed. A proposal scale of 1 accepts about a quarter of the proposals, close to the optimum for a random walk; smaller steps accept more but move less, larger steps stall.</p>
    <p>The band in the main figure is marginalised over the posterior: 32 states are taken at even spacing from the chain after burn-in, the conditional mean and variance of the activity signal are computed for each, and the mixture's mean and spread are drawn, with the conditional means of the first 12. Before the first step the band is the prediction at the starting values. From the fixed point the chain settles within a few thousand steps near η<sub>3</sub> of 25.6 d, η<sub>1</sub> of 2.9 m/s and a jitter of 1.3 m/s (the pilot run below).</p>
  </div>
</details>

<section class="prose pg-credits" aria-labelledby="origin">
  <h2 id="origin">Where it came from</h2>
  <p>This page rebuilds my second project for AST4000, Data Analysis in Astronomy, in the MSc at the University of Porto (2020/21): prior draws, conditioning on points and a Metropolis fit of a quasi-periodic kernel to HD 41248. The R notebook had faults I saw only later: the jitter never entered the covariance, the amplitude was not squared, only accepted proposals were stored, the acceptance test compared likelihoods rather than their logarithms, no priors were stated and the prediction was never marginalised over the chain. This version fixes them all and uses the published velocities, not the course file.</p>
</section>

<section class="prose pg-credits" aria-labelledby="credits">
  <h2 id="credits">Data and credits</h2>
  <p>The velocities are the 223 HARPS measurements of HD 41248 published with <a href="https://doi.org/10.1088/0004-637X/794/2/110">Jenkins and Tuomi (2014, ApJ 794, 110)</a>, read unchanged from VizieR catalogue <a href="https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=J/ApJ/794/110">J/ApJ/794/110</a> (table 1) at the CDS, Strasbourg. They run from 31 October 2003 to 6 December 2013, 3,689 days, with a scatter of 3.76 m/s and a median uncertainty of 1.25 m/s; the page subtracts their mean of 3,528.06 m/s and keeps the catalogue uncertainties. Use of VizieR is acknowledged as the CDS asks (<a href="https://doi.org/10.1051/aas:2000169">Ochsenbein, Bauer and Marcout 2000</a>).</p>
  <p>HD 41248 is a solar analogue with a contested planetary system. <a href="https://doi.org/10.1088/0004-637X/771/1/41">Jenkins et al. (2013)</a> reported signals of 18.357 and 25.648 days in 62 velocities as super-Earths near a 7:5 resonance; <a href="https://doi.org/10.1051/0004-6361/201423808">Santos et al. (2014)</a> added 162 velocities, tied the 25 day signal to rotation through the activity indicators and could not confirm the 18 day one; Jenkins and Tuomi (2014) kept the planets in all 223. With ESPRESSO, <a href="https://doi.org/10.1051/0004-6361/201936389">Faria et al. (2020, A&amp;A 635, A13)</a> found that a Gaussian process alone explains the data, with a rotation period matching <em>TESS</em> photometry; that rotation is what this page recovers.</p>
  <p>The quasi-periodic kernel for activity follows <a href="https://doi.org/10.1093/mnras/stu1320">Haywood et al. (2014, MNRAS 443, 2517)</a>; the kernels, conditioning and marginal likelihood are chapters 2, 4 and 5 of <a href="https://gaussianprocess.org/gpml/">Rasmussen and Williams (2006)</a>; the proposal scaling is from <a href="https://doi.org/10.1214/aoap/1034625254">Roberts, Gelman and Gilks (1997)</a>. The pilot run (60,000 steps, the first 8,000 adapted and discarded, 25 percent accepted) gave η<sub>1</sub> 2.9 m/s, η<sub>2</sub> 38 d, η<sub>3</sub> 25.6 d, η<sub>4</sub> 0.67 and s 1.3 m/s as posterior medians.</p>
  <p>Download the <a href="{{ '/assets/data/playground/hd41248_harps.json' | relative_url }}">velocities</a> (12 kB), their <a href="{{ '/assets/data/playground/hd41248_harps.meta.json' | relative_url }}">provenance</a>, which records the query, its date and the catalogue ReadMe, and the <a href="{{ '/assets/data/playground/hd41248_gp_pilot.json' | relative_url }}">pilot run</a>. The table remains the authors' and the journal's; it is reproduced here for teaching, with its reference. Everything runs in your browser, and nothing you do here is sent anywhere.</p>
</section>
</div>
<script src="{{ '/assets/js/tokens.js' | relative_url }}" defer></script>
<script type="module" src="{{ '/assets/js/playground/gp-playground.js' | relative_url }}"></script>
