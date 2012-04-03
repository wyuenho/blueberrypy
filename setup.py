import os.path

from setuptools import setup, find_packages


setup_requires = []
try:
    import argparse
except:
    setup_requires.append('argparse')

try:
    from logging.config import dictConfig
except:
    setup_requires.append('logutils')

readme_file = open(os.path.abspath(os.path.join(os.path.dirname(__file__), 'README.rst')), 'r')
readme = readme_file.read()
readme_file.close()

setup(name='blueberrypy',
      version='0.5',
      author='Jimmy Yuen Ho Wong',
      author_email='wyuenho@gmail.com',
      url='http://bitbucket.org/wyuenho/blueberrypy',
      description='CherryPy plugins and tools for integration with various libraries, including logging, Redis, SQLAlchemy and Jinja2 and webassets.',
      long_description=readme,
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Plugins',
                   'Environment :: Web Environment',
                   'Framework :: CherryPy',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7',
                   'Topic :: Database',
                   'Topic :: Internet :: WWW/HTTP :: Session',
                   'Topic :: Software Development :: Libraries',
                   'Topic :: Utilities'],
      license='BSD',
      package_dir={'': 'src'},
      packages=find_packages('src'),
      include_package_data=True,
      entry_points={'console_scripts': ['blueberrypy = blueberrypy.command:main']},
      zip_safe=False,
      setup_requires=setup_requires,
      install_requires=['CherryPy>=3.2.2',
                        'Jinja2>=2.6',
                        'PyYAML>=3.10',
                        'python-dateutil<2.0',
                        'simplejson>=2.4.0'],
      extras_require={'speedups': ['cdecimal>=2.3',
                                   'MarkupSafe>=0.15',
                                   'hiredis>=0.1.0'],
                      'all': ['SQLAlchemy>=0.7.6',
                              'redis>=2.4.11',
                              'webassets>=0.6',
                              'Routes>=1.12.3',
                              'WebError>=0.10.3'],
                      'dev': ['Sphinx>=1.1.3',
                              'decorator>=3.3.2',
                              'nose>=1.1.3',
                              'nose-testconfig>=0.8',
                              'coverage>=3.5.1',
                              'lazr.smtptest>=1.3',
                              'tox>=1.3']})
