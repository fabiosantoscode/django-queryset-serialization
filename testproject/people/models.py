from django.contrib import admin
from django.db import models
from dqs import dqs

# Create your models here.

GENDER_CHOICES = (
    (1,'male'),
    (2,'female')
)
GENDER_VALUES = dict([(v,k) for k,v in GENDER_CHOICES])
class Person(models.Model):
    class Meta:
        verbose_name_plural = 'people'
    gender = models.SmallIntegerField(choices=GENDER_CHOICES)
    name = models.CharField(max_length=150)
    
    def __unicode__(self):
        name, lim = self.name, 40
        return '%s (...)' % name[:lim] if len(name) > lim else name
admin.site.register(Person)


