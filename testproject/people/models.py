from django.db import models
from dqs import dqs

# Create your models here.

GENDER_CHOICES = (
    (1,'male'),
    (2,'female')
)
class Person(models.Model):
    gender = models.SmallIntegerField(choices=GENDER_CHOICES)
    name = models.CharField(max_length=150)
    
    def __unicode__(self):
        n, l=self.name,40
        return '%s (...)' % n[:l] if len(n) > l else n
        


'''
Searches

'''

def find_by_name_start(qs, name_start):
    return qs.filter(name__istartswith=name_start)

qs = People.objects.all()

dqs.register(qs, 'namestart', find_by_name_start)

