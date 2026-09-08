---
title: Projects
nav:
  order: 2
  tooltip: Software, datasets, and more
---

# {% include icon.html icon="fa-solid fa-wrench" %}Projects

Projects and Publications- Coming Soon!

{% include tags.html tags="publication, resource, website" %}

{% include search-info.html %}

{% include section.html %}

## Featured

{% include list.html component="card" data="projects" filter="group == 'featured'" %}

{% include section.html %}

## More

{% include list.html component="card" data="projects" filter="group != 'featured' and group != 'previous'" style="small" %}

{% include section.html %}

## Previous Projects

{% include list.html component="card" data="projects" filter="group == 'previous'" style="small" %}
