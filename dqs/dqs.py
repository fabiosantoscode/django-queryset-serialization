from itertools import izip, count
from functools import update_wrapper, partial
import json
import warnings
import inspect



class DjangoQuerysetSerializationException(Exception):
    pass
dqse = DjangoQuerysetSerializationException



class SerializationNotRegistered(dqse):
    pass



class BadSerializationFormat(dqse):
    pass



class Serialization(object):
    class SerializationStep(object):
        def __init__(self, fname, function, index, **arguments):    
            self._index = index
            self._fname = fname
            self._function = function
            self._arguments = arguments
        
        def step(self, queryset):
            return self._function.__call__(queryset, **self._arguments)
    
    def __init__(self, name, queryset):
        self.name=name
        self._steps=[]
        self._queryset = queryset
    
    def add_step(self, fname, function, **arguments):
        self._steps.append(Serialization.SerializationStep(
                fname, function, len(self._steps), **arguments))
    
    def get_queryset(self, queryset=None):
        queryset = queryset if queryset is not None else self._queryset
        for step in self._steps:
            queryset = step.step(queryset)
        return queryset
    
    def _f(self, fname, *args, **kwargs):
        qs = self.get_queryset()
        f = getattr(qs,fname)
        f(qs,*args,**kwargs)
    
for fname in ('get','filter','all','exclude','order_by'):
    setattr(Serialization,fname,partial(Serialization._f,fname=fname))


class DjangoQuerysetSerialization(dict):
    '''
    
    '''
    
    def _get_function_stack(self, name):
        try:
            return self[name][1]
        except KeyError:
            raise SerializationNotRegistered
    
    def _get_queryset(self, name):
        try:
            return self[name][0]
        except KeyError:
            raise SerializationNotRegistered
    
    
    def register(self, queryset, stackname, *functions):
        function_stack = []
        for function, index in izip(functions, count()):
            function_stack.append((function.__name__, function, index))
        
        self[stackname] = queryset, function_stack
    
    def from_dict(self, d):
        function_stack = self._get_function_stack(d['name'])
        queryset = self._get_queryset(d['name'])
        argument_stack = d['stack']
        
        serialization = Serialization(d['name'], queryset)
        
        iter_argstack = iter(argument_stack)
        last_arg = None
        for fname, func, index in function_stack:
            call_args = {}
            try:
                if not last_arg:
                    last_arg = iter_argstack.next()
                
                if last_arg['name'] == fname:
                    call_args = last_arg.get('args',{})
                    last_arg = None
                else:
                    "last_arg remains the same for the next iteration"
            except StopIteration:
                pass
            serialization.add_step(fname, func, **call_args)
        
        return serialization
    
    def from_json(self, j):
        return self.from_dict(json.loads(j))
    
    def from_url(self, url):
        warnings.warn('TODO: URL DECODE')
        
        url = url.lstrip('/')
        components = iter(url.split('/'))
        
        try:
            name = components.next()
        except StopIteration:
            raise BadSerializationFormat
        
        function_stack = self._get_function_stack(name)
        queryset = self._get_queryset(name)
        
        def get_functions():
            for fname, func, index in function_stack:
                argspec = inspect.getargspec(func)[0]
                return fname, argspec, len(argspec)
        
        
        result_stack = [] # going to be a list of dicts
        
        last_fname = ''
        last_urlcomponent = ''
        for function_name,arguments,argument_count in get_functions():
            fname = components.pop()
            if function_name == fname:
                function_call_details = {'name':fname, 'args':{}}
                for argname in arguments:
                    '''at this point, we have key/value pairs
                    expressed in the URL. Odd-indexed values
                    are keys, even-indexed values are the
                    values. We have to extract an argument, then a 
                    value, then iterate again.'''
                    try:
                        if argname == components_next():
                            function_call_details['args'][argname
                                ] = components.next()
                        else:
                            raise BadSerializationFormat
                    except StopIteration:
                        raise BadSerializationFormat
                result_stack += [function_call_details]
            else:
                raise BadSerializationFormat
            
        d = {
            'name' : name,
            'stack' : result_stack
        }
        return self.from_dict(d)

dqs = DjangoQuerysetSerialization()

if __name__ == '__main__':
    l = []
    qs = object()
    
    def clearfunction(qs):
        print 'asd1'
        global l
        l.append(qs)
    
    def functionsomewhere(qs,penis, another):
        print 'asd'
        global l
        l+=[penis,another]
        
    def otherfunction(qs):
        global l
        print 'asdadsas'
        l+=['otherfunctioncalled']
    
    def finalfunction(qs, page):
        global l
        print 'finalfunction'
        l+=[int(page)]
    
    #register the functions into the DQS stack. Called in order.
    dqs.register(qs,'some_serialization_i_registered', clearfunction, functionsomewhere, otherfunction, finalfunction)
    
    assert len(dqs) == 1
    
    #add a dqs dict structure. could come from json.
    d = json.dumps({
        'name':'some_serialization_i_registered',
        'stack':[
            {
                'name':'functionsomewhere',
                'args':{
                    'penis':'iamargument',
                    'another':'asdgu'
                }
            }
        ]
    })
    
    url = 'some_serialization_i_registered/functionsomewhere/penis/iamargument/another/asdgu/finalfunction/page/10'
    
    #serialization = dqs.from_json(d)
    #serialization = dqs.from_dict(d)
    serialization = dqs.from_url(url)
    
    serialization.get_queryset()
    
    assert 'some_serialization_i_registered' in dqs
    assert 'iamargument' in l
    assert 'asdgu' in l
    assert 'otherfunctioncalled' in l
    assert qs in l
    assert 10 in l
    
    assert len(dqs)==1


