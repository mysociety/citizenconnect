from django.db import models
from django.contrib.gis.db import models as geomodels

class Place(geomodels.Model):

    # Name is shorter and should be used when searching.
    name = models.CharField(max_length=250)

    # Longer name, eg: "High Street, Putney" that can be displayed to user.
    context_name = models.CharField(max_length=250)

    # Where is the center of this place. Might not be very accurate.
    centre = geomodels.PointField()

    # Where did this entry come from?
    SOURCE_OS_LOCATOR = 1
    SOURCE_OS_50K_GAZETEER = 2
    SOURCE_CHOICES = (
        (SOURCE_OS_LOCATOR, 'OS Locator'),
        (SOURCE_OS_50K_GAZETEER, 'OS 1:50k Gazetteer'),
    )
    source = models.IntegerField(choices=SOURCE_CHOICES)

    objects = geomodels.GeoManager()
