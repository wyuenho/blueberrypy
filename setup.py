from __future__ import print_function

import os.path
import sys

from setuptools import setup, find_packages


install_requires = ["CherryPy>=3.3",
                    "docopt>=0.6",
                    "Jinja2>=2.7",
                    "PyYAML>=3.10",
                    "python-dateutil>=2.2"]

speedup_requires = ["MarkupSafe>=0.20",
                    "hiredis>=0.1.0",
                    "simplejson>=3.4"]

dev_requires = ["Sphinx>=1.2",
                "nose>=1.3",
                "nose-testconfig>=0.9",
                "coverage>=3.7",
                "flexmock>=0.9.7",
                "lazr.smtptest>=2.0",
                "tox>=1.7"]

if sys.version_info < (2, 7):
    print("blueberrypy doesn't support python <= 2.6. Sorry!", file=sys.stderr)
    sys.exit(1)

if sys.version_info < (3, 3):
    speedup_requires.append("cdecimal>=2.3")

readme_file = open(os.path.abspath(os.path.join(os.path.dirname(__file__), "README.rst")), "r")
readme = readme_file.read()
readme_file.close()

setup(name="blueberrypy",
      version="0.6",
      author="Jimmy Yuen Ho Wong",
      author_email="wyuenho@gmail.com",
      url="http://bitbucket.org/wyuenho/blueberrypy",
      description="CherryPy plugins and tools for integration with various libraries, including "
                  "logging, Redis, SQLAlchemy and Jinja2 and webassets.",
      long_description=readme,
      classifiers=["Development Status :: 4 - Beta",
                   "Environment :: Plugins",
                   "Environment :: Web Environment",
                   "Framework :: CherryPy",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: BSD License",
                   "Natural Language :: English",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python :: 2.7",
                   "Programming Language :: Python :: 3.3",
                   "Programming Language :: Python :: 3.4",
                   "Topic :: Database",
                   "Topic :: Internet :: WWW/HTTP :: Session",
                   "Topic :: Software Development :: Libraries",
                   "Topic :: Utilities"],
      license="BSD",
      package_dir={"": "src"},
      packages=find_packages("src"),
      include_package_data=True,
      use_2to3=True,
      entry_points={"console_scripts": ["blueberrypy = blueberrypy.command:main"]},
      zip_safe=False,
      install_requires=install_requires,
      extras_require={"speedups": speedup_requires,
                      "all": ["SQLAlchemy>=0.9",
                              "redis>=2.9",
                              "webassets>=0.9",
                              "Routes>=2.0",
                              "backlash>=0.0.5",
                              "Shapely>=1.2",
                              "GeoAlchemy2>=0.2.4"],
                      "geospatial": ["Shapely>=1.3",
                                     "GeoAlchemy2>=0.2.4"],
                      "dev": dev_requires})
