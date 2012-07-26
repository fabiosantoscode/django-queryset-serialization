from itertools import chain
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
        self[stackname] = queryset, list(functions)
    
    def register_chainable(self, queryset, stackname):
        self[stackname] = queryset, []
        return ChainableSerializer(stackname)
    
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

class ChainableSerializer(object):
    global dqs
    dqs_instance = dqs
    
    '''
    A new way to serialize a queryset. You can just create it, and
    use it like you would use a real queryset, except you can save
    them for later execution.
    
    $parameters, or __keyword_arguments may be specified.
    
    Example:
    
    some_queryset = SomeModel.objects.all()
    qs = SerializedQueryset(some_queryset)
    
    qs = qs.exclude(banned=True)
    qs = qs.filter(something__iexact='$parameter1')
    
    qs.get_queryset({'$parameter1':'something'})
    
    NOTE:
     - If you are going to serialize to JSON, any arguments passed to
     the queryset methods must be serializable through JSON.
     - Every parameter must be a string.
    
    '''
    
    def __init__(self, queryset_name):
        self._variables = []
        self._stack = []
        assert queryset_name in dqs
        self._queryset = queryset_name
    
    @classmethod
    def from_dict(cls, d):
        instance = cls.__init__(d['queryset'])
        
        instance._stack = d.get('stack', [])
        instance._variables = d.get('variables', [])
        
        return instance
    
    def to_dict(self):
        return {
            "variables":self._variables,
            "stack":self._stack,
            "queryset":self._queryset
        }
    
    @classmethod
    def from_json(self, data):
        return self.from_dict(json.reads(data))
    
    def to_json(self):
        return json.dumps(self.to_dict())
    
    def get_queryset(self, parameters, override_dqs=None):
        '''
        Get a queryset by executing the operations to the base
        queryset registered in the DjangoQuerysetSerialization
        instance.
        
        Parameters (__customizable_kwarg='$param1','$other-param')
        are looked up internally and replaced with the actual values
        passed in through the argument `parameters`.
        
        '''
        
        dqs = self.dqs_instance or override_dqs
        
        queryset = dqs.get_base_queryset(self._queryset).all()
        
        for operation in self._stack:
            args_raw, kwargs_raw = operation['args'], operation['kwargs']
            
            args, kwargs = [], {}
            for argument in args_raw:
                if argument in self._variables:
                    argument = parameters[argument]
                args.append(argument)
            
            for keyword, value in kwargs_raw.items():
                if keyword in self._variables:
                    keyword = parameters[keyword]
                if value in self._variables:
                    value = parameters[value]
                kwargs[keyword] = value
            
            method = getattr(queryset, operation['name'])
            queryset = method(*args, **kwargs)
        return queryset
    
    def _register(self, fname, *args, **kwargs):
        '''
        add a configurable queryset function call. Takes the queryset
        method name (ie: 'filter', 'all', 'exclude'...), and
        positional and keyword arguments for the call. Parameters
        will be replaced by any given input parameters when
        unserializing.
        
        '''
        
        args = list(args)
        
        def add_variable(var):
            if var in self._variables:
                raise ValueError('%s was already used!' % var)
            self._variables.append(var)
        
        for i, arg in enumerate(args):
            if arg.startswith('$$'): #escaping
                args[i] = arg[1:]
            elif arg.startswith('$'):
                add_variable(arg)
        
        for key, arg in kwargs.items():
            if arg.startswith('$$'):
                kwargs[key] = arg[1:]
            elif arg.startswith('$'):
                add_variable(arg)
            
            if key.startswith('____'):
                kwargs[key[2:]] = arg
                del kwargs[key]
            elif key.startswith('__'):
                add_variable(key)
        
        self._stack.append({
            'name':fname,
            'args':tuple(args),
            'kwargs':kwargs
        })
        
        return self #chain me!
    
    def filter(self, **kwargs):
        return self._register('filter', **kwargs)
    
    def exclude(self, **kwargs):
        return self._register('exclude', **kwargs)
    
    def annotate(self, *args, **kwargs):
        return self._register('annotate', *args, **kwargs)
    
    def order_by(self, *args):
        return self._register('order_by', *args)
    
    def reverse(self):
        return self._register('reverse')
    
    def distinct(self, *args):
        return self._register('distinct', *args)
    
    def values(self, *args):
        return self._register('values', *args)
    
    def values_list(self, *args):
        return self._register('values_list', *args)
    
    def dates(self, *args, **kwargs):
        return self._register('dates', *args, **kwargs)
    
    def none(self, *args, **kwargs):
        return self._register('none', *args, **kwargs)
    
    def all(self):
        return self._register('all')
    
    def select_related(self):
        return self._register('select_related')
    
    def prefetch_related(self, *args):
        return self._register('prefetch_related', *args)
    
    def extra(self, *args, **kwargs):
        return self._register('extra', *args, **kwargs)
    
    def defer(self, *args):
        return self._register('defer', *args)
    
    def only(self, *args, **kwargs):
        return self._register('only', *args, **kwargs)
    
    def using(self, alias):
        return self._register('using', alias)
    
    def select_for_update(self, nowait):
        return self._register('select_for_update', nowait)



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

def register_chainable(base_queryset, name):
    global dqs
    return dqs.register_chainable(base_queryset, name)


