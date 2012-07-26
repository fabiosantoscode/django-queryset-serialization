import json
from django.test import TestCase
import dqs
import models
    
class BasicTests(TestCase):
    def setUp(self):
        self.dqs = dqs.DjangoQuerysetSerialization()

    def test_new_serializer(self):
        this_model_should_be_found = models.Person(
            gender=models.GENDER_VALUES['male'],
            name='Gibberish Betty Sun The Third'
        )
        
        this_model_should_be_found.save()
        
        serializer = (self.dqs.make_serializer()
            .filter(name__icontains='$a.placeholder')
            .all())
        
        self.dqs.register('name1', serializer, models.Person.objects.all())
        assert len(serializer._stack) == 2
        
        qs = self.dqs['name1'].get_queryset({'$a.placeholder':'Gibberish'})
        
        assert (this_model_should_be_found in qs)
        
    def test_new_serializer_unicode(self):
        pass #TODO
    
    def test_new_serializer_serialization(self):
        '''
        test using serializers after themselves being serialized and
        unserialized
        '''
        
        #TODO Add serialization capabilities to the serializers
    
    def test_serializers_are_immutable(self):
        #TODO
        pass
