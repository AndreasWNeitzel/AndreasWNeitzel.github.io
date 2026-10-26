---
layout: page
permalink: /software/starfold-demo/
math: true
crumb: {label: Software, url: /software/}
title: Starfold on 9,242 Milky Way stars
nav_section: Software
description: A recorded Starfold run on 9,242 APOGEE DR19 stars with Gaia DR3 orbits, with the map it cut, the chemistry and orbit planes, every star's record across the 32 refits and the warnings the run raised.
lede: Starfold split 9,242 Milky Way stars into two groups without labels, and the group medians lie on the disc's two chemical sequences.
extra_css: [/assets/css/starfold-demo.css]
---
<div class="sfd-page">

<section class="sfd" id="sf-demo" aria-label="Recorded Starfold run" data-header="{{ '/assets/data/starfold/apogee_run.json' | relative_url }}">
  <div class="sfd-dash">
    <div class="sfd-ctrl">
      <section class="sfd-panel sfd-verdict" aria-labelledby="sfd-verdict-title">
        <h2 class="sfd-title" id="sfd-verdict-title">What the run reports</h2>
        <dl class="sfd-readout">
          <div><dt>Groups</dt><dd>2</dd></div>
          <div><dt>Recurrence</dt><dd>0.91<span class="sfd-and">and</span>0.92</dd></div>
          <div><dt>Unassigned</dt><dd>1,068</dd></div>
          <div><dt>Unresolved</dt><dd>0.154</dd></div>
        </dl>
        <div class="sfd-calib">
          <p class="sfd-label">Calibration test</p>
          <div class="sfd-calib-plot"></div>
          <p class="sfd-small">p = 0.10: 1 of 19 structureless copies of the table scored at or above it.</p>
        </div>
        <div class="sfd-flags">
          <p class="sfd-label">Flags raised</p>
          <details><summary>search_budget_exhausted</summary><p>the search used every trial; a larger n_trials may help</p></details>
          <details><summary>consensus_subsampled</summary><p>the co-association check ran on a seeded subset of stars</p></details>
          <details><summary>consensus_disagrees</summary><p>the cut of the co-association matrix agrees with the partition below 0.5</p></details>
          <details><summary>null_not_run</summary><p>no calibration test ran, so there is no p-value; run starfold.null_test</p></details>
        </div>
      </section>

      <section class="sfd-panel sfd-settings" aria-label="Colours and selection">
        <label class="sfd-field"><span class="sfd-label">Colour the stars by</span><span class="sfd-select"><select class="sfd-colour" disabled>
          <option value="fit" selected>Groups in the fit on all stars</option>
          <option value="refit">Groups in one refit</option>
          <option value="col:0">[Fe/H]</option>
          <option value="col:1">[α/M]</option>
          <option value="col:2">[Mg/Fe]</option>
          <option value="col:3">Radial action</option>
          <option value="col:4">Vertical action</option>
          <option value="col:5">Angular momentum</option>
          <option value="col:6">Eccentricity</option>
          <option value="col:7">Orbital energy</option>
        </select></span></label>
        <div class="sfd-key" role="group" aria-label="Key to the colours"></div>
        <p class="sfd-sel" hidden><span class="sfd-sel-text"></span> <button type="button" class="sfd-link sfd-clear">Clear</button></p>
        <p class="sfd-state" aria-live="polite">Loading 9,242 stars (0.7 MB).</p>
      </section>
    </div>

    <figure class="sfd-panel panel sfd-plot sfd-map">
      <figcaption class="sfd-head"><span class="sfd-title">Map of the stars</span><span class="sfd-note">9,242 stars</span></figcaption>
      <div class="sfd-stage"><canvas role="img" aria-label="Map of 9,242 stars in two coloured groups with unassigned stars between them"></canvas><div class="sfd-tip" hidden></div></div>
      <p class="sfd-cap">Similar stars sit close together. <span class="sfd-exact">The UMAP map of the eight standardised columns that HDBSCAN cut; its axes have no units.</span></p>
    </figure>

    <figure class="sfd-panel sfd-plot sfd-chem">
      <figcaption class="sfd-head"><span class="sfd-title">Chemistry</span><span class="sfd-seg" role="group" aria-label="Vertical axis"><button type="button" aria-pressed="true" data-y="1">[α/M]</button><button type="button" aria-pressed="false" data-y="2">[Mg/Fe]</button></span></figcaption>
      <div class="sfd-stage"><canvas role="img" aria-label="Alpha-element abundance against iron abundance for every star, coloured as the map"></canvas><div class="sfd-tip" hidden></div></div>
      <p class="sfd-cap">Alpha elements against iron, where the disc has two sequences. <span class="sfd-exact">ASPCAP <span class="sfd-chem-y">[α/M]</span> and [Fe/H] from APOGEE DR19 in dex; rings mark the group medians.</span></p>
    </figure>

    <figure class="sfd-panel sfd-plot sfd-orbit">
      <figcaption class="sfd-head"><span class="sfd-title">Orbits</span><span class="sfd-seg" role="group" aria-label="Orbital quantities"><button type="button" aria-pressed="true" data-orbit="el"><i>E</i>, <span class="tex" data-tex="L_z"><i>L</i><sub>z</sub></span></button><button type="button" aria-pressed="false" data-orbit="j"><span class="tex" data-tex="J_\mathrm{R}"><i>J</i><sub>R</sub></span>, <span class="tex" data-tex="J_z"><i>J</i><sub>z</sub></span></button></span></figcaption>
      <div class="sfd-stage"><canvas role="img" aria-label="Orbital energy against angular momentum for every star, coloured as the map"></canvas><div class="sfd-tip" hidden></div></div>
      <p class="sfd-cap"><span class="sfd-orbit-plain">How bound each orbit is, against how much it turns with the disc.</span> <span class="sfd-exact sfd-orbit-exact"><i>E</i> and <span class="tex" data-tex="L_z"><i>L</i><sub>z</sub></span> from galpy orbits in the McMillan17 potential; rings mark the group medians.</span></p>
    </figure>

    <section class="sfd-panel sfd-replay" aria-labelledby="sfd-replay-title">
      <div class="sfd-head"><h2 class="sfd-title" id="sfd-replay-title">The 32 refits</h2><span class="sfd-note sfd-refit-now">showing the fit on all stars</span></div>
      <div class="sfd-buttons">
        <button type="button" class="btn btn--primary btn--sm sfd-play" disabled>Replay</button>
        <button type="button" class="btn btn--sm sfd-prev" aria-label="Previous refit" disabled>&lsaquo;</button>
        <button type="button" class="btn btn--sm sfd-next" aria-label="Next refit" disabled>&rsaquo;</button>
        <button type="button" class="btn btn--sm sfd-back" disabled>All stars</button>
      </div>
      <div class="sfd-strip" role="group" aria-label="The refits, by agreement with the fit on all stars"></div>
      <p class="sfd-small sfd-refit-text">Each bar is a refit on a random 80 percent of the stars, as tall as its agreement with the fit on all stars.</p>
    </section>

    <section class="sfd-panel sfd-star" aria-labelledby="sfd-star-title">
      <div class="sfd-head">
        <h2 class="sfd-title" id="sfd-star-title">Star</h2>
        <div class="sfd-tools">
          <span class="sfd-select sfd-select--sm"><select class="sfd-pick" aria-label="Star to inspect" disabled><option>Loading</option></select></span>
          <form class="sfd-find" autocomplete="off"><input type="text" inputmode="numeric" spellcheck="false" placeholder="Gaia DR3 source_id" aria-label="Find a star by its Gaia DR3 source_id" disabled><button type="submit" class="btn btn--sm" disabled>Find</button></form>
        </div>
      </div>
      <p class="sfd-facts">Hover over a star in any panel.</p>
      <div class="sfd-history"><div class="sfd-cells" aria-hidden="true"></div><p class="sfd-small sfd-history-text"></p></div>
      <dl class="sfd-feats"></dl>
    </section>
  </div>
  <noscript><p class="sfd-state">The panels need JavaScript. The run's numbers are in the tables below.</p></noscript>
</section>

<section class="sfd-numbers" aria-labelledby="numbers">
  <h2 id="numbers">The run in numbers</h2>
  <p class="sfd-intro">The recorded run of Starfold 0.2.0 on the APOGEE DR19 example table: a search over 48 settings, one fit on all stars, then 32 refits on random 80 percent subsets.</p>
  <div class="sfd-tables">
    <figure class="sfd-table">
      <figcaption>The two groups in measured units. Each cell is the median over the 32 refits of the group's median, with its 5 to 95 percent range over the refits in brackets, beside the median of all stars.</figcaption>
      <div class="table-wrap"><table>
        <thead><tr><th scope="col">Column</th><th scope="col">Group 0, 1,588 stars</th><th scope="col">Group 1, 6,586 stars</th><th scope="col">All stars</th></tr></thead>
        <tbody>
<tr><th scope="row">[Fe/H] <small>dex</small></th><td>−0.416 <small>(−0.424 to −0.405)</small></td><td>−0.076 <small>(−0.080 to −0.071)</small></td><td>−0.138</td></tr>
<tr><th scope="row">[α/M] <small>dex</small></th><td>0.222 <small>(0.221 to 0.224)</small></td><td>0.026 <small>(0.025 to 0.027)</small></td><td>0.045</td></tr>
<tr><th scope="row">[Mg/Fe] <small>dex</small></th><td>0.273 <small>(0.271 to 0.275)</small></td><td>0.040 <small>(0.039 to 0.042)</small></td><td>0.062</td></tr>
<tr><th scope="row"><span class="tex" data-tex="J_\mathrm{R}"><i>J</i><sub>R</sub></span> <small>kpc km/s</small></th><td>79.3 <small>(76 to 82.2)</small></td><td>23.4 <small>(23 to 23.8)</small></td><td>29.4</td></tr>
<tr><th scope="row"><span class="tex" data-tex="J_z"><i>J</i><sub>z</sub></span> <small>kpc km/s</small></th><td>32.6 <small>(31.4 to 33.7)</small></td><td>8.55 <small>(8.36 to 8.66)</small></td><td>11.3</td></tr>
<tr><th scope="row"><span class="tex" data-tex="L_z"><i>L</i><sub>z</sub></span> <small>kpc km/s</small></th><td>1,474 <small>(1,464 to 1,485)</small></td><td>1,926 <small>(1,922 to 1,935)</small></td><td>1,857</td></tr>
<tr><th scope="row">eccentricity</th><td>0.260 <small>(0.254 to 0.265)</small></td><td>0.130 <small>(0.128 to 0.131)</small></td><td>0.148</td></tr>
<tr><th scope="row"><i>E</i> <small>km²/s²</small></th><td>−163,784 <small>(−164,177 to −163,230)</small></td><td>−154,301 <small>(−154,408 to −154,095)</small></td><td>−155,907</td></tr>
        </tbody>
      </table></div>
    </figure>
    <figure class="sfd-table">
      <figcaption>The setting the search chose, on the 80 percent subsets it was scored on and scaled up for the fit on all stars, beside the library defaults.</figcaption>
      <div class="table-wrap"><table>
        <thead><tr><th scope="col">Setting</th><th scope="col">Subsets</th><th scope="col">All stars</th><th scope="col">Defaults</th></tr></thead>
        <tbody>
<tr><th scope="row"><code>n_neighbors</code></th><td>54</td><td>54</td><td>15</td></tr>
<tr><th scope="row"><code>min_dist</code></th><td>0.289</td><td>0.289</td><td>0.1</td></tr>
<tr><th scope="row"><code>n_components</code></th><td>2</td><td>2</td><td>2</td></tr>
<tr><th scope="row"><code>min_cluster_size</code></th><td>72</td><td>90</td><td>5</td></tr>
<tr><th scope="row"><code>min_samples</code></th><td>24</td><td>30</td><td>5</td></tr>
<tr><th scope="row"><code>selection_method</code></th><td>eom</td><td>eom</td><td>eom</td></tr>
        </tbody>
      </table></div>
      <ul class="sfd-list">
        <li>The search ran 48 trials, 39 to the end and 9 pruned, and selected trial 45.</li>
        <li>Fresh gap over three structureless copies: 0.372 for the selected setting and −0.001 for the defaults.</li>
        <li>One fit of the defaults on all stars found 326 groups and left 3,553 stars unassigned.</li>
        <li>Two groups in 31 refits and three in refit 10; agreement with the fit on all stars from 0.68 to 0.88.</li>
        <li>Co-association on a seeded subset of 4,096 stars: within 0.979, between 0.003, contrast 0.976. The cut of that matrix left all of them unassigned (agreement 0.000).</li>
        <li>334 fits in 163 s on a laptop RTX 3060 with RAPIDS cuML, random_state 0.</li>
      </ul>
    </figure>
  </div>
</section>

<details class="sfd-more">
  <summary>What you are looking at</summary>
  <div class="prose">
    <p>Each star carries eight numbers. [Fe/H] is its iron abundance relative to the Sun, in dex, a base-10 logarithm, and [α/M] and [Mg/Fe] say how rich it is in alpha elements such as magnesium; all three come from APOGEE spectra through the ASPCAP pipeline. The other five describe its orbit, integrated with galpy in the McMillan17 model of the Galaxy from <em>Gaia</em> DR3 astrometry: the radial and vertical actions <span class="tex" data-tex="J_\mathrm{R}"><i>J</i><sub>R</sub></span> and <span class="tex" data-tex="J_z"><i>J</i><sub>z</sub></span>, the angular momentum <span class="tex" data-tex="L_z"><i>L</i><sub>z</sub></span>, the eccentricity and the energy <i>E</i>.</p>
    <p>Starfold tried 48 settings of UMAP and HDBSCAN, scored each without labels against a structureless copy of the table, and fitted the selected one on all stars. The map shows that fit. UMAP placed the stars so that neighbours in the eight standardised columns stay close, and HDBSCAN marked the two dense regions as groups and left 1,068 stars around and between them unassigned. Positions on the map have no units; only which stars sit near which counts.</p>
    <p>The chemistry panel is the classic test. The Milky Way disc holds two chemical sequences: a high-alpha one of older, metal-poorer stars on hotter orbits, and a low-alpha one that reaches solar [Fe/H] and above (<a href="https://doi.org/10.1051/0004-6361/201322631">Bensby et al. 2014</a>; <a href="https://doi.org/10.1088/0004-637X/808/2/132">Hayden et al. 2015</a>). Starfold was told none of this. Group 0 has the high-alpha pattern and group 1 the reverse, in chemistry and in orbits. That passes a sanity check of the method; it is not a finding about the Galaxy.</p>
    <p>To see how far the split holds, Starfold refitted the same setting 32 times, each on a random 80 percent of the stars with new seeds. A star's support for a group is the share of its refit group that belongs to that group, averaged over the refits that drew it, and dots fade where support for their own group is low. Refit groups carry arbitrary numbers, so the replay colours each one by the group it matches by Jaccard index, as Starfold does for recurrence.</p>
    <p>Recurrence is that matched overlap, averaged over the refits: 0.914 for group 0 and 0.918 for group 1, both above the 0.85 that the <a href="https://rdrr.io/cran/fpc/man/clusterboot.html">clusterboot documentation</a> gives for a highly stable cluster. Refit 10 found a third group of 124 stars, 119 of them from group 1; the other 31 refits found two, so the count interval is 2 to 2. The unresolved mass, 0.154, is the average share of a star's refit outcomes that were no group.</p>
    <p>The co-association contrast measures how much more often the refits put two stars of one group together than two stars of different groups; on a seeded subset of 4,096 stars it is 0.976. A second clustering of that matrix left every one of those stars unassigned and raised <code>consensus_disagrees</code>; the tutorial records its cause as not diagnosed. The calibration test ran separately on the same run: one of 19 structureless copies scored at or above the table, so p = 0.10, with a 95 percent Monte Carlo interval of 0.001 to 0.260.</p>
    <p>So the run supports two reproducible groups, and no more. With p above 0.05 the split is not shown to exceed a single correlated population, and attaching the test to the saved run would add the flag <code>no_structure_supported</code>. The run gives no membership probabilities, models no selection function and carries no measurement errors. The table's provenance note calls it a convenience for tutorials, not a source for scientific work.</p>
    <p>The star panel follows the star under the pointer, or the one you clicked or chose. Its 32 cells are the refits in order: a coloured cell means the refit put the star with that group, an outline means it left the star unassigned, and a dot means it did not draw the star. Each line below spans the 1st to 99th percentile of all stars, the ticks mark the two group medians and the dot marks the star; a square means the star lies beyond the line. The source_id links to the star's row in the <em>Gaia</em> DR3 catalogue at VizieR.</p>
    <p>Hover over a star to read it in the star panel, click to keep it, and drag across any panel to select a set of stars, which the other panels then show. Replay steps through the refits, cross-fading between them unless your device asks for reduced motion. On ten labelled tables Starfold matched or beat the library defaults on six of six development tables and on two of four held-out ones; <a href="{{ '/software/starfold-benchmark/' | relative_url }}">the benchmark</a> lists every table.</p>
  </div>
</details>

<section class="prose sfd-credits" aria-labelledby="credits">
  <h2 id="credits">Data and credits</h2>
  <p>The 9,242 stars are the APOGEE DR19 example table that ships with the Starfold repository: stars with a spectrum signal-to-noise ratio above 70 and both ASPCAP chemistry and a galpy orbit. The chemistry comes from APOGEE in <a href="https://www.sdss.org/dr19/">SDSS-V Data Release 19</a> (<a href="https://arxiv.org/abs/2507.07093">SDSS Collaboration 2025</a>; <a href="https://doi.org/10.3847/1538-3881/ade4b9">Meszaros et al. 2025, AJ 170, 96</a>), measured with the ASPCAP pipeline (<a href="https://doi.org/10.3847/1538-4365/ac4414">Abdurro'uf et al. 2022, ApJS 259, 35</a>).</p>
  <p>The orbits were integrated with galpy (<a href="https://doi.org/10.1088/0067-0049/216/2/29">Bovy 2015, ApJS 216, 29</a>) in the McMillan17 potential (<a href="https://doi.org/10.1093/mnras/stw2759">McMillan 2017, MNRAS 465, 76</a>) from the astrometry of the European Space Agency mission <em>Gaia</em> (<a href="https://doi.org/10.1051/0004-6361/202243940">Gaia Collaboration, Vallenari et al. 2023, A&amp;A 674, A1</a>), processed by the <em>Gaia</em> Data Processing and Analysis Consortium (DPAC). <em>Gaia</em> data are © ESA/Gaia/DPAC and released under <a href="https://creativecommons.org/licenses/by-sa/3.0/igo/">CC BY-SA 3.0 IGO</a>, and the derived files below are shared under the same licence.</p>
  <p>Starfold builds on UMAP (<a href="https://arxiv.org/abs/1802.03426">McInnes, Healy and Melville 2018</a>), HDBSCAN (<a href="https://doi.org/10.1007/978-3-642-37456-2_14">Campello, Moulavi and Sander 2013</a>) and Optuna (<a href="https://arxiv.org/abs/1907.10902">Akiba et al. 2019</a>). Its <a href="https://github.com/AndreasWNeitzel/starfold">code</a> is MIT-licensed, and the <a href="https://andreaswneitzel.github.io/Starfold/tutorial/apogee.html">APOGEE tutorial</a> in its manual reads this run step by step.</p>
  <p>Download the <a href="{{ '/assets/data/starfold/apogee_run.bin' | relative_url }}">data</a> (0.7 MB), its <a href="{{ '/assets/data/starfold/apogee_run.json' | relative_url }}">header</a> and its <a href="{{ '/assets/data/starfold/apogee_run.meta.json' | relative_url }}">provenance</a>, which records the checksums of the run, the table and the calibration record, the Starfold version and commit, and the seed. I recomputed the map with the call the tutorial notebook uses, and it gives back the recorded groups exactly. Everything runs in your browser, and nothing you do here is sent anywhere.</p>
</section>
</div>
<script src="{{ '/assets/js/tokens.js' | relative_url }}" defer></script>
<script type="module" src="{{ '/assets/js/starfold-demo.js' | relative_url }}"></script>
