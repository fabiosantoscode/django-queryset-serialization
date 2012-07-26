from setuptools import setup, find_packages
 
version = '1.1'

DESC = '''
Django Queryset Serialization
because serializing django querysets is more trouble than it's worth

Serializes Django Querysets for later use.
'''

setup(
    name='django-queryset-serialization',
    version=version,
    description='django-queryset-serialization',
    long_description=DESC,
    classifiers=[
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Framework :: Django',
    'Environment :: Web Environment',
    ],
    keywords='django,querysets,serialize,serialization',
    author=u'Fábio Santos',
    author_email='fabiosantosart@gmail.com',
    url='http://github.com/fabiosantoscode/django-queryset-serialization',
    license='WTFPL',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
