# Create your views here.

from inspect import getargspec
import dqs
from dqs import dqs as dqs_instance

from django.views.generic import TemplateView
from django.http import HttpResponse
from django.shortcuts import render

def index(request):
    print "view function called"
    serialization_list = []
    for name in dqs_instance: # dqs is a subclass of dict
        serialization_list.append({
            'name': name,
            'function_stack': [(fname,
                [argname for argname in getargspec(function)[0][1:]]
                )for fname, function, index in dqs.get_function_stack(name)]
            })
    return render(request, 'people/index.html', {'serialization_list'
        : serialization_list} )

def results(request, url=''):
    if url:
        qs = dqs.from_url(url)
    elif request.POST:
        qs = dqs.from_request_data(request.POST)
    else:
        return HttpResponse('Bad request', content_type='text/plain', status=503)
    return render(request, 'people/results.html', {
        'people' : qs.get_queryset(),
        'name' : qs.name })

