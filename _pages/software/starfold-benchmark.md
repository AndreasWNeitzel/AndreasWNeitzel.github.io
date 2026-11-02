---
layout: page
permalink: /software/starfold-benchmark/
crumb: {label: Software, url: /software/}
title: Starfold held-out benchmark
nav_section: Software
description: Per-table results of Starfold 0.2.0 against the library defaults on ten tables with known classes.
extra_css: [/assets/css/starfold-bench.css]
lede: Starfold 0.2.0 was tested on ten tables with known classes and lost to the library defaults on two of the four held-out tables.
---
<div class="row">
  <div class="prose">
    <p>Starfold chooses UMAP and HDBSCAN settings without labels and reports how far its groups can be trusted. The benchmark checks whether the chosen setting recovers known classes better than the library defaults. Six development tables informed the selection rules, and four held-out tables were not used until the rules were fixed.</p>
    <p>Recovery is the adjusted Rand index (floored at zero) against the true classes on the assigned rows, times the share of rows assigned. The defaults score is the median over eight seeds, and a difference below 0.02 counts as a match. Starfold matched or beat the defaults on 6 of 6 development tables and on 2 of 4 held-out tables, losing on COIL-20 and Isolet.</p>
  </div>
</div>
<section class="row" aria-labelledby="table">
  <h2 id="table">Results per table</h2>
  <div class="table-wrap">
    <table>
      <thead>
        <tr><th scope="col">Table</th><th scope="col">Set</th><th scope="col">Rows</th><th scope="col">Features</th><th scope="col">Classes</th><th scope="col">Starfold</th><th scope="col">Defaults</th><th scope="col">Result</th></tr>
      </thead>
      <tbody>
        {%- for r in site.data.starfold_benchmark %}
        <tr><th scope="row">{{ r.table }}</th><td>{{ r.set }}</td><td>{{ r.n_rows | delimit }}</td><td>{{ r.n_features | delimit }}</td><td>{{ r.n_classes }}</td><td>{{ r.starfold_recovery | append: "000" | slice: 0, 5 }}</td><td>{{ r.defaults_recovery | append: "000" | slice: 0, 5 }}</td><td>{{ r.result }}</td></tr>
        {%- endfor %}
      </tbody>
    </table>
  </div>
  <p class="meta">Recorded at tag v0.2.0 (commit f93dea0) in <code>bench/results/summary.json</code>. The <a href="{{ '/assets/data/starfold_benchmark.csv' | relative_url }}">CSV</a> lists each table's source, and the <a href="{{ '/assets/data/starfold_benchmark.json' | relative_url }}">provenance</a> record is in JSON.</p>
</section>
<section class="row" aria-labelledby="figures">
  <h2 id="figures">Figures</h2>
  <figure class="figure sfb-figure" data-credit="own">
    {% include figures/starfold-resolution.svg %}
    <figcaption>Starfold gains most where the classes are large compared with the finest structure its graph can resolve. Left, recovery minus default recovery; right, correlation of the label-free score with recovery. Data: <a href="{{ '/assets/data/starfold/benchmark/resolution.json' | relative_url }}">resolution.json</a>.</figcaption>
  </figure>
  <figure class="figure sfb-figure" data-credit="own">
    {% include figures/starfold-injection.svg %}
    <figcaption>Groups smaller than the resolution scale are not found; those found stay pure as the support threshold rises. A method check on synthetic groups injected into a real table and never kept. Data: <a href="{{ '/assets/data/starfold/benchmark/injection.json' | relative_url }}">injection.json</a>, <a href="{{ '/assets/data/starfold/benchmark/provenance.json' | relative_url }}">provenance</a>.</figcaption>
  </figure>
</section>
