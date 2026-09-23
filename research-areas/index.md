---
title: Research Areas
nav:
  order: 2
  tooltip: How the center's work is organized
---

# {% include icon.html icon="fa-solid fa-diagram-project" %}Research Areas

The center organizes its work into seven areas. Each section below describes an
area, lists the projects working in it, and links to its publications.

{% comment %}
  collect the areas that have something to show, so that both the jump links
  and the sections below skip the ones that are still empty.
{% endcomment %}
{% assign active = "" | split: "," %}
{% for type in site.data.types %}
  {% if type[1].category %}
    {% capture filter %}tags != nil and tags.include?('{{ type[0] }}'){% endcapture %}
    {% assign projects = site.data.projects | data_filter: filter %}
    {% assign citations = site.data.citations | data_filter: filter %}
    {% if projects.size > 0 or citations.size > 0 %}
      {% assign active = active | push: type[0] %}
    {% endif %}
  {% endif %}
{% endfor %}

<div class="tags">
  {%- for slug in active -%}
    <a href="#{{ slug }}" class="tag">{{ site.data.types[slug].name }}</a>
  {%- endfor -%}
</div>

{% for slug in active %}
{% assign category = site.data.types[slug] %}
{% capture filter %}tags != nil and tags.include?('{{ slug }}'){% endcapture %}
{% capture publications %}/research/?search=%22tag: {{ slug }}%22{% endcapture %}
{% assign citations = site.data.citations | data_filter: filter %}

{% include section.html %}

## {% include icon.html icon=category.icon %}{{ category.name }}

{{ category.description }}

{% include list.html data="projects" component="card" style="small" filter=filter tag_link="/projects/" %}

{% if citations.size > 0 %}
{% include button.html icon="fa-solid fa-scroll" text="Publications in this area" link=publications %}
{% endif %}

{% endfor %}
