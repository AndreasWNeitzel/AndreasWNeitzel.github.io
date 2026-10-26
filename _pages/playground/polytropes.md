---
layout: page
permalink: /playground/polytropes/
crumb: {label: Software, url: /software/}
title: Build a star
description: Solve the Lane-Emden equation in your browser, scale the polytrope to the Sun, 61 Vir or GJ 504, infer its index from the luminosity with a Monte Carlo over the published uncertainties, and see where it departs from a MESA model.
lede: Solve the Lane-Emden equation here in your browser, scale the result to a real star and see where a polytrope stops describing one.
math: true
---
<link rel="stylesheet" href="{{ '/assets/css/playground.css' | relative_url }}">
<link rel="stylesheet" href="{{ '/assets/css/polytrope-playground.css' | relative_url }}">
<div class="pg-page">
<p class="pg-intro">A polytrope assumes one relation between pressure and density, <span class="tex" data-tex="P = K\rho^{1 + 1/n}">P = Kρ^(1 + 1/n)</span>. Solved for an index <span class="tex" data-tex="n">n</span> and scaled to a star's mass and radius, it gives the run of density, pressure and temperature, and hydrogen burning in that structure gives a luminosity to match against the observed one.</p>

<section class="pg pt" id="pt-playground" aria-label="Polytrope playground" data-stars="{{ '/assets/data/playground/polytrope_stars.json' | relative_url }}" data-mesa="{{ '/assets/data/playground/mesa_1msun_profile.json' | relative_url }}">
  <div class="pt-dash">
    <div class="pt-ctrl">
    <div class="pg-panel pg-run pt-run">
      <label class="pg-field"><span class="pg-label">Star</span><span class="pg-select"><select name="star" class="pt-star" disabled><option>Loading</option></select></span></label>
      <p class="pt-obs">Loading the star table.</p>
      <div class="pg-buttons">
        <button type="button" class="btn btn--primary btn--sm pt-draw" title="Sample M, R and L from their uncertainties" disabled>Draw</button>
        <button type="button" class="btn btn--sm pt-reset" title="Discard the draws" disabled>Reset</button>
      </div>
      <div class="pg-live" aria-live="polite" aria-atomic="true">
        <dl class="pg-readout">
          <div><dt>n at L obs</dt><dd><span class="pt-nstar">&hellip;</span></dd></div>
          <div><dt>L model at slider n</dt><dd><span class="pt-lmodel">&hellip;</span> <small>L&#9737;</small></dd></div>
        </dl>
        <p class="pg-state">Loading.</p>
      </div>
    </div>
    <form class="pg-panel pg-settings pt-settings" aria-label="Polytrope settings">
      <label class="pt-slider pt-slider--wide"><span class="pt-slider-head"><span class="pg-label">Polytropic index n</span><output>3.00</output></span><input type="range" name="n" min="0" max="4.9" step="0.01" value="3" disabled></label>
      <label class="pt-slider"><span class="pt-slider-head"><span class="pg-label">Mass (M&#9737;)</span><output>1.00</output></span><input type="range" name="M" min="0.5" max="2" step="0.01" value="1" disabled></label>
      <label class="pt-slider"><span class="pt-slider-head"><span class="pg-label">Radius (R&#9737;)</span><output>1.00</output></span><input type="range" name="R" min="0.5" max="2.5" step="0.01" value="1" disabled></label>
      <label class="pt-slider"><span class="pt-slider-head"><span class="pg-label">Hydrogen X</span><output>0.74</output></span><input type="range" name="X" min="0.5" max="0.8" step="0.01" value="0.7381" disabled></label>
      <label class="pt-slider"><span class="pt-slider-head"><span class="pg-label">Metals Z</span><output>0.013</output></span><input type="range" name="Z" min="0.001" max="0.04" step="0.001" value="0.0134" disabled></label>
      <p class="pg-hint">A star sets M, R, X and Z and moves n to the index at its luminosity; every slider move re-solves the model.</p>
    </form>
    </div>

    <figure class="pg-panel panel pt-main">
      <figcaption class="pg-head">
        <span class="pg-title">Inside the star</span>
        <span class="pg-key"><span><i class="k-poly"></i>polytrope</span><span class="pt-main-key" hidden><i class="k-mesa"></i>MESA model, 1 M&#9737; at 2.8 Gyr</span><span class="pt-main-key" hidden><i class="k-conv"></i>convective in MESA</span></span>
      </figcaption>
      <div class="pg-stage"><canvas role="img" aria-label="Density, temperature, pressure and energy generation against fractional radius"></canvas><div class="pg-tip" hidden></div></div>
    </figure>

    <figure class="pg-panel pt-curve">
      <figcaption class="pg-head"><span class="pg-title">Model luminosity against index</span><span class="pg-key"><span><i class="k-obs"></i><span class="pt-curve-key">L obs</span></span></span></figcaption>
      <div class="pg-stage"><canvas role="img" aria-label="Model luminosity in solar units on a log scale against the polytropic index from 0 to 4.9, with the observed luminosity marked"></canvas><div class="pg-tip" hidden></div></div>
    </figure>

    <figure class="pg-panel pt-hist">
      <figcaption class="pg-head"><span class="pg-title">Index from the uncertainties</span><span class="pg-key pt-mc-key">no draws yet</span></figcaption>
      <div class="pg-stage"><canvas role="img" aria-label="Histogram of the polytropic index over Monte Carlo draws of mass, radius and luminosity, with the median and the 68 per cent interval"></canvas></div>
    </figure>
  </div>

  <section class="pg-panel pt-detail" aria-label="The solution and the energy generation">
    <div class="pg-head"><span class="pg-title">The solution behind the picture</span></div>
    <p class="pt-facts">Solving.</p>
    <div class="pg-pair">
      <figure class="pg-sub pt-theta">
        <div class="pg-stage"><canvas role="img" aria-label="The Lane-Emden solution theta against xi for the chosen index, with the exact solutions for n = 0, 1 and 5"></canvas></div>
        <figcaption class="pg-caption"><span class="pt-check">Checking the solver against the exact solutions.</span></figcaption>
      </figure>
      <figure class="pg-sub pt-eps">
        <div class="pg-stage"><canvas role="img" aria-label="Energy generation of the pp chain and the CNO cycle against fractional radius, with the fraction of the luminosity generated inside each radius"></canvas></div>
        <figcaption class="pg-caption"><span class="pg-key"><span><i class="k-pp"></i>pp chain</span><span><i class="k-cno"></i>CNO cycle</span><span><i class="k-cum"></i>L inside r, right axis</span><span class="pt-main-key" hidden><i class="k-ana"></i>X in MESA, right axis</span></span> <span class="pt-share"></span></figcaption>
      </figure>
    </div>
  </section>
  <noscript><p class="pg-state">The playground needs JavaScript. The data it uses are described below.</p></noscript>
</section>

<details class="pg-more">
  <summary>What you are looking at</summary>
  <div class="prose">
    <p>Writing <span class="tex" data-tex="\rho = \rho_c\,\theta^n">ρ = ρ_c θ^n</span> and measuring the radius in units of <span class="tex" data-tex="\alpha^2 = (n+1)K\rho_c^{1/n - 1}/(4\pi G)">α² = (n + 1)K ρ_c^(1/n − 1)/(4πG)</span> turns hydrostatic equilibrium and mass conservation into the Lane-Emden equation,</p>
    <p><span class="tex tex-display" data-tex="\frac{1}{\xi^2}\frac{d}{d\xi}\left(\xi^2\frac{d\theta}{d\xi}\right) + \theta^n = 0,\qquad \theta(0) = 1,\quad \theta'(0) = 0.">(1/ξ²) d/dξ (ξ² dθ/dξ) + θ^n = 0, with θ(0) = 1 and θ′(0) = 0.</span></p>
    <p>The solver integrates it by fourth-order Runge-Kutta from a series start, in steps of 0.01 that grow with ξ, and halves the last step until the first zero, ξ₁, is bracketed within 10⁻⁹. At n = 0 and n = 1 the equation has closed forms, θ = 1 − ξ²/6 and θ = sin ξ/ξ; at n = 5 the solution (1 + ξ²/3)^(−1/2) never reaches zero. The caption under the solution reports the comparison, and the tabulated values of Chandrasekhar (1939) for n = 1.5, 3 and 4 are reproduced to the printed digits (ξ₁ = 3.65375, 6.89685 and 14.97155).</p>
    <p>With M and R the constants follow: <span class="tex" data-tex="\rho_c = \bar\rho\,\xi_1 / (3\,|\theta'(\xi_1)|)">ρ_c = ρ̄ ξ₁/(3|θ′(ξ₁)|)</span> with <span class="tex" data-tex="\bar\rho = 3M/(4\pi R^3)">ρ̄ = 3M/(4πR³)</span>, <span class="tex" data-tex="P_c = GM^2 / \big(4\pi R^4 (n+1)\,\theta'(\xi_1)^2\big)">P_c = GM²/(4πR⁴(n + 1)θ′(ξ₁)²)</span>, and the ideal gas with the mean molecular weight of a fully ionised mixture, <span class="tex" data-tex="\mu = 4/(3 + 5X - Z)">μ = 4/(3 + 5X − Z)</span>, gives <span class="tex" data-tex="T_c = \mu m_u P_c / (k \rho_c)">T_c = μ m_u P_c/(k ρ_c)</span>. Inside, ρ = ρ_c θ^n, P = P_c θ^(n+1) and T = T_c θ at r = R ξ/ξ₁. Radiation pressure, degeneracy and any change of composition with depth are left out: a polytrope has one μ throughout.</p>
    <p>The energy generation is the pp chain plus the CNO cycle in the approximations of Kippenhahn, Weigert and Weiss (2012), eqs. (18.63) and (18.65), which fit the NACRE rates of Angulo et al. (1999): <span class="tex" data-tex="\varepsilon_{pp} = 2.57\times10^{4}\,\psi f_{11} g_{11}\,\rho X^2\, T_9^{-2/3}\, e^{-3.381\, T_9^{-1/3}}">ε_pp = 2.57 × 10⁴ ψ f₁₁ g₁₁ ρ X² T₉^(−2/3) exp(−3.381 T₉^(−1/3))</span> with <span class="tex" data-tex="g_{11} = 1 + 3.82\,T_9 + 1.51\,T_9^2 + 0.144\,T_9^3 - 0.0114\,T_9^4">g₁₁ = 1 + 3.82 T₉ + 1.51 T₉² + 0.144 T₉³ − 0.0114 T₉⁴</span>, and <span class="tex" data-tex="\varepsilon_{CNO} = 8.24\times10^{25}\, g_{14,1}\, X_{CNO} X \rho\, T_9^{-2/3}\, e^{-15.231\, T_9^{-1/3} - (T_9/0.8)^2}">ε_CNO = 8.24 × 10²⁵ g₁₄ X_CNO X ρ T₉^(−2/3) exp(−15.231 T₉^(−1/3) − (T₉/0.8)²)</span> with <span class="tex" data-tex="g_{14,1} = 1 - 2.00\,T_9 + 3.41\,T_9^2 - 2.43\,T_9^3">g₁₄ = 1 − 2.00 T₉ + 3.41 T₉² − 2.43 T₉³</span>, both in erg g⁻¹ s⁻¹ with ρ in g cm⁻³ and T₉ = T/10⁹ K. The page takes ψ = 1 (the pp I branch alone), f₁₁ = 1 (no screening) and X_CNO = 0.66 Z, the share of C, N and O among the metals in the solar mixture of Asplund et al. (2009). The luminosity is <span class="tex" data-tex="L = \int_0^R 4\pi r^2 \rho\,\varepsilon\, dr">L = ∫ 4πr² ρ ε dr</span> over the model, by Simpson's rule on 400 intervals.</p>
    <p>The model luminosity rises steeply with n because the central temperature does, so one index matches the observed luminosity: the dot on the curve and the first readout. Draw repeats that match with M, R and L sampled from the published uncertainties (a normal distribution; a split normal where the error bars are asymmetric; in log L where the paper quotes it that way) and collects the indices in the histogram with their median and 16th to 84th percentiles, until 2,000 draws or Pause; the small triangle under its axis marks the index at the central values. The nominal Sun and the MESA model carry no uncertainties, so there is nothing to draw for them.</p>
    <p>For the Sun and the MESA preset the dots are the interior of a 1 M☉, [Fe/H] = 0 MESA model at 2.76 Gyr, the stored profile nearest the Sun's age (see the data notes), and the shaded band is its convective envelope, which begins at 0.74 R. The polytrope has a single index everywhere; the model's envelope follows a nearly adiabatic run of pressure with density that a core-fitted index cannot share, and its composition is not uniform: the hydrogen fraction, the dotted curve in the energy panel, falls from 0.70 at the surface to 0.50 at the centre, where the pp chain has been at work. The two small panels show the solution θ(ξ) against the three exact cases, and the energy generation split into its two chains with the fraction of the luminosity produced inside each radius. Hover over the figures for values; a click on the luminosity curve sets n.</p>
  </div>
</details>

<section class="prose pg-credits" aria-labelledby="origin">
  <h2 id="origin">Where it came from</h2>
  <p>This page descends from the first project of my Computational Astronomy course at the University of Porto (2018/19): a Python notebook that solved the Lane-Emden equation with scipy, matched the model luminosity of the Sun, 61 Vir and GJ 504 to the observed one and ran a Monte Carlo over the quoted errors of M, R and L. This version runs the same chain in the browser and re-solves on every slider move; it uses the IAU 2015 nominal Sun, takes the rate formulae and the constants from the sources named below, states the uncertainty conventions of each paper, checks the solver against the three exact solutions, and adds the comparison with a full stellar model.</p>
</section>

<section class="prose pg-credits" aria-labelledby="credits">
  <h2 id="credits">Data and credits</h2>
  <p>Constants: the solar radius, luminosity and mass parameter are the nominal conversion constants of IAU 2015 Resolution B3 (<a href="https://doi.org/10.3847/0004-6256/152/2/41">Prša et al. 2016, AJ 152, 41</a>): R☉ = 6.957 × 10⁸ m, L☉ = 3.828 × 10²⁶ W and GM☉ = 1.3271244 × 10²⁰ m³ s⁻², with the <a href="https://physics.nist.gov/cuu/Constants/">CODATA 2022</a> values of G and the atomic mass constant. The solar composition, X = 0.7381 and Z = 0.0134, and the share of C, N and O in Z come from <a href="https://doi.org/10.1146/annurev.astro.46.060407.145222">Asplund et al. (2009, ARA&amp;A 47, 481)</a>.</p>
  <p>Rates and polytropes: the energy generation follows <a href="https://doi.org/10.1007/978-3-642-30304-3">Kippenhahn, Weigert and Weiss, Stellar Structure and Evolution (2nd ed., Springer, 2012)</a>, Sect. 18.5, eqs. (18.63) and (18.65), which are their fits to the NACRE rates of Angulo et al. (1999, Nucl. Phys. A 656, 3). The polytropic relations and the tabulated constants are those of Chandrasekhar (1939, An Introduction to the Study of Stellar Structure), as reproduced in Chap. 19 and Table 19.1 of the same textbook.</p>
  <p>61 Vir: radius 0.9867 ± 0.0048 R☉, luminosity 0.8222 ± 0.0033 L☉ and [Fe/H] = +0.01 from <a href="https://doi.org/10.1093/mnras/stt2360">von Braun et al. (2014, MNRAS 438, 2413)</a>, Table 4, where the radius comes from a CHARA angular diameter; the mass 0.95 (+0.04, −0.03) M☉ from <a href="https://doi.org/10.1088/0004-637X/708/2/1366">Vogt et al. (2010, ApJ 708, 1366)</a>, Table 1, who adopt the isochrone mass of Valenti and Fischer (2005). GJ 504: mass 1.16 ± 0.05 M☉, radius 1.36 ± 0.04 R☉ and [Fe/H] = +0.13 from <a href="https://doi.org/10.1088/0004-637X/806/2/163">Fuhrmann and Chini (2015, ApJ 806, 163)</a>, Table 1, whose note states that the errors are 2σ, so half of each is used as σ; log (L/L☉) = 0.332 ± 0.032 from <a href="https://doi.org/10.1088/0004-637X/774/1/11">Kuzuhara et al. (2013, ApJ 774, 11)</a>, Table 1, who adopt the Valenti and Fischer (2005) value. The two stars are planet hosts, and the two papers on GJ 504 disagree about its age; nothing here depends on that.</p>
  <p>The stellar model is one interior profile from the data file of my Stellar Explorer (<a href="https://github.com/AndreasWNeitzel/stellar-explorer-data">stellar-explorer-data on GitHub</a>): a 1 M☉, [Fe/H] = 0 track computed with MESA r24.08.1 (<a href="https://doi.org/10.1088/0067-0049/192/1/3">Paxton et al. 2011, ApJS 192, 3</a>) and post-processed with GYRE, stored as the 94 models whose interior the run saved, with 256-zone profiles. On the main sequence the run saved an interior every fifty models, so the one nearest the Sun's age (4.6 Gyr) is the model at 2.76 Gyr, and that is the age stated here; the mass, radius and luminosity of the MESA preset are those of that model, and its profile arrays are exported unchanged.</p>
  <p>Download the <a href="{{ '/assets/data/playground/polytrope_stars.json' | relative_url }}">star table</a>, which records every value with its table and convention, and the <a href="{{ '/assets/data/playground/mesa_1msun_profile.json' | relative_url }}">model profile</a> with its provenance. Everything runs in your browser, and nothing you do here is sent anywhere.</p>
</section>
</div>
<script src="{{ '/assets/js/tokens.js' | relative_url }}" defer></script>
<script type="module" src="{{ '/assets/js/playground/polytrope-playground.js' | relative_url }}"></script>
