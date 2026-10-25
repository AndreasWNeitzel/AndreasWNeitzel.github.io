---
layout: page
permalink: /software/starfold-demo/
title: Starfold on handwritten digits
nav_section: Software
description: A recorded Starfold run on 1,797 handwritten digits, with every digit inspectable and the 32 refits replayable.
lede: Starfold sorted 1,797 handwritten digits into 10 groups without seeing the labels, while one run of the library defaults found 51.
---
<div class="row">
  <div class="prose">
    <p>Each point is one digit from the scikit-learn digits table. Hovering over a point shows its digit. When the 32 refits on random subsets are replayed, the points Starfold marks as uncertain flicker.</p>
    <p class="meta">Recorded run of Starfold 0.2.0 (commit f93dea0) on the 1,797-row, 64-feature digits table. Optuna chose the UMAP and HDBSCAN settings without labels, and that setting was refit on 32 random 80 percent subsets. Each point is faded by the share of refits in which it kept its group, and 30 rows are unassigned. The run raised the flags search_budget_exhausted, count_unstable and consensus_disagrees. The map axes have no meaning.</p>
  </div>
</div>
<section class="row" aria-labelledby="demo">
  <h2 id="demo">The recorded run</h2>
  <div id="sf-demo" class="sf-demo" data-src="{{ '/assets/data/starfold_digits_demo.json' | relative_url }}">
    <p class="sf-status muted">Not loaded yet.</p>
    <p class="no-print"><button type="button" class="button sf-load">Load the recorded run (0.5 MB)</button></p>
    <div class="sf-figure">
      <canvas class="sf-map" role="img" aria-label="Map of 1,797 handwritten digits coloured by group"></canvas>
      <div class="sf-tip" hidden><canvas width="96" height="96" aria-hidden="true"></canvas><p></p></div>
    </div>
    <noscript>
      <img src="{{ '/assets/figures/starfold/digits_groups.png' | relative_url }}" width="1600" height="928" alt="Map of 1,797 handwritten digits in ten coloured groups, each group labelled with one of its handwritten digits.">
    </noscript>
    <div class="sf-controls" hidden>
      <fieldset class="sf-modes">
        <legend>Colour the points by</legend>
        <label><input type="radio" name="sf-mode" value="truth"> the written digit (never shown to Starfold)</label>
        <label><input type="radio" name="sf-mode" value="starfold" checked> the 10 Starfold groups, faded where refits disagree</label>
        <label><input type="radio" name="sf-mode" value="defaults"> the 51 groups from one run of the library defaults</label>
      </fieldset>
      <div class="sf-replay">
        <label>Refit <input type="range" class="sf-refit" min="0" max="31" value="0" step="1"> <span class="sf-refit-label">Refit 1 of 32</span></label>
        <button type="button" class="button sf-play">Replay the refits</button>
      </div>
      <div class="table-wrap">
        <table class="sf-groups">
          <thead><tr><th scope="col">Group</th><th scope="col">Digits</th><th scope="col">Recurs in</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
  </div>
  <p class="meta">Download the <a href="{{ '/assets/data/starfold_digits_demo.json' | relative_url }}">recorded run</a> and its <a href="{{ '/assets/data/starfold_digits_demo.meta.json' | relative_url }}">provenance</a>. The digits come from scikit-learn (BSD-3-Clause), a copy of the UCI Optical Recognition of Handwritten Digits test set (CC BY 4.0).</p>
</section>
<section class="row" aria-labelledby="examples">
  <h2 id="examples">Selected examples from the benchmark</h2>
  <div class="prose">
    <p>Recovery of the known classes (adjusted Rand index times the share of rows assigned), Starfold against the library defaults, on five tables picked to show the range. Over all 10 tables Starfold matched or beat the defaults on 8 and lost on 2 of the 4 held-out ones. <a href="{{ '/software/starfold-benchmark/' | relative_url }}">The full benchmark</a> lists every table.</p>
    <ul class="list">
      <li>Rice grains, 0.29 against 0.01</li>
      <li>Landsat satellite pixels, 0.35 against 0.05</li>
      <li>Handwritten digits, 0.74 against 0.64</li>
      <li>Pen strokes, 0.82 against 0.75</li>
      <li>Dry beans, 0.50 against 0.45</li>
    </ul>
  </div>
</section>
<script src="{{ '/assets/js/tokens.js' | relative_url }}" defer></script>
<script src="{{ '/assets/js/starfold-demo.js' | relative_url }}" defer></script>
