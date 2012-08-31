import json

from django.test import TestCase
from django.db import models

from dqs.utils import *
import serialization


GENDER_VALUES={'male':1,'female':2}
GENDER_CHOICES = GENDER_VALUES.items()

class Person(models.Model):
    gender = models.SmallIntegerField(choices=GENDER_CHOICES, null=True)
    name = models.CharField(max_length=150, null=True)
    best_friend = models.ForeignKey('Person', related_name='best_friend_of', unique=True, null=True)
    friends = models.ManyToManyField('Person', null=True)



class BasicTests(TestCase):
    def setUp(self):
        self.dqs = serialization.DjangoQuerysetSerialization()

    def test_new_serializer(self):
        this_model_should_be_found = Person(
            gender=GENDER_VALUES['male'],
            name='Gibberish Betty Sun The Third')
        
        this_model_should_be_found.save()
        
        serializer = (self.dqs.make_serializer()
            .filter(name__icontains='$a.placeholder')
            .filter(name__icontains='Betty')
            .all())
        
        self.dqs.register('name2', serializer, Person.objects.all())
        
        qs = self.dqs['name2'].get_queryset({
            'a.placeholder':'Gibberish'})
        
        self.assertTrue(this_model_should_be_found in qs)
        
        
        serializer = (self.dqs.make_serializer()
            .filter(__configurable_filter='$a.placeholder')
            .filter(name__icontains='Betty')
            .all())
        
        self.dqs.register('name1', serializer, Person.objects.all())
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
        qs = Person.objects.all()
        Person(name='excludeme',
            gender=GENDER_VALUES['male']).save()
        
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
        p = Person(name='Person with a $weird name',
            gender=GENDER_VALUES['male'])
        
        p.save()
        
        qs = self.dqs.register('escaping-test',
            self.dqs.make_serializer().filter(name__icontains='$$weird'),
            Person.objects.all()).get_queryset()
        
        self.assertTrue(p in qs)
    
    def test_pass_advanced(self):
        '''
        test that we can pass more than strings as parameters, even though the placeholder itself is a string
        '''
        examplea = Person(name='examplea',
            gender=GENDER_VALUES['male'])
        examplea.save()
        
        example = Person(name='example',
            gender=GENDER_VALUES['male'])
        example.save()
        
        examplette = Person(name='examplette',
            gender=GENDER_VALUES['female'])
        examplette.save()
        
        qs = self.dqs.register('name', self.dqs.make_serializer()
                .filter(name__in='$name'),
            Person.objects.all())
        
        find_examplette = qs.get_queryset({
            'name':['examplette']})
        
        find_everyone_else = qs.get_queryset({
            'name':['example', 'examplette']})
        
        self.assertTrue(examplette in find_examplette)
        self.assertTrue(examplea not in find_everyone_else)
    
    def test_m2m_support(self):
        pass #TODO
    
    def test_util_functions(self):
        self.assertTrue(not is_string_placeholder('something'))
        self.assertTrue(not is_string_placeholder('$$something'))
        self.assertTrue(is_string_placeholder('$something'))

        self.assertTrue(is_kwarg_key_placeholder('__sthSth_'))
        self.assertTrue(not is_kwarg_key_placeholder('__sth-sth'))
        self.assertTrue(not is_kwarg_key_placeholder('____sthsth'))

        self.assertEqual(clean_placeholder('$placeholder'),'placeholder')
        self.assertEqual(unescape_non_placeholder('$$placeholder'),'$placeholder')

    
    def test_parameters_as_lists(self):
        s=self.dqs.register('passing-lists-params',
            self.dqs.make_serializer().filter(gender='$gender'),
            Person.objects.all())
        
        queryset = (self.dqs['passing-lists-params']
            .from_iterable_parameters([GENDER_VALUES['male']]))
        
        self.assertEqual(queryset.all().count(),0)
        
        p1 = Person(name='someone',
            gender=GENDER_VALUES['male'])
        p2 = Person(name='someoneelse',
            gender=GENDER_VALUES['female'])
        
        p1.save()
        p2.save()
        
        self.assertEqual(queryset.all().count(), 1)
        
        self.assertTrue(p1 in queryset.all())
        self.assertTrue(p2 not in queryset.all())
    
    def test_escaping_interchangeable(self):
        '''test that users can still use `$names-like-these` in their
        parameters dictionary keys, although the requirement is
        actually that they pass `names-like-these`, without $ or __
        '''
        
        s = self.dqs.register('names',
            self.dqs.make_serializer().filter(gender='$gender'),
            Person.objects.all())
        
        male_gender = GENDER_VALUES['male']
        
        Person(name='someone',
            gender=male_gender).save()
        
        for paramss in [{'$gender':male_gender},
                {'gender':male_gender}]:
            qs = s.get_queryset(paramss)
            self.assertTrue(len(qs) == 1)
    
    def test_reduce_name_collisions(self):
        '''
        Avoid name collisions with dictionary keys, since it could
        happen that .filter(gender='$gender') will cause a name
        collision when unserializing.
        
        This will not mean that the user will have to pass in the
        unescaped parameters. We must be wary that it is not always
        the user who gives the parameters, cleanly through a dict.
        '__' and '$' are not very good to have spread about an URL, 
        for example.
        
        The avoidance is achieved through storing the serializer's
        kwargs (both keys and values), and args, unchanged, and then
        checking if they are placeholders using the utility
        funcs _is_siphon_placeholder and is_underscore_placeholder 
        together. This means that unescaping of escaped values must 
        also happen, but that is tested in test_placeholder_escaping.
        
        '''
        #print s.serializer._placeholders, s.serializer._stack
        #TODO
    
    def test_from_url(self):
        qs = Person.objects.all()
        Person(name='somename',
            gender=GENDER_VALUES['male']).save()
        
        Person(name='$somename',
            gender=GENDER_VALUES['male']).save()
            
        Person(name='__somename',
            gender=GENDER_VALUES['male']).save()
        
        serializer = self.dqs.make_serializer().filter(name='$name')
        self.dqs.register('urlserialization1', serializer, Person.objects.all())
        
        self.assertEqual(len(self.dqs.from_url('/urlserialization1/somename')),1)
        self.assertEqual(len(self.dqs.from_url('/__somename', 'urlserialization1')),1)
        self.assertEqual(len(self.dqs.from_url('/$somename', 'urlserialization1')),1)
        
        self.assertEqual(len(self.dqs.from_url('/somename', 'urlserialization1')),1)
        
        self.assertEqual(len(self.dqs.from_url('/urlserialization1/wrongname')),0)
        self.assertEqual(len(self.dqs.from_url('/wrongname', 'urlserialization1')),0)
        
        
        
    
    def test_from_request_data(self):
        pass #TODO
    
    def test_from_json(self):
        pass #TODO
    
    def test_forms(self):
        'Test django-queryset-serialization forms and document them'
        
        import dqs.forms
        from django import forms
        
        supposedly_called_functions = set(['clean_field1', '__init__'])
        
        person = Person(name='name')
        person.save()
        serializer = (self.dqs.make_serializer()
            .all()
            .filter(name='$field1'))
        self.dqs.register('form-test', serializer, 
            Person.objects)
        
        class DqsForm(dqs.forms.Form):
            serialization = self.dqs['form-test']
            
            field1 = forms.CharField(max_length=13)
        
        form = DqsForm(dict(field1='name'))
        
        self.assertTrue(form.is_valid())
        qs = form.get_queryset()
        
        self.assertTrue(person in qs)
        
        # Test giving it the serialization on __init__
        class DqsForm2(dqs.forms.Form):
            kwargfield = forms.CharField(max_length=8)
        
        serializer = (self.dqs.make_serializer()
            .all()
            .filter(__kwargfield='name'))
        self.dqs.register('form-test2', serializer, 
            Person.objects)
        
        try:
            DqsForm2()
            self.assertFalse('Exception was not raised!')
        except AttributeError:
            pass
        
        form2 = DqsForm2(dict(kwargfield='name'), self.dqs['form-test2'])
        form2.is_valid()
        
        self.assertTrue(person in form2.get_queryset())
    
    def test_model_persistance(self):
        pass #TODO
