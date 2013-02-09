from django.db import models

# Create your models here.
class Organisation(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    name = models.TextField(help_text='The name of the organisation')

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "organisations"
