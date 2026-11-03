---
layout: page
permalink: /credits/
title: Credits
copy: credits
extra_css:
  - /assets/css/credits.css
---
{%- assign CP = site.data.copy.credits -%}
{%- assign mail = site.data.person.emails.academic -%}
{%- assign slot = "{" | append: "email}" -%}
{%- capture maillink %}<a href="mailto:{{ mail }}">{{ mail }}</a>{% endcapture -%}
<div class="cr-terms">
  <section><h2>My work</h2><p>{{ CP.own }} {{ CP.mockups }}</p></section>
  <section><h2>Photographs</h2><p>{{ CP.pictures }}</p></section>
  <section><h2>Reuse</h2><p>{{ CP.reuse | replace: slot, maillink }}</p></section>
</div>
<section class="section section--tight" aria-labelledby="others">
  <div class="section-head"><h2 id="others">Other people's work</h2><p>{{ CP.thirdparty }}</p></div>
  {%- for g in site.data.credits.groups %}
  <div class="cr-group" id="{{ g.id }}">
    <h3>{{ g.title }}</h3>
    <table class="cr-table">
      <thead><tr><th scope="col">What</th><th scope="col">Credit</th><th scope="col">Licence</th></tr></thead>
      <tbody>
        {%- for r in g.items %}
        <tr><th scope="row">{% if r.link != "" %}<a href="{{ r.link }}">{{ r.what | missions }}</a>{% else %}{{ r.what | missions }}{% endif %}</th><td>{{ r.credit }}</td><td>{{ r.licence }}</td></tr>
        {%- endfor %}
      </tbody>
    </table>
  </div>
  {%- endfor %}
</section>
