import json
from django.test import TestCase
import dqs
    
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
        
    

