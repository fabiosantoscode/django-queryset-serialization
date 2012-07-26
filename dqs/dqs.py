from itertools import izip, count
from functools import update_wrapper, partial
import json
import warnings
from functools import update_wrapper
import inspect



class Serialization(object):
    class SerializationStep(object):
        def __init__(self, function, **arguments):
            self._function = function
            self._arguments = arguments
        
        def apply_to(self, queryset):
            return self._function.__call__(queryset, **self._arguments)
    
    def __init__(self, name, queryset=None):
        self.name=name
        self._steps=[]
        self._queryset = queryset
    
    def add_step(self, function, **arguments):
        self._steps.append(Serialization.SerializationStep(
            function, **arguments))
    
    def set_base_queryset(self, queryset):
        self._queryset = queryset
    
    def get_queryset(self, queryset=None):
        for step in self._steps:
            # Apply all serialization functions to the queryset
            queryset = step.apply_to(self._queryset)
        return queryset



class DjangoQuerysetSerialization(dict):
    '''
    Subclass of dict
    
    
    Internal description:
    Contains tuples of (base queryset, function stack), known as
    "serializations". Function stacks are lists of callables.
    These functions are called by SerializationStep instances
    one by one to create the output querysets.
    
    The keys of this dictionary are the names of those serializations.
    
    '''
    
    def get_function_stack(self, name):
        return self[name][1]
    
    def get_base_queryset(self, name):
        return self[name][0]
    
    def register(self, queryset, stackname, *functions):
        function_stack = []
        for function in functions:
            function_stack.append(function)
        
        self[stackname] = queryset, function_stack
    
    def from_dict(self, d):
        function_stack = self.get_function_stack(d['name'])
        queryset = self.get_base_queryset(d['name'])
        argument_stack = d['stack']
        
        serialization = Serialization(d['name'], queryset)
        
        iter_argstack = iter(argument_stack)
        last_arg = None
        for func in function_stack:
            call_args = {}
            try:
                if not last_arg:
                    last_arg = iter_argstack.next()
                
                if last_arg['name'] == func.__name__:
                    call_args = last_arg.get('args',{})
                    last_arg = None
                else:
                    "last_arg remains the same for the next iteration"
            except StopIteration:
                pass
            serialization.add_step(func, **call_args)
        
        return serialization
    
    def from_json(self, j):
        return self.from_dict(json.loads(j))
    
    def from_url(self, url):
        '''
        Unserialize a queryset from an URL. Magic is still done inside
        from_dict.
        Takes an URL and returns the queryset.
        
        Format of the url:
        
        /serializationname/-function1/arg1-val1/arg2-val2/-pag/page-10
        
        first slash is optional
        '''
        warnings.warn('TODO: URL DECODE')
        
        ret = {}
        
        url = url.strip('/')
        
        components = url.split('/')
        
        ret['name'] = components[0]
        
        components = components[1:]
        
        def process_component(component):
            if component.startswith('-'):
                return 'function', component.lstrip('-')
            elif '-' in component:
                s = component.split('-')
                return 'argument', { s[0]: '-'.join(s[1:]) }
            else:
                raise ValueError('expected "-function" or'\
                    ' "argname-argument", got %s' % component)
        
        ret['stack'] = []
        
        for url_component in components:
            component_type, result = process_component(url_component)
            if component_type == 'function':
                ret['stack'].append({
                    'name': result,
                    'args': {}
                })
            if component_type == 'argument':
                ret['stack'][-1]['args'].update(result)
        
        return self.from_dict(ret)
    
    def from_request_data(self, request_data, name='', prefix=''):
        '''
        Unserializes from request data (request.GET, request.POST or
        request.REQUEST)
        
        Params:
        "name" and "prefix" are actually for overriding "name" and
        "prefix" in the request data. "prefix" is optional either way,
        and "name" must be present either in the request data or as
        an argument to this method.
        '''
        
        name = name or request_data.get('name','')
        if not name:
            raise ValueError
        
        prefix = prefix or request_data.get('prefix','')
        
        function_stack = self.get_function_stack(name)
        queryset = self.get_base_queryset(name)
        
        serialization = Serialization(name, queryset)
        
        for func in function_stack:
            fname = func.__name__
            argument_prefix = ('%s_' % prefix) if prefix else ''
            arguments = {}
            for argname in inspect.getargspec(func)[0]:
                if argument_prefix + argname in request_data:
                    arguments[argname] = request_data[argname]
            serialization.add_step(func, **arguments)
        
        return serialization


dqs = DjangoQuerysetSerialization()

def from_request_data(request_data, name='', prefix=''):
    global dqs
    return dqs.from_request_data(request_data, name, prefix)

def from_url(url):
    global dqs
    return dqs.from_url(url)

def from_dict(d):
    global dqs
    return dqs.from_dict(d)
    
def from_json(d):
    global dqs
    return dqs.from_json(d)

def get_base_queryset(name):
    global dqs
    return dqs.get_base_queryset(name)

def register(base_queryset, name, *functions):
    global dqs
    return dqs.register(base_queryset, name, *functions)


