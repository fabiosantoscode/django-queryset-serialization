# Create your views here.

import dqs

from django.views.generic.list_detail import object_list
from django.views.generic.basic import direct_to_template

def search(request):
    if request.GET.get('query'):
        return object_list(request, dqs.from_string(request.GET['query']), template_name='people/search.html')
    else:
        return direct_to_template(request, 'people/search.html')
