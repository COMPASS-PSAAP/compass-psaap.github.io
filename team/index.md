---
title: Team
nav:
  order: 3
  tooltip: About our team
---

# {% include icon.html icon="fa-solid fa-users" %}Team

We have a growing team consisting of six Principal Investigators, two Full Time Research Scientists, and five PhD Students. Take a look at their profiles to learn more about their objectives, work, publications, and research interests!
{% include section.html background="images/background.jpg" dark=true %}

Principal Investigators

{% include section.html %}

{% include section.html %}

{% include list.html data="members" component="portrait" filter="role == 'programmer'" %}

{% include section.html background="images/background.jpg" dark=true %}

{% include section.html background="images/background.jpg" dark=true %}

<h2> <strong> Staff Researchers </strong> </h2>
{% include section.html %}

{% include section.html %}

{% include list.html data="members" component="portrait" filter="role != 'programmer'" %}

{% include section.html background="images/background.jpg" dark=true %}

Posts Here ?????

{% include section.html %}

{% capture content %}

{% include figure.html image="images/photo.jpg" %}
{% include figure.html image="images/photo.jpg" %}
{% include figure.html image="images/photo.jpg" %}

{% endcapture %}

{% include grid.html style="square" content=content %}
