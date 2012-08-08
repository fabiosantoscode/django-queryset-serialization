'''
Basic Usage:

#serialization.py
from dqs import serialization

serializer = dqs.make_serializer().filter(person__name__icontains='$param')
#notice the '$param' tag.

serialization.dqs.register('people-search', serializer, Person.objects)

#views.py
from dqs import serialization
(...)
serialization.dqs['people-search'].get_queryset({'$param':'a'})
#returns Person.objects.filter(person__name__icontains='a')
'''

