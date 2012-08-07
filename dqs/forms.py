from django import forms



class Form(forms.Form):
    '''
    Django Queryset Serialization form.
    
    To use, create subclasses, and add fields that match the desired
    serialization's parameters. For example, you have the following
    serialization:
    
    serializer = dqs.dqs.make_serializer().filter(name='$name')
    dqs.dqs.register('some_serializer',serializer,People.objects.all())
    
    Create the following form:
    
    class NameSearch(dqs.forms.Form):
        serialization = dqs.dqs['some_serializer']
        name = forms.CharField(max_length=13)
    
    You can use the NameSearch form everywhere you can use a regular
    Django form. It's a regular Django form, after all.
    
    When you want to get a queryset from a valid DQS form, just call
    get_queryset.
    
    '''
    
    name = forms.CharField(widget=forms.widgets.HiddenInput())
    
    def __init__(self, data=None, serialization=None, **kwargs):
        super(Form, self).__init__(data, **kwargs)
        self.serialization = serialization or self.serialization
        self.fields['name'].initial = self.serialization.name
    
    def get_queryset(self):
        parameters = getattr(self, 'cleaned_data', {}) #omg!
        return self.serialization.get_queryset(parameters)