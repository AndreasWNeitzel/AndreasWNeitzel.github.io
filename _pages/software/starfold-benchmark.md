---
layout: page
permalink: /software/starfold-benchmark/
title: Starfold held-out benchmark
nav_section: Software
description: Per-table results of Starfold 0.2.0 against the library defaults on ten tables with known classes.
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
        <tr><th scope="row">{{ r.table }}</th><td>{{ r.set }}</td><td>{{ r.n_rows }}</td><td>{{ r.n_features }}</td><td>{{ r.n_classes }}</td><td>{{ r.starfold_recovery }}</td><td>{{ r.defaults_recovery }}</td><td>{{ r.result }}</td></tr>
        {%- endfor %}
      </tbody>
    </table>
  </div>
  <p class="meta">Recorded at tag v0.2.0 (commit f93dea0) in <code>bench/results/summary.json</code>. The <a href="{{ '/assets/data/starfold_benchmark.csv' | relative_url }}">CSV</a> lists each table's source, and the <a href="{{ '/assets/data/starfold_benchmark.json' | relative_url }}">provenance</a> record is in JSON.</p>
</section>
<section class="row" aria-labelledby="figures">
  <h2 id="figures">Figures</h2>
  <figure class="figure">
    <img src="{{ '/assets/figures/starfold/digits_partitions.png' | relative_url }}" width="1639" height="711" alt="Three two-dimensional maps of the digits table: true digits, the ten Starfold groups faded by recurrence, and the fifty-one groups one default fit finds." loading="lazy">
    <figcaption>The scikit-learn digits on a two-dimensional map, coloured by the true digits (left, used only to check the fit), the 10 Starfold groups faded where refits rarely agree (middle), and the 51 groups from one default fit (right).</figcaption>
  </figure>
  <figure class="figure">
    <img src="{{ '/assets/figures/starfold/bench_resolution.png' | relative_url }}" width="2179" height="1028" alt="Recovery gain and score-recovery correlation plotted against class size relative to the modularity resolution scale." loading="lazy">
    <figcaption>Recovery gain, and the correlation of the label-free score with recovery, against class size in units of the modularity resolution scale, about the square root of 15 m rows (dashed line, Fortunato and Barthelemy 2007, <a href="https://doi.org/10.1073/pnas.0605965104">doi:10.1073/pnas.0605965104</a>).</figcaption>
  </figure>
  <figure class="figure">
    <img src="{{ '/assets/figures/starfold/bench_injection.png' | relative_url }}" width="2181" height="1047" alt="Retrieval, purity and completeness of injected groups against their size." loading="lazy">
    <figcaption>Retrieval, purity and completeness of injected groups against their size, in units of the same resolution scale. Each size is a single draw of three sites, so the plot gives only a rough threshold.</figcaption>
  </figure>
</section>
