CherryPie
=========
The crust for your CherryPy



What is it?
-----------
CherryPie is a CherryPy project skeleton generator and a collection of tools,
plugins and utilities for `CherryPy <http://cherrypy.org/>`_ - the minimalist
Python web framework.


What does it offer?
-------------------
CherryPie is offered as a set of CherryPy tools, WSPB plugins and extra utility
modules. All the components are optional and completely pluggable without any
intermodule dependencies, so you can safely pick and choose just the components
you want.

- SQLAlchemy ORM integration
- Per-request SQLAlchemy ORM session
- Redis session storage
- Jinja2 template engine
- Webassets asset pipeline integrated with Jinja2
- Application specific logging
- CherryPy project skeleton generator
- Preconfigured console for experiementing inside a generated project
- YAML configuration for CherryPy, Python's logging module and Webassets
- Convenient Email module for sending text emails
- JSON tools to convert to and from SQLAlchemy models
- CSRF token


Installation
------------
CherryPie is still unreleased, so for now you have to install it directly from
BitBucket.


   pip install https://bitbucket.org/wyuenho/cherrypie


Note: You should probably install it inside a `virtualenv <http://www.virtualenv.org/>`_.


Usage
-----

Once CherryPie is installed, a script called `cherrypie` should be available on
your PATH.

::

  usage: cherrypie [-h] [-v] [-c CONFIG_DIR] [command]

  CherryPie lightweight pluggable Web application framework command line interface.

     Type 'cherrypie -h' or 'cherrypie --help' for general help.
     Type 'cherrypie help <command>' for help on that specific command.

  commands:

     help                print this help or a command's if an argument is given
     create              create a project skeleton
     console             CherryPie REPL for experimentations
     bundle              bundles up web assets (type 'cherrypie help bundle' for details)
     serve               spawn a new CherryPy server process

  positional arguments:
     command               the action to perform

  optional arguments:
     -h, --help            show this help message and exit
     -v, --version         print version information and exit.
     -c CONFIG_DIR, --config_dir CONFIG_DIR
                           path to the config directory


To create a project skeleton::

   $ cherrypie create

After you've answered a couple of questions, you should see something similar to
this::

   ===========================================================================
   Your project skeleton has been created under /Users/wyuenho/Documents/workspace/cptest.
   
   
   Subsystems chosen
   -----------------
   Routes (RESTful controllers): True
   Jinja2: True
   webassets: True
   redis: False
   SQLAlchemy: True
   
   Please install the neccessary packages indicated as True above via 'pip' or
   'easy_install'.

   In unrestricted environments, you may also install 'MarkupSafe' and
   'cdecimal' to speed up Jinja2 and SQLAlchemy's queries on Decimal fields
   respectively. You may also install 'hiredis' if you have opted for the Redis
   session storage.
   
   You should also download the appropriate database driver if you have decided
   to use CherryPie's SQLAlchemy support.
   
   ...


Given the above selection, you should do this next::

   $ pip install routes webassets redis sqlalchemy

You can install the optional speedup packages too::

   $ pip install MarkupSafe cdecimal hiredis

Finall, you need to install a database driver such as `psycopg2`::

   $ pip install psycopg2

Now you can serve the generated app::

   $ cherrypie serve

Now type `http://localhost:8080` into your browser's location bar and voila!
Happy coding!

TODO
----

#. project skeleton test templates
#. test config
#. test script output
#. test cherrypie.util
#. test template engine
#. write readme
#. write sphinx doc
#. integrate with weberror
#. integrate with geoalchemy, shapely, geojson
#. modularize skeleton generation
#. add config files to cherrypy's auto watch
#. babel integration
#. request handler cache decorator
