---
layout: page
permalink: /playground/orbits/
crumb: {label: Software, url: /software/}
math: true
title: Orbits playground
description: Integrate a Molniya constellation and a geostationary satellite around the Earth, then six real Gaia DR3 stars through a model Milky Way, in your browser, with three integrators and the live energy error.
lede: Integrate orbits in your browser, from a satellite's twelve hours around the Earth to a star's billion years through the Milky Way.
---
<link rel="stylesheet" href="{{ '/assets/css/playground.css' | relative_url }}">
<link rel="stylesheet" href="{{ '/assets/css/orbits-playground.css' | relative_url }}">
<div class="pg-page">
<p class="pg-intro">The same leapfrog, Runge-Kutta and Euler steppers move three Molniya satellites and a geostationary one around a point-mass Earth, with the visibility from three ground stations, and then six real stars from <em>Gaia</em> DR3 through the MWPotential2014 model of the Milky Way. The energy error shows what the choice of integrator costs.</p>

<section class="pg ob" id="orbits-playground" aria-label="Orbits playground" data-mode="earth" data-src="{{ '/assets/data/playground/orbits.json' | relative_url }}">
  <div class="ob-dash">
    <div class="pg-ctrl">
    <div class="pg-panel pg-run ob-run">
      <div class="ob-mode" role="group" aria-label="Problem">
        <button type="button" data-mode="earth" aria-pressed="true">Earth</button>
        <button type="button" data-mode="galaxy" aria-pressed="false">Galaxy</button>
      </div>
      <div class="pg-buttons">
        <button type="button" class="btn btn--primary btn--sm ob-run-btn" disabled>Run</button>
        <button type="button" class="btn btn--sm ob-step" title="Advance by one step" disabled>Step</button>
        <button type="button" class="btn btn--sm ob-reset" title="Return every body to its starting point" disabled>Reset</button>
      </div>
      <div class="pg-live" aria-live="polite" aria-atomic="true">
        <dl class="pg-readout ob-readout">
          <div><dt>Time</dt><dd><span class="ob-time">0</span></dd></div>
          <div data-mode="earth"><dt>Altitude</dt><dd><span class="ob-alt">&hellip;</span> <small>km</small></dd></div>
          <div data-mode="earth"><dt>Speed</dt><dd><span class="ob-speed">&hellip;</span> <small>km/s</small></dd></div>
          <div data-mode="galaxy"><dt>Eccentricity</dt><dd><span class="ob-ecc">&hellip;</span><small class="ob-ref ob-ecc-ref"></small></dd></div>
          <div data-mode="galaxy"><dt><i>z</i><sub>max</sub></dt><dd><span class="ob-zmax">&hellip;</span><small class="ob-ref ob-zmax-ref">kpc</small></dd></div>
          <div data-mode="galaxy"><dt><i>L</i><sub>z</sub></dt><dd><span class="ob-lz">&hellip;</span><small class="ob-ref ob-lz-ref">kpc km/s</small></dd></div>
          <div data-mode="galaxy"><dt>Energy <i>E</i></dt><dd><span class="ob-energy-value">&hellip;</span><small class="ob-ref ob-e-ref">km²/s²</small></dd></div>
          <div><dt>Energy error</dt><dd><span class="ob-err">&hellip;</span><small class="ob-ref ob-stepnow"></small></dd></div>
        </dl>
        <p class="pg-state">Loading the orbits (15 KB).</p>
      </div>
    </div>

    <form class="pg-panel pg-settings ob-settings" aria-label="Integration settings">
      <label class="pg-field pg-field--wide"><span class="pg-label">Integrator</span><span class="pg-select"><select name="integrator">
        <option value="leapfrog" selected>Leapfrog, symplectic</option>
        <option value="rk4">RK4, adaptive step</option>
        <option value="euler">Euler, the coursework scheme</option>
      </select></span></label>
      <label class="pg-field"><span class="pg-label">Step</span><span class="pg-select"><select name="step"><option>Loading</option></select></span></label>
      <label class="pg-field"><span class="pg-label">Speed</span><span class="pg-select"><select name="speed"><option>Loading</option></select></span></label>
      <label class="pg-field pg-field--wide"><span class="pg-label">Follow</span><span class="pg-select"><select name="follow"><option>Loading</option></select></span></label>
      <div class="ob-only" data-mode="earth">
        <label class="ob-slider ob-station"><span class="pg-label">Third station, latitude north</span><output name="latout">80.0°</output><input type="range" name="lat" min="60" max="90" step="0.5" value="80"></label>
      </div>
      <div class="ob-only" data-mode="galaxy">
        <details class="ob-tp">
          <summary>Launch a test particle, not a star</summary>
          <div class="ob-tp-grid">
            <label class="ob-slider"><span class="pg-label"><i>R</i></span><output name="tpRout">8.0 kpc</output><input type="range" name="tpR" min="0.5" max="40" step="0.1" value="8"></label>
            <label class="ob-slider"><span class="pg-label"><i>z</i></span><output name="tpZout">0.0 kpc</output><input type="range" name="tpZ" min="-5" max="5" step="0.1" value="0"></label>
            <label class="ob-slider"><span class="pg-label"><i>v</i><sub>R</sub></span><output name="tpVRout">0 km/s</output><input type="range" name="tpVR" min="-300" max="300" step="5" value="0"></label>
            <label class="ob-slider"><span class="pg-label"><i>v</i><sub>φ</sub></span><output name="tpVPout">220 km/s</output><input type="range" name="tpVP" min="-300" max="300" step="5" value="220"></label>
            <label class="ob-slider"><span class="pg-label"><i>v</i><sub>z</sub></span><output name="tpVZout">0 km/s</output><input type="range" name="tpVZ" min="-200" max="200" step="5" value="0"></label>
            <button type="button" class="btn btn--sm ob-launch" disabled>Launch</button>
          </div>
        </details>
      </div>
    </form>
    </div>

    <figure class="pg-panel panel ob-main">
      <figcaption class="pg-head"><span class="pg-title ob-main-title">Around the Earth</span><span class="pg-key ob-main-key"></span></figcaption>
      <div class="pg-stage"><canvas role="img" aria-label="Three Molniya satellites and a geostationary satellite around the rotating Earth, drawn to scale"></canvas></div>
      <p class="pg-caption ob-main-cap">Drag to turn the view. A line from a station to a satellite means the satellite is above that station's horizon.</p>
    </figure>

    <figure class="pg-panel ob-side">
      <figcaption class="pg-head"><span class="pg-title ob-side-title">Visible from the ground</span><span class="pg-key ob-side-key"></span></figcaption>
      <div class="pg-stage"><canvas role="img" aria-label="Timeline of when each satellite is above the horizon of Porto, Moscow and the third station"></canvas></div>
    </figure>

    <figure class="pg-panel ob-energy">
      <figcaption class="pg-head"><span class="pg-title">Energy error</span><span class="pg-key"><span class="tex" data-tex="|E - E_0| / |E_0|">|E − E₀| / |E₀|</span></span></figcaption>
      <div class="pg-stage"><canvas role="img" aria-label="Relative energy error of every body against time, on a log scale"></canvas><div class="pg-tip" hidden></div></div>
    </figure>
  </div>

  <section class="pg-panel ob-details" data-mode="earth" aria-label="The satellites and the stations">
    <h2>The satellites and the stations</h2>
    <div class="table-wrap ob-table-sats"></div>
    <div class="table-wrap ob-table-stations"></div>
    <p class="pg-caption">Elements of the Molniya orbit from Kidder and Vonder Haar (1990) and the NASA orbit catalogue; the semi-major axes follow from the periods by Kepler's third law with GM = 398,600.4418 km³/s² (IERS Conventions 2010). The Earth is a sphere of radius 6,378.137 km turning once a sidereal day; the Greenwich meridian lies along the inertial <i>x</i> axis at <i>t</i> = 0. Visibility uses the geometric horizon, an elevation above 0 degrees.</p>
  </section>
  <section class="pg-panel ob-details" data-mode="galaxy" aria-label="The stars and the potential">
    <h2>The six stars</h2>
    <div class="table-wrap ob-table-stars"></div>
    <p class="pg-caption">Catalogue values from <em>Gaia</em> DR3 at epoch J2016.0, with their published uncertainties; distances are 1 / parallax. Galactocentric coordinates with the Sun at (−8.0, 0, 0.0208) kpc moving at (11.10, 232.24, 7.25) km/s; their uncertainties are standard deviations over 20,000 draws from the Gaia errors and correlations. The reference eccentricity, <span class="tex" data-tex="z_\mathrm{max}"><i>z</i><sub>max</sub></span>, pericentre and apocentre come from a 10 Gyr galpy integration of the same starting point, for comparison with the live values.</p>
    <h2>The potential</h2>
    <div class="table-wrap ob-table-potential"></div>
    <p class="pg-caption">MWPotential2014 (Bovy 2015). Each component is scaled so that its share of the radial force at <i>R</i> = 8 kpc in the plane is the fraction listed; the shares sum to one, so the circular speed there is 220 km/s. The masses are what these scalings imply.</p>
  </section>
  <noscript><p class="pg-state">The playground needs JavaScript. The numbers it uses are in the data file linked below.</p></noscript>
</section>

<details class="pg-more">
  <summary>What you are looking at</summary>
  <div class="prose">
    <p>In Earth mode the view shows three Molniya satellites and one geostationary satellite around the turning Earth, to scale. A Molniya orbit has a semi-major axis of 26,562 km, an eccentricity of 0.74, an inclination of 63.4 degrees and its perigee at the southernmost point of the orbit, so each pass takes half a sidereal day and the satellite spends about two thirds of it high over the northern hemisphere. The three orbital planes are 120 degrees apart and the satellites are timed so that one of them is always near apogee above the same longitude, here Moscow's. The geostationary satellite circles 35,786 km above the equator at longitude 0, in step with the ground.</p>
    <p>The timeline fills in whenever a satellite is above a station's horizon. The test is the elevation angle, the angle between the line from the station to the satellite and the station's horizontal plane, <span class="tex" data-tex="\sin\varepsilon = (\mathbf{r} - \mathbf{s}) \cdot \hat{\mathbf{s}} \,/\, |\mathbf{r} - \mathbf{s}|">sin ε = (r − s) · ŝ / |r − s|</span>, positive when the satellite is above it. Porto and Moscow always have at least one Molniya satellite above the horizon. The third station can be moved between 60 and 90 degrees north; the geostationary satellite drops below its horizon at 81.3 degrees, where the line of sight grazes the Earth, while the Molniya satellites remain in view.</p>
    <p>The integrator menu switches between three ways of stepping the same equations. The leapfrog kicks the velocity by half a step, drifts the position by a full step and kicks again, <span class="tex tex-display" data-tex="\mathbf{v}_{n+\frac12} = \mathbf{v}_n + \tfrac{h}{2}\,\mathbf{a}(\mathbf{x}_n), \quad \mathbf{x}_{n+1} = \mathbf{x}_n + h\,\mathbf{v}_{n+\frac12}, \quad \mathbf{v}_{n+1} = \mathbf{v}_{n+\frac12} + \tfrac{h}{2}\,\mathbf{a}(\mathbf{x}_{n+1})">v(n+1/2) = v(n) + (h/2) a(x(n)), x(n+1) = x(n) + h v(n+1/2), v(n+1) = v(n+1/2) + (h/2) a(x(n+1))</span> which is symplectic: its energy error oscillates over each orbit and does not grow. The fourth-order Runge-Kutta scheme compares one step with two half steps and shrinks or grows the step to keep the difference below a tolerance of one part in <span class="tex" data-tex="10^{10}">10¹⁰</span>; it is far more accurate per step, so its error starts lower, but it drifts in one direction over long runs. The coursework scheme advances the position to second order and the velocity by an explicit Euler step, <span class="tex tex-display" data-tex="\mathbf{x}_{n+1} = \mathbf{x}_n + h\,\mathbf{v}_n + \tfrac{h^2}{2}\,\mathbf{a}(\mathbf{x}_n), \quad \mathbf{v}_{n+1} = \mathbf{v}_n + h\,\mathbf{a}(\mathbf{x}_n)">x(n+1) = x(n) + h v(n) + (h²/2) a(x(n)), v(n+1) = v(n) + h a(x(n))</span> and its energy climbs at every perigee pass, so a Molniya orbit widens within a day. The energy panel plots <span class="tex" data-tex="|E - E_0| / |E_0|">|E − E₀| / |E₀|</span> for every body on a log scale, the followed body drawn thicker, with <span class="tex" data-tex="E = \tfrac12 v^2 - GM/r">E = v²/2 − GM/r</span> around the Earth and <span class="tex" data-tex="E = \tfrac12 v^2 + \Phi(R, z)">E = v²/2 + Φ(R, z)</span> in the Galaxy.</p>
    <p>In Galaxy mode the same code integrates six stars in MWPotential2014 (Bovy 2015): a power-law bulge with an exponential cut-off, a Miyamoto and Nagai disc, <span class="tex" data-tex="\Phi_\mathrm{d} = -GM_\mathrm{d} \big/ \sqrt{R^2 + \big(a + \sqrt{z^2 + b^2}\big)^2}">Φ_d = −GM_d / sqrt(R² + (a + sqrt(z² + b²))²)</span>, and a Navarro, Frenk and White halo, scaled so that the circular speed at the Sun's radius of 8 kpc is 220 km/s. Each star starts from its <em>Gaia</em> DR3 position, parallax, proper motion and radial velocity, converted to Galactocentric coordinates with astropy. The main view looks down from the north Galactic pole, where the disc turns clockwise and the dashed ring is the Sun's circle; the side panel plots the distance from the axis against the height above the plane, the plane in which the orbit is a filled band rather than a line.</p>
    <p>The readouts give four numbers for the followed star. The eccentricity, <span class="tex" data-tex="e = (R_\mathrm{apo} - R_\mathrm{peri}) / (R_\mathrm{apo} + R_\mathrm{peri})"><i>e</i> = (R_apo − R_peri) / (R_apo + R_peri)</span>, comes from the smallest and largest distances from the Galactic centre reached so far, <span class="tex" data-tex="z_\mathrm{max}"><i>z</i><sub>max</sub></span> is the largest height reached so far, <i>E</i> is the energy and <span class="tex" data-tex="L_z = R\,v_\phi"><i>L</i><sub>z</sub> = R v_φ</span> is the vertical component of the angular momentum, positive for stars that turn with the disc. Both settle once the star has completed a radial and a vertical oscillation, and the small print beneath each gives the value from a 10 Gyr galpy integration. In my research these are the quantities that separate the thin disc, on near-circular orbits that stay within a few hundred parsecs of the plane, from the thick disc, on hotter orbits reaching a kiloparsec or more, and from the halo, on eccentric orbits with slow or reversed rotation; <a href="{{ '/software/starfold-demo/' | relative_url }}">the Starfold demo</a> uses the same ones for 9,242 stars. Kapteyn's star and HD 140283 have negative <span class="tex" data-tex="L_z"><i>L</i><sub>z</sub></span>: they orbit against the disc's rotation.</p>
    <p>The test particle starts on the Sun's side of the Galaxy at the chosen distance from the axis and height, with the chosen radial (outward positive), azimuthal (positive with the disc) and vertical velocities; the defaults put it on the circular orbit at the Sun's radius. It is a test particle, not a star. Run advances the clock at the chosen speed, Step takes one integration step and Reset returns every body to its starting point. The adaptive RK4 treats the step as its ceiling and reports the step it is using. The leapfrog also conserves <span class="tex" data-tex="L_z"><i>L</i><sub>z</sub></span> to rounding error in this axisymmetric model, because each kick lies in the plane through the axis.</p>
  </div>
</details>

<section class="prose pg-credits" aria-labelledby="origin">
  <h2 id="origin">Where it came from</h2>
  <p>This page is rebuilt from project 3 of the Computational Astronomy course at the University of Porto (2018/19): an N-body code that I applied to a Molniya constellation and a geostationary satellite, with signal reception at Porto, Moscow and a point at 80 degrees north. That code stepped the velocity with an explicit Euler update and held the Earth still, so a ground station never moved under the satellites. This version keeps that scheme for comparison and adds the symplectic leapfrog and an adaptive RK4, a turning Earth with visibility from the elevation angle, the live energy error, and the Galaxy mode, in which the same integrators follow real stars through a model of the Milky Way.</p>
</section>

<section class="prose pg-credits" aria-labelledby="credits">
  <h2 id="credits">Data and credits</h2>
  <p>The Molniya eccentricity of 0.74 and inclination of 63.4 degrees are the values of <a href="https://doi.org/10.1175/1520-0426(1990)007%3C0517:OTUOSI%3E2.0.CO;2">Kidder and Vonder Haar (1990, J. Atmos. Oceanic Technol. 7, 517)</a>; NASA's <a href="https://science.nasa.gov/earth/earth-observatory/catalog-of-earth-satellite-orbits">Catalog of Earth Satellite Orbits</a> gives 63.4 degrees, a 12 hour period and 0.722 for the same orbit type, and real Molniya satellites fell between the two. The period is half a sidereal day, and the semi-major axis follows from Kepler's third law with GM = 398,600.4418 km³/s² (IERS Conventions 2010, Table 1.1), which with the geostationary period gives a radius of 42,164 km, the figure NASA quotes, and an altitude of 35,786 km, the figure on ESA's <a href="https://www.esa.int/Enabling_Support/Space_Transportation/Types_of_orbits">Types of orbits</a> page. The Earth's radius of 6,378.137 km and its rotation come from the <a href="https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html">NSSDC Earth fact sheet</a> and the IERS conventions.</p>
  <p>The Milky Way model is MWPotential2014 of <a href="https://doi.org/10.1088/0067-0049/216/2/29">Bovy (2015, ApJS 216, 29)</a>: a bulge with density falling as <i>r</i><sup>−1.8</sup> and cut off at 1.9 kpc, a <a href="https://ui.adsabs.harvard.edu/abs/1975PASJ...27..533M">Miyamoto and Nagai (1975)</a> disc with scale length 3 kpc and scale height 0.28 kpc, and a <a href="https://doi.org/10.1086/304888">Navarro, Frenk and White (1997)</a> halo with scale radius 16 kpc, contributing 5, 60 and 35 percent of the radial force at 8 kpc, where the circular speed is 220 km/s. The page's potential was checked against galpy's at ten points to one part in <span class="tex" data-tex="10^{12}">10¹²</span>. The Sun sits 20.8 pc above the plane (<a href="https://doi.org/10.1093/mnras/sty2813">Bennett and Bovy 2019</a>) and moves at (11.10, 12.24, 7.25) km/s relative to the local circular orbit (<a href="https://doi.org/10.1111/j.1365-2966.2010.16253.x">Schönrich, Binney and Dehnen 2010</a>).</p>
  <p>The six stars are <em>Gaia</em> DR3 sources with a radial velocity, chosen to span the disc and the halo: 61 Virginis, Proxima Centauri, Barnard's star, Lalande 21185, Kapteyn's star and HD 140283. Arcturus and Alpha Centauri, the obvious bright examples, are brighter than the <em>Gaia</em> DR3 limit and have no entry, and tau Ceti and epsilon Eridani have no DR3 radial velocity. Names were resolved through <a href="https://doi.org/10.1051/aas:2000332">SIMBAD</a>. This page uses data from the European Space Agency mission <em>Gaia</em> (<a href="https://doi.org/10.1051/0004-6361/202243940">Gaia Collaboration, Vallenari et al. 2023, A&amp;A 674, A1</a>), processed by the <em>Gaia</em> Data Processing and Analysis Consortium (DPAC); the astrometry is described by <a href="https://doi.org/10.1051/0004-6361/202039709">Lindegren et al. (2021, A&amp;A 649, A2)</a> and the radial velocities by <a href="https://doi.org/10.1051/0004-6361/202244220">Katz et al. (2023, A&amp;A 674, A5)</a>. <em>Gaia</em> data are © ESA/Gaia/DPAC and released under <a href="https://creativecommons.org/licenses/by-sa/3.0/igo/">CC BY-SA 3.0 IGO</a>, and the derived file below is shared under the same licence.</p>
  <p>Download the <a href="{{ '/assets/data/playground/orbits.json' | relative_url }}">data</a> (15 KB) and its <a href="{{ '/assets/data/playground/orbits.meta.json' | relative_url }}">provenance</a>, which records the queries, their dates, the candidates set aside and why, and the galpy cross-checks. The integration runs in your browser, and nothing you do here is sent anywhere.</p>
</section>
</div>
<script src="{{ '/assets/js/tokens.js' | relative_url }}" defer></script>
<script type="module" src="{{ '/assets/js/playground/orbits-playground.js' | relative_url }}"></script>
