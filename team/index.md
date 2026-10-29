---
title: Team
nav:
  order: 4
  tooltip: About our team
---

# {% include icon.html icon="fa-solid fa-users" %}Team

Our team brings together faculty, research scientists, students, and staff from the University of New Mexico, Tennessee Tech University, the University of Alabama, and the University of California, Davis. Take a look at their profiles to learn more about their objectives, work, publications, and research interests!
{% include section.html background="images/site/background.jpg" dark=true %}

<h2> <strong> Principal Investigators </strong> </h2> 

{% include section.html %}

{% include section.html %}

{% include list.html data="members" component="portrait" filter="role == 'principal-investigator'" %}

{% include section.html background="images/site/background.jpg" dark=true %}

{% include section.html background="images/site/background.jpg" dark=true %}

<h2> <strong> Staff Researchers </strong> </h2>
{% include section.html %}

{% include section.html %}

{% include list.html data="members" component="portrait" filter="role == 'programmer'" %}

{% include section.html background="images/site/background.jpg" dark=true %}

<h2> <strong> Student Researchers </strong> </h2>
{% include section.html %}

{% include section.html %}

{% include list.html data="members" component="portrait" filter="role == 'student'" %}

{% include section.html background="images/site/background.jpg" dark=true %}

<h2> <strong> Administrative Staff </strong> </h2>
{% include section.html %}

{% include section.html %}

{% include list.html data="members" component="portrait" filter="role == 'admin'" %}

{% include section.html background="images/site/background.jpg" dark=true %}

<h2> <strong> Former Members & Alumni </strong> </h2>
{% include section.html %}

{% include section.html %}

{% include list.html data="members" component="portrait" filter="role == 'past-member'" %}
