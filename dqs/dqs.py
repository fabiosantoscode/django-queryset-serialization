from itertools import izip, count
from functools import update_wrapper, partial
import json
import warnings
from functools import update_wrapper
import inspect



class DjangoQuerysetSerializationException(Exception):
    pass

class SerializationNotRegistered(DjangoQuerysetSerializationException):
    pass

class BadSerializationFormat(DjangoQuerysetSerializationException):
    pass



class Serialization(object):
    class SerializationStep(object):
        def __init__(self, fname, function, index, **arguments):    
            self._index = index
            self._fname = fname
            self._function = function
            self._arguments = arguments
        
        def apply_to(self, queryset):
            return self._function.__call__(queryset, **self._arguments)
        
        def __repr__(self):
            return "<SerializationStep: Function %d: %s(**%s)>" % (
                self._index, self._fname, self._arguments)
    
    def __init__(self, name, queryset=None):
        self.name=name
        self._steps=[]
        self._queryset = queryset
    
    def add_step(self, fname, function, **arguments):
        self._steps.append(Serialization.SerializationStep(
                fname, function, len(self._steps), **arguments))
    
    def get_queryset(self, queryset=None):
        queryset = queryset if queryset is not None else self._queryset
        for step in self._steps:
            # Apply all serialization functions to the queryset
            queryset = step.apply_to(queryset)
        return queryset



dqs_methods = [] #shortcuts to the class methods
def shortcut_decorator(f):
    '''
    add f to a list of django-queryset-serialization shortcut methods,
    which won't need to be called upon the DjangoQuerysetSerialization
    instance.
    '''
    
    global dqs_methods
    def wrapper(*args, **kwargs):
        #dqs is the queen instance of DjangoQuerysetSerialization
        return f(dqs, *args, **kwargs)
    
    dqs_methods.append(update_wrapper(wrapper, f))
    
    return f #so this is a decorator and really isn't a decorator.



class DjangoQuerysetSerialization(dict):
    '''
    Subclass of dict
    
    
    Internal description:
    Contains tuples of (base queryset, function stack), known as
    "serializations". Function stacks are tuples of (function
    __name__, function, index). These functions are then called by
    django-queryset-serialization one by one to create the output
    querysets.
    
    The keys of this dictionary are the names of those serializations.
    
    '''
    
    @shortcut_decorator
    def get_function_stack(self, name):
        try:
            return self[name][1]
        except KeyError:
            raise SerializationNotRegistered
    
    @shortcut_decorator
    def get_base_queryset(self, name):
        try:
            return self[name][0]
        except KeyError:
            raise SerializationNotRegistered
    
    @shortcut_decorator
    def register(self, queryset, stackname, *functions):
        function_stack = []
        for function, index in izip(functions, count()):
            function_stack.append((function.__name__, function, index))
        
        self[stackname] = queryset, function_stack
    
    @shortcut_decorator
    def from_dict(self, d):
        function_stack = self.get_function_stack(d['name'])
        queryset = self.get_base_queryset(d['name'])
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
    
    @shortcut_decorator
    def from_json(self, j):
        return self.from_dict(json.loads(j))
    
    @shortcut_decorator
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
        
        url = url.lstrip('/').rstrip('/')
        
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
                raise BadSerializationFormat('expected "-function" or'\
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
    
    @shortcut_decorator
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
            raise BadSerializationFormat
        
        prefix = prefix or request_data.get('prefix','')
        
        function_stack = self.get_function_stack(name)
        queryset = self.get_base_queryset(name)
        
        serialization = Serialization(name, queryset)
        
        for fname, func, index in function_stack:
            argument_prefix = ('%s_' % prefix) if prefix else ''
            arguments = {}
            for argname in inspect.getargspec(func)[0]:
                if argument_prefix + argname in request_data:
                    arguments[argname] = request_data[argname]
            serialization.add_step(fname, func, **arguments)
        
        return serialization



try:
    this_module
except NameError:
    dqs = DjangoQuerysetSerialization()
    
    'Add every method in the list'
    import dqs as this_module
    for method in dqs_methods:
        setattr(this_module, method.__name__, method)
    
    setattr(this_module, 'this_module', 'Was already imported')
