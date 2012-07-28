import re

def parameters_to_dict(placeholders, parameters):
    '''
    Takes as input the parameters list, and the serializer's
    placeholder list. Outputs a dict mapping placeholders to params,
    given that these params have the same order than the placeholder
    list.

    They also must have the same length. There are NO optional
    parameters, and no way to define an optional placeholder

    '''
    
    'raise TypeErrors'
    parameters = list(parameters)
    placeholders = list(placeholders)
    
    if not len(parameters) == len(placeholders):
        raise ValueError ('Parameters must have the same length as the placeholders')
    
    return dict(zip(placeholders, parameters))

def is_string_placeholder(s):
    return s.startswith('$') and not s.startswith('$$')

# from http://stackoverflow.com/a/10134719/1011311
kwarg_re = re.compile(r'^__[^\d\W]\w*$')
def is_kwarg_key_placeholder(s):
    if s.startswith('____'):
        return False
    return bool(kwarg_re.findall(s))

def is_placeholder(s):
    siphon = is_string_placeholder(s)
    underscore = is_kwarg_key_placeholder(s)
    return siphon or underscore

def unescape_non_placeholder(s):
    assert not is_placeholder(s)
    if s.startswith('$'):
        return s[1:]
    elif s.startswith('__'):
        return s[2:]
    else:
        return s

def clean_placeholder(s):
    assert is_placeholder(s)
    if s.startswith('$'):
        return s[1:]
    elif s.startswith('__'):
        return s[2:]

def unescape(s):
    if is_placeholder(s):
        return clean_placeholder(s)
    else:
        return unescape_non_placeholder(s)


