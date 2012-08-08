from django.contrib import admin
from django.db import models
from dqs.serialization import dqs

# Create your models here.

GENDER_CHOICES = (
    (1,'male'),
    (2,'female')
)
GENDER_VALUES = dict([(v,k) for k,v in GENDER_CHOICES])
class Person(models.Model):
    gender = models.SmallIntegerField(choices=GENDER_CHOICES, null=True)
    name = models.CharField(max_length=150, null=True)
    best_friend = models.ForeignKey('Person', related_name='best_friend_of', unique=True, null=True)
    friends = models.ManyToManyField('Person', null=True)
admin.site.register(Person)



