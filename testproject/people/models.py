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

'''
Searches

'''

def exclude_john(qs):
    return qs.exclude(name__istartswith='john')

def exclude_nancy(qs):
    return qs.exclude(name__istartswith='nancy')

def find_by_name_start(qs, name_start):
    return qs.filter(name__istartswith=name_start)

def females_only(qs):
    return qs.exclude(gender=GENDER_VALUES['male'])

base_qs = Person.objects.all()
males = Person.objects.filter(gender=GENDER_VALUES['male'])

dqs.register(base_qs, 'namestart', find_by_name_start)
dqs.register(males, 'male_namestart', find_by_name_start)
dqs.register(base_qs, 'female_namestart', find_by_name_start, females_only)
dqs.register(base_qs, 'no-common-names', exclude_john, exclude_nancy)

dqs.register(base_qs, 'everyone')

