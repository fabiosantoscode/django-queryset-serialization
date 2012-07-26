import json
from django.test import TestCase
import dqs
import models
    
class BasicTests(TestCase):
    def setUp(self):
        self.dqs = dqs.DjangoQuerysetSerialization()
        
    def test_function_chain(self):
        """
        In this test we make sure that the chain of functions are
        called, with the correct arguments.
        
        We make a chain of functions that add their arguments to
        a list, as well as some random stuff, then we make sure all
        the arguments and random stuffs are there.
        """
        
        "there she is, our list"
        qs = []
        
        def clearfunction(qs):
            qs.append(qs)
            return qs
        
        def functionsomewhere(qs,phoenix, another):
            qs+=[phoenix,another]
            return qs
            
        def otherfunction(qs):
            qs.append('otherfunctioncalled')
            return qs
        
        def finalfunction(qs, page):
            qs.append(int(page))
            return qs
        
        #register the functions into the DQS stack. Called in order.
        self.dqs.register(qs,'some_serialization_i_registered',
            clearfunction,
            functionsomewhere,
            otherfunction,
            finalfunction)
        
        self.assertEqual(len(self.dqs), 1)
        
        #add a dqs dict structure. could come from json.
        d = {
            'name':'some_serialization_i_registered',
            'stack':[
                {
                    'name':'functionsomewhere',
                    'args':{
                        'phoenix':'iamargument',
                        'another':'asdgu'
                    }
                },{
                    'name':'finalfunction',
                    'args':{
                        'page':'10'
                    }
                }
            ]
        }
        
        j = json.dumps(d)
        
        url = 'some_serialization_i_registered/-functionsomewhere/'\
            'phoenix-iamargument/another-asdgu/-finalfunction/page-10'
        
        serializations = [
            ('json', self.dqs.from_json(j)),
            ('dict', self.dqs.from_dict(d)),
            ('url', self.dqs.from_url(url)),
        ]
        
        for name, serialization in serializations:
            print 'testing result of %s serialization' % name
            qs = serialization.get_queryset()
            
            self.assertIn('some_serialization_i_registered', self.dqs)
            
            self.assertIn(qs, qs)
            self.assertIn('iamargument', qs)
            self.assertIn(10, qs)
            self.assertIn('otherfunctioncalled', qs)
            
            self.assertEqual(len(self.dqs), 1)
            
            qs = []
        
    def test_new_serializer(self):
        this_model_should_be_found = models.Person(
            gender=models.GENDER_VALUES['male'],
            name='Gibberish Betty Sun The Third'
        )
        
        this_model_should_be_found.save()
        
        serializer = dqs.dqs.register_chainable(
            models.Person.objects.all(), '155')
        serializer = serializer.filter(name__icontains='$a.parameter'
            ).all()
        
        assert len(serializer._stack) == 2
        
        serializer2 =dqs.dqs.register_chainable(
            models.Person.objects.all(), '214')
        serializer2 = serializer2.filter(__something_to_filter='Sun'
            ).all()
        
        assert len(serializer2._stack) == 2
        
        serializer3 =dqs.dqs.register_chainable(
            models.Person.objects.all(), '123')
        serializer3 = serializer3.filter(__something_to_filter='$parm'
            ).all()
        
        assert len(serializer3._stack) == 2
        
        qs1 = serializer.get_queryset({'$a.parameter':'Gibberish'})
        qs2 = serializer2.get_queryset({
                '__something_to_filter':'name__icontains'})
        qs3 = serializer3.get_queryset({
                '__something_to_filter':'name__iendswith',
                '$parm':'The Third'})
        
        assert (this_model_should_be_found in qs1)
        assert (this_model_should_be_found in qs2)
        assert (this_model_should_be_found in qs3)
        
    def test_new_serializer_unicode(self):
        pass #TODO
    
    def test_new_serializer_serialization(self):
        test1 = models.Person(
            gender=models.GENDER_VALUES['male'],
            name='Some name and a [tag]')
        #test2 = models.Person(
        #    gender=models.GENDER_VALUES['female'],
        #    name='Some namette and a [tag]')
        
        test1.save()
        #test2.save()
        
        queryset1 = models.Person.objects.all()
        #queryset2 = queryset1
        
        name1 = 'NAME1'
        #name2 = 'NAME2'
        
        serialized1 = (dqs.dqs.register_chainable(queryset1, name1)
            .all()
            .all()
            .filter(name__contains='[tag]')
            .filter(name__contains='tte') #only found in one model.
            .to_json())
        
        #serialized2 = (dqs.dqs.register_chainable(queryset2, name2)
        #    .all()
        #    .filter(name__icontains='[tag]')
        #    .exclude(name__icontains='profanity(!)')
        #    .to_url())
        
        assert name1 in dqs.dqs
        #assert name2 in dqs.dqs
        
        
