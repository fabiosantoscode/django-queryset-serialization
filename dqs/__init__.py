'''
Basic Usage:
    
from dqs import dqs

serializer = dqs.make_serializer(person__name__icontains='$param')
#notice the '$param' tag.

dqs.register('people-search', serializer, Person.objects.all())

(...)

from dqs import dqs

dqs['people-search'].get_queryset({'$param':'a'})
#returns a queryset of people with names with "a" in them.
'''

