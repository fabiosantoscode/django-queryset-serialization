from itertools import chain
from functools import update_wrapper, partial
import json
import warnings
from functools import update_wrapper
import inspect



class Serialization():
    def __init__(self, name, serializer, base_queryset):
        self.name = name
        self.base_queryset = base_queryset
        self.serializer = serializer
    
    def get_queryset(self, parameters=None):
        '''
        Get a queryset by executing the operations to the base
        queryset registered in the DjangoQuerysetSerialization
        instance.
        
        Parameters (__customizable_kwarg='$param1','$other-param')
        inserted when this was being created are replaced with the
        actual values passed in through the argument `parameters`.
        
        '''
        
        return self.serializer.get_queryset(self.base_queryset, parameters)

class DjangoQuerysetSerialization(dict):
    '''
    Central class of the django-queryset-serialization system. New
    serializations are registered here, and 
    
    Subclass of dict
    
    Internal description:
    Dictionary mapping serialization names to Serialization objects.
    
    Usage:
    
    from dqs import dqs
    
    serializer = dqs.make_serializer(person__name__icontains='$param')
    dqs.register('people-search', serializer, Person.objects.all())
    
    (.. ..)
    
    from dqs import dqs
    
    dqs['people-search'].get_queryset({'$param':'a'})
    #gets a queryset of people with names with "a" in them.
    
    '''
    
    def make_serializer(self):
        return ChainableSerializer()
    
    def register(self, name, serializer, queryset):
        if name in self:
            raise Exception('%s was already registered in Django-queryset-serialization' % name)
        serialization = Serialization(name, serializer, queryset)
        self[name] = serialization
        return serialization

dqs = DjangoQuerysetSerialization()



#class QuerysetMethodWrapper(object):
#    def __init__(self, method):
#TODO make ChainableSerializer delegate this bit of work

class ChainableSerializer(object):
    '''
    A new way to serialize a queryset. You can just create it, and
    change it like you would use a real queryset, except you can save
    it for later execution.
    
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
    
    def __init__(self):
        self._placeholders = []
        self._stack = []
    
    def get_queryset(self, base_queryset, parameters):
        'Called by Serialization.get_queryset()'
        
        if self._placeholders and not parameters:
            raise Exception('There are required parameters to get this queryset. The required parameters are: %s.' % ', '.join(self._placeholders))
        
        #def replace_placeholders
        
        queryset = base_queryset
        for operation in self._stack:
            args_raw, kwargs_raw = operation['args'], operation['kwargs']
            
            #args = map(replace_placeholders, operation['args'])
            #kwargs_keys = map(replace_placeholders, oper
            #TODO ditch these cycles!
            args, kwargs = [], {}
            for argument in args_raw:
                if argument in self._placeholders:
                    argument = parameters[argument]
                args.append(argument)
            
            for keyword, value in kwargs_raw.items():
                if keyword in self._placeholders:
                    keyword = parameters[keyword]
                if value in self._placeholders:
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
        
        def add_placeholder(var):
            if var in self._placeholders:
                raise ValueError('%s was already used as a placeholder!' % var)
            self._placeholders.append(var)
        
        for i, arg in enumerate(args):
            if arg.startswith('$$'): #escaping
                args[i] = arg[1:]
            elif arg.startswith('$'):
                add_placeholder(arg)
        
        for key, arg in kwargs.items():
            if arg.startswith('$$'):
                kwargs[key] = arg[1:]
            elif arg.startswith('$'):
                add_placeholder(arg)
            
            if key.startswith('____'):
                kwargs[key[2:]] = arg
                del kwargs[key]
            elif key.startswith('__'):
                add_placeholder(key)
        
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



