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
            .filter(name__icontains='Betty')
            .all())
        
        self.dqs.register('name2', serializer, models.Person.objects.all())
        
        qs = self.dqs['name2'].get_queryset({
            'a.placeholder':'Gibberish'})
        
        self.assertTrue(this_model_should_be_found in qs)
        
        
        serializer = (self.dqs.make_serializer()
            .filter(__configurable_filter='$a.placeholder')
            .filter(name__icontains='Betty')
            .all())
        
        self.dqs.register('name1', serializer, models.Person.objects.all())
        self.assertTrue(len(serializer._stack) == 3)
        
        qs = self.dqs['name1'].get_queryset({
            'configurable_filter':'name__icontains',
            'a.placeholder':'Gibberish'})
        
        self.assertTrue(this_model_should_be_found in qs)
        
    def test_new_serializer_unicode(self):
        pass #TODO
    
    def test_new_serializer_serialization(self):
        '''
        test using serializers after themselves being serialized,
        together with their parameters, and then unserialized and
        used.
        '''
        
        #TODO Add serialization capabilities to the serializers
    
    def test_serializers_can_have_their_parameters_changed(self):
        '''
        test the interface with which one can change a serializer's
        parameters programatically.
        '''
        
    
    def test_serializers_are_immutable(self):
        '''
        Assert that serializers are immutable.
        '''
        print 'test_serializers_are_immutabel'
        qs = models.Person.objects.all()
        models.Person(name='excludeme',
            gender=models.GENDER_VALUES['male']).save()
        
        serializer = self.dqs.make_serializer()
        serializer2 = serializer.all()
        self.assertTrue(serializer is not serializer2)
        
        name = 'testing_immutable'
        self.dqs.register(name, serializer, qs)
        
        self.assertTrue(self.dqs[name].get_queryset().count() == 1)
        serializer = (serializer
            .filter(name__icontains='this-string-not-in-name'))
        'Still the same result, even though the serializer changed'
        self.assertTrue(self.dqs[name].get_queryset().count() == 1)
        
        
        
    def test_placeholder_escaping(self):
        p = models.Person(name='Person with a $weird name',
            gender=models.GENDER_VALUES['male'])
        
        p.save()
        
        qs = self.dqs.register('escaping-test',
            self.dqs.make_serializer().filter(name__icontains='$$weird'),
            models.Person.objects.all()).get_queryset()
        
        self.assertTrue(p in qs)
    
    def test_pass_advanced(self):
        return #TODO
        #the __in lookup is not working for some reason...
        '''
        test that we can pass more than strings as parameters, even though the placeholder itself is a string
        '''
        models.Person(name='example',
            gender=models.GENDER_VALUES['male']).save()
        
        example = models.Person(name='example',
            gender=models.GENDER_VALUES['male'])
        example.save()
        
        examplette = models.Person(name='examplette',
            gender=models.GENDER_VALUES['female'])
        examplette.save()
        
        queryset = self.dqs.register('passing-lists',
            self.dqs.make_serializer().filter(gender__in='$gender'),
            models.Person.objects.all()
            ).get_queryset({'gender':[models.GENDER_VALUES['male']]})
        
        self.assertTrue(example in queryset)
        self.assertFalse(examplette not in queryset)
    
    def test_m2m_support(self):
        pass
    
    def test_parameters_as_lists(self):
        return #TODO
        queryset = self.dqs.register('passing-lists',
            self.dqs.make_serializer().filter(gender__eq='$gender'),
            models.Person.objects.all()
            ).get_queryset([models.GENDER_VALUES['male']])
        
        queryset2 = queryset.all() #a copy
        
        self.assertEqual(queryset.all().count(),0)
        
        models.Person(name='someone',
            gender=models.GENDER_VALUES['male']).save()
        models.Person(name='someoneelse',
            gender=models.GENDER_VALUES['female']).save()
        
        self.assertEqual(queryset.all().count(), 1)
    
