


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