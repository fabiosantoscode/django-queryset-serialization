import itertools
import copy
import utils


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
        
        return self.serializer.get_queryset(self.base_queryset,
            parameters)



class DjangoQuerysetSerialization(dict):
    '''
    Central class of the django-queryset-serialization system. New
    serializations are registered here, and 
    
    Subclass of dict
    
    Internal description:
    Dictionary mapping serialization names to Serialization objects.
    
    '''
    
    def make_serializer(self):
        return FilterChain()
    
    def register(self, name, serializer, queryset):
        if name in self:
            raise Exception('%s was already registered in this '
                + 'django-queryset-serialization instance' % name)
        serialization = Serialization(name, serializer, queryset)
        self[name] = serialization
        return serialization
    
    def from_dictionary_parameters(self, d, name=None):
        name = name or d['name']
        serialization = self[name]
    
    def from_iterable_parameters(self, iterable, name=None):
        iterable = iter(iterable)
        name = name or iterable.next()
        serialization = self[name]
        parameters = utils.parameters_to_dict(
            serialization.serializer._placeholders, iterable)
        
        return serialization.get_queryset(parameters)
    
    def from_url(self, url, name=None):
        url = url.strip().strip('/')
        components = url.split('/')
        return self.from_iterable(url, name)


dqs = DjangoQuerysetSerialization()



class FilterChain(object):
    '''
    A new way to serialize a queryset. You can just create it, and
    change it like you would use a real queryset, except you can save
    it for later execution.
    
    $parameters, or __keyword_arguments can be specified. They are
    later passed to Serialization.get_queryset
    
    Example:
    
    some_queryset = SomeModel.objects.all()
    qs = FilterChain(some_queryset)
    
    qs = qs.exclude(banned=True)
    qs = qs.filter(something__iexact='$parameter1')
    
    qs.get_queryset({'$parameter1':'something'})
    
    NOTE:
     - Every parameter tag ($parameter-tag) must be a string. It is
    a good idea to keep them URL-friendly
    
    '''
    __slots__ = ['_placeholders','_stack']
    
    def __init__(self):
        self._placeholders = []
        self._stack = []
    
    placeholders = property(lambda s:s._placeholders)
    
    def _copy(self):
        '''
        Make a copy of this class. very useful for immutability
        '''
        copied = self.__class__()
        copied._stack = copy.deepcopy(self._stack)
        copied._placeholders = copy.copy(self._placeholders)
        return copied
    
    def get_queryset(self, base_queryset, parameters):
        'called by Serializer.get_queryset()'
        
        if self._placeholders and not parameters:
            raise Exception('There are required parameters to get '
                + 'this queryset. The required parameters are: %s.'
                % ', '.join(self._placeholders))
        
        'copy the placeholders. we are going to consume them'
        placeholders_left = list(self._placeholders)
        
        
        def replace_placeholders(l):
            '''
            Replace placeholder items in the input list (args,
            kwargs.keys() and kwargs.values()) with
            '''
            ret = []
            for val in l:
                val = utils.unescape(val)
                if val in placeholders_left:
                    ret.append(parameters[val])
                    placeholders_left.remove(val)
                else:
                    ret.append(val)
            return ret
        
        def replace_placeholders_in_dict(d):
            vals = replace_placeholders(d.values())
            keys = replace_placeholders(d.keys())
            return dict(zip(keys,vals))
        calls = []
        
        for operation in self._stack:
            args = replace_placeholders(operation['args'])
            kwargs = replace_placeholders_in_dict(operation['kwargs'])
            name = operation['name']
            calls.append((name,args,kwargs))
        
        if len(placeholders_left) > 0:
            raise Exception(
                '%d parameters were not given to get_queryset:' %
                (len(placeholders_left), ', '.join(
                placeholders_left)))
        
        queryset = base_queryset
        for name, args, kwargs in calls:
            method = getattr(queryset, name)
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
        
        def find_placeholder(arg):
            if utils.is_placeholder(arg):
                arg = utils.clean_placeholder(arg)
                if arg in self._placeholders:
                    raise ValueError(
                        '%s was already used as a placeholder!' % arg)
                self._placeholders.append(arg)
                return arg
            else:
                return utils.unescape_non_placeholder(arg)
        
        args = map(find_placeholder, args)
        kwargs_keys = map(find_placeholder, kwargs.keys())
        kwargs_values = map(find_placeholder, kwargs.values())
        
        kwargs = dict(zip(kwargs_keys, kwargs_values))
        
        self._stack.append({
            'name':fname,
            'args':tuple(args),
            'kwargs':kwargs
        })
    
    def filter(self, **kwargs):
        return self.method('filter', **kwargs)
    
    def exclude(self, **kwargs):
        return self.method('exclude', **kwargs)
    
    def annotate(self, *args, **kwargs):
        return self.method('annotate', *args, **kwargs)
    
    def order_by(self, *args):
        return self.method('order_by', *args)
    
    def reverse(self):
        return self.method('reverse')
    
    def distinct(self, *args):
        return self.method('distinct', *args)
    
    def values(self, *args):
        return self.method('values', *args)
    
    def values_list(self, *args):
        return self.method('values_list', *args)
    
    def dates(self, *args, **kwargs):
        return self.method('dates', *args, **kwargs)
    
    def none(self, *args, **kwargs):
        return self.method('none', *args, **kwargs)
    
    def all(self):
        return self.method('all')
    
    def select_related(self):
        return self.method('select_related')
    
    def prefetch_related(self, *args):
        return self.method('prefetch_related', *args)
    
    def extra(self, *args, **kwargs):
        return self.method('extra', *args, **kwargs)
    
    def defer(self, *args):
        return self.method('defer', *args)
    
    def only(self, *args, **kwargs):
        return self.method('only', *args, **kwargs)
    
    def using(self, alias):
        return self.method('using', alias)
    
    def select_for_update(self, nowait):
        return self.method('select_for_update', nowait)
    
    def method(self, method_name, *args, **kwargs):
        '''
        Call the queryset method by name instead of calling a
        dedicated shortcut
        
        .all(), .filter(), .exclude(), etc. are just using this method
        internally.
        
        .all() == .method('all')
        .filter(**kwargs) == .method('filter', **kwargs)
        etc.
        
        This is useful when you want to use a method for which there
        is no shortcut, or when you want to do more complex stuff like
        custom serializations and such.
        
        This project is rather django version agnostic. If new methods
        are inserted in QuerySet, they are immediately supported
        through .method()
        
        '''
        
        copy = self._copy()
        
        copy._register(method_name, *args, **kwargs)
        
        return copy

