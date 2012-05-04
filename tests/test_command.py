import __builtin__
import os.path
import sys
try:
    import unittest2 as unittest
except ImportError:
    import unittest
import textwrap

from StringIO import StringIO

import cherrypy
import jinja2
import webassets

from yaml import load as load_yaml

from ludibrio import Mock

import blueberrypy
from blueberrypy.command import main


class CreateCommandTest(unittest.TestCase):

    def test_create_command_y_with_path(self):
        sys.argv = "blueberrypy create -p /tmp".split()

        with Mock() as raw_input:
            from __builtin__ import raw_input
            raw_input("Project name: ") >> "testproject"
            raw_input("Package name: ") >> "testproject"
            raw_input("Version (PEP 386): ") >> "0.1"
            raw_input("Author name: ") >> "author"
            raw_input("Email: ") >> "alice@example.com"
            raw_input("Use controllers backed by a templating engine? [Y/n] ") >> "y"
            raw_input("Use RESTful controllers? [y/N] ") >> "y"
            raw_input("Use Jinja2 templating engine? [Y/n] ") >> "y"
            raw_input("Use webassets asset management framework? [Y/n] ") >> "y"
            raw_input("Use redis session? [y/N] ") >> "y"
            raw_input("Use SQLAlchemy ORM? [Y/n] ") >> "y"
            raw_input("SQLAlchemy database connection URL: ") >> "sqlite://"

        config = {'author': 'author',
                  'current_year': 2012,
                  'driver': 'pysqlite',
                  'email': 'alice@example.com',
                  'package': 'testproject',
                  'path': '/tmp',
                  'project_name': 'testproject',
                  'sqlalchemy_url': 'sqlite://',
                  'use_controller': True,
                  'use_jinja2': True,
                  'use_redis': True,
                  'use_rest_controller': True,
                  'use_sqlalchemy': True,
                  'use_webassets': True,
                  'version': '0.1'}

        with Mock() as create_project:
            from blueberrypy.command import create_project
            create_project(config, dry_run=False) >> None

        main()

        raw_input.validate()
        create_project.validate()

    def test_create_command_yes(self):
        sys.argv = "blueberrypy create".split()

        with Mock() as raw_input:
            from __builtin__ import raw_input
            raw_input("Project name: ") >> "testproject"
            raw_input("Package name: ") >> "testproject"
            raw_input("Version (PEP 386): ") >> "0.1"
            raw_input("Author name: ") >> "author"
            raw_input("Email: ") >> "alice@example.com"
            raw_input("Use controllers backed by a templating engine? [Y/n] ") >> "Yes"
            raw_input("Use RESTful controllers? [y/N] ") >> "Yes"
            raw_input("Use Jinja2 templating engine? [Y/n] ") >> "Yes"
            raw_input("Use webassets asset management framework? [Y/n] ") >> "Yes"
            raw_input("Use redis session? [y/N] ") >> "Yes"
            raw_input("Use SQLAlchemy ORM? [Y/n] ") >> "Yes"
            raw_input("SQLAlchemy database connection URL: ") >> "sqlite://"

        config = {'author': 'author',
                  'current_year': 2012,
                  'driver': 'pysqlite',
                  'email': 'alice@example.com',
                  'package': 'testproject',
                  'path': os.getcwdu(),
                  'project_name': 'testproject',
                  'sqlalchemy_url': 'sqlite://',
                  'use_controller': True,
                  'use_jinja2': True,
                  'use_redis': True,
                  'use_rest_controller': True,
                  'use_sqlalchemy': True,
                  'use_webassets': True,
                  'version': '0.1'}

        with Mock() as create_project:
            from blueberrypy.command import create_project
            create_project(config, dry_run=False) >> None

        main()

        raw_input.validate()
        create_project.validate()

    def test_create_command_n(self):
        sys.argv = "blueberrypy create".split()

        with Mock() as raw_input:
            from __builtin__ import raw_input
            raw_input("Project name: ") >> "testproject"
            raw_input("Package name: ") >> "testproject"
            raw_input("Version (PEP 386): ") >> "0.1"
            raw_input("Author name: ") >> "author"
            raw_input("Email: ") >> "alice@example.com"
            raw_input("Use controllers backed by a templating engine? [Y/n] ") >> "n"
            raw_input("Use RESTful controllers? [y/N] ") >> "n"
            raw_input("Use redis session? [y/N] ") >> "n"
            raw_input("Use SQLAlchemy ORM? [Y/n] ") >> "n"

        config = {'author': 'author',
                  'current_year': 2012,
                  'email': 'alice@example.com',
                  'package': 'testproject',
                  'path': os.getcwdu(),
                  'project_name': 'testproject',
                  'use_controller': False,
                  'use_jinja2': False,
                  'use_redis': False,
                  'use_rest_controller': False,
                  'use_sqlalchemy': False,
                  'use_webassets': False,
                  'version': '0.1'}

        with Mock() as create_project:
            from blueberrypy.command import create_project
            create_project(config, dry_run=False) >> None

        main()

        raw_input.validate()
        create_project.validate()

    def test_create_command_no(self):
        sys.argv = "blueberrypy create".split()

        with Mock() as raw_input:
            from __builtin__ import raw_input
            raw_input("Project name: ") >> "testproject"
            raw_input("Package name: ") >> "testproject"
            raw_input("Version (PEP 386): ") >> "0.1"
            raw_input("Author name: ") >> "author"
            raw_input("Email: ") >> "alice@example.com"
            raw_input("Use controllers backed by a templating engine? [Y/n] ") >> "No"
            raw_input("Use RESTful controllers? [y/N] ") >> "No"
            raw_input("Use redis session? [y/N] ") >> "No"
            raw_input("Use SQLAlchemy ORM? [Y/n] ") >> "No"

        config = {'author': 'author',
                  'current_year': 2012,
                  'email': 'alice@example.com',
                  'package': 'testproject',
                  'path': os.getcwdu(),
                  'project_name': 'testproject',
                  'use_controller': False,
                  'use_jinja2': False,
                  'use_redis': False,
                  'use_rest_controller': False,
                  'use_sqlalchemy': False,
                  'use_webassets': False,
                  'version': '0.1'}

        with Mock() as create_project:
            from blueberrypy.command import create_project
            create_project(config, dry_run=False) >> None

        main()

        raw_input.validate()
        create_project.validate()

    def test_create_command_conditional_no(self):
        sys.argv = "blueberrypy create".split()

        with Mock() as raw_input:
            from __builtin__ import raw_input
            raw_input("Project name: ") >> "testproject"
            raw_input("Package name: ") >> "testproject"
            raw_input("Version (PEP 386): ") >> "0.1"
            raw_input("Author name: ") >> "author"
            raw_input("Email: ") >> "alice@example.com"
            raw_input("Use controllers backed by a templating engine? [Y/n] ") >> "y"
            raw_input("Use RESTful controllers? [y/N] ") >> "No"
            raw_input("Use Jinja2 templating engine? [Y/n] ") >> "No"
            raw_input("Use webassets asset management framework? [Y/n] ") >> "No"
            raw_input("Use redis session? [y/N] ") >> "No"
            raw_input("Use SQLAlchemy ORM? [Y/n] ") >> "No"

        config = {'author': 'author',
                  'current_year': 2012,
                  'email': 'alice@example.com',
                  'package': 'testproject',
                  'path': os.getcwdu(),
                  'project_name': 'testproject',
                  'use_controller': True,
                  'use_jinja2': False,
                  'use_redis': False,
                  'use_rest_controller': False,
                  'use_sqlalchemy': False,
                  'use_webassets': False,
                  'version': '0.1'}

        with Mock() as create_project:
            from blueberrypy.command import create_project
            create_project(config, dry_run=False) >> None

        main()

        raw_input.validate()
        create_project.validate()

    def test_create_command_conditional_n(self):
        sys.argv = "blueberrypy create".split()

        with Mock() as raw_input:
            from __builtin__ import raw_input
            raw_input("Project name: ") >> "testproject"
            raw_input("Package name: ") >> "testproject"
            raw_input("Version (PEP 386): ") >> "0.1"
            raw_input("Author name: ") >> "author"
            raw_input("Email: ") >> "alice@example.com"
            raw_input("Use controllers backed by a templating engine? [Y/n] ") >> "y"
            raw_input("Use RESTful controllers? [y/N] ") >> "No"
            raw_input("Use Jinja2 templating engine? [Y/n] ") >> "n"
            raw_input("Use webassets asset management framework? [Y/n] ") >> "n"
            raw_input("Use redis session? [y/N] ") >> "No"
            raw_input("Use SQLAlchemy ORM? [Y/n] ") >> "No"

        config = {'author': 'author',
                  'current_year': 2012,
                  'email': 'alice@example.com',
                  'package': 'testproject',
                  'path': os.getcwdu(),
                  'project_name': 'testproject',
                  'use_controller': True,
                  'use_jinja2': False,
                  'use_redis': False,
                  'use_rest_controller': False,
                  'use_sqlalchemy': False,
                  'use_webassets': False,
                  'version': '0.1'}

        with Mock() as create_project:
            from blueberrypy.command import create_project
            create_project(config, dry_run=False) >> None

        main()

        raw_input.validate()
        create_project.validate()

    def test_create_command_invalid_input_and_defaults(self):
        sys.argv = "blueberrypy create".split()

        with Mock() as raw_input:
            from __builtin__ import raw_input
            raw_input("Project name: ") >> ""
            raw_input("Package name: ") >> ""
            raw_input("Package name: ") >> "valid_package_name"
            raw_input("Version (PEP 386): ") >> "IWillFail"
            raw_input("Version (PEP 386): ") >> "0.1"
            raw_input("Author name: ") >> ""
            raw_input("Email: ") >> "notavalidemail"
            raw_input("Email: ") >> "alice@example.com"
            raw_input("Use controllers backed by a templating engine? [Y/n] ") >> ""
            raw_input("Use RESTful controllers? [y/N] ") >> ""
            raw_input("Use Jinja2 templating engine? [Y/n] ") >> ""
            raw_input("Use webassets asset management framework? [Y/n] ") >> ""
            raw_input("Use redis session? [y/N] ") >> ""
            raw_input("Use SQLAlchemy ORM? [Y/n] ") >> ""
            raw_input("SQLAlchemy database connection URL: ") >> ""

        config = {'author': '',
                  'current_year': 2012,
                  'email': 'alice@example.com',
                  'package': 'valid_package_name',
                  'path': os.getcwdu(),
                  'project_name': '',
                  'sqlalchemy_url': '',
                  'use_controller': True,
                  'use_jinja2': True,
                  'use_redis': False,
                  'use_rest_controller': False,
                  'use_sqlalchemy': True,
                  'use_webassets': True,
                  'version': '0.1'}

        with Mock() as create_project:
            from blueberrypy.command import create_project
            create_project(config, dry_run=False) >> None

        main()

        raw_input.validate()
        create_project.validate()

    def test_create_command_invalid_yes_no(self):
        sys.argv = "blueberrypy create".split()

        with Mock() as raw_input:
            from __builtin__ import raw_input
            raw_input("Project name: ") >> ""
            raw_input("Package name: ") >> "valid_package_name"
            raw_input("Version (PEP 386): ") >> "0.1"
            raw_input("Author name: ") >> ""
            raw_input("Email: ") >> "alice@example.com"
            raw_input("Use controllers backed by a templating engine? [Y/n] ") >> "sdf"
            raw_input("Use controllers backed by a templating engine? [Y/n] ") >> "y"
            raw_input("Use RESTful controllers? [y/N] ") >> "asdfasdf"
            raw_input("Use RESTful controllers? [y/N] ") >> "y"
            raw_input("Use Jinja2 templating engine? [Y/n] ") >> "asdf"
            raw_input("Use Jinja2 templating engine? [Y/n] ") >> "y"
            raw_input("Use webassets asset management framework? [Y/n] ") >> "asdf"
            raw_input("Use webassets asset management framework? [Y/n] ") >> "y"
            raw_input("Use redis session? [y/N] ") >> "asdfasdf"
            raw_input("Use redis session? [y/N] ") >> "y"
            raw_input("Use SQLAlchemy ORM? [Y/n] ") >> "asdfasdf"
            raw_input("Use SQLAlchemy ORM? [Y/n] ") >> "y"
            raw_input("SQLAlchemy database connection URL: ") >> ""

        config = {'author': '',
                  'current_year': 2012,
                  'email': 'alice@example.com',
                  'package': 'valid_package_name',
                  'path': os.getcwdu(),
                  'project_name': '',
                  'sqlalchemy_url': '',
                  'use_controller': True,
                  'use_jinja2': True,
                  'use_redis': True,
                  'use_rest_controller': True,
                  'use_sqlalchemy': True,
                  'use_webassets': True,
                  'version': '0.1'}

        with Mock() as create_project:
            from blueberrypy.command import create_project
            create_project(config, dry_run=False) >> None

        main()

        raw_input.validate()
        create_project.validate()


# dummy controllers
class Root(object):

    def index(self):
        return "hello world!"
    index.exposed = True

class DummyRestController(object):

    def dummy(self, **kwargs):
        return "hello world!"

rest_controller = cherrypy.dispatch.RoutesDispatcher()
rest_controller.connect("dummy", "/dummy", DummyRestController, action="dummy")


class FakeFile(StringIO):
    def __enter__(self):
        return self
    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        return False


class ServeCommandTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.old_sys_argv = sys.argv
        cls.old_cherrypy_server_bind_addr = cherrypy.server.bind_addr

    def setUp(self):
        self.old_exists = os.path.exists
        self.old_open = __builtin__.open

        # mock out engine.block()
        self.old_cherrypy_engine_block = cherrypy.engine.block
        def dummy_block(self):
            pass
        cherrypy.engine.block = dummy_block.__get__(cherrypy.engine, cherrypy.engine.__class__)

    def tearDown(self):
        # clean up attached objects
        if hasattr(cherrypy.engine, "sqlalchemy"):
            del cherrypy.engine.sqlalchemy
        if hasattr(cherrypy.engine, "logging"):
            del cherrypy.engine.logging
        if blueberrypy.email._mailer is not None:
            blueberrypy.email._mailer = None
        if hasattr(cherrypy.lib.sessions, "RedisSession"):
            del cherrypy.lib.sessions.RedisSession
        if hasattr(cherrypy.tools, "orm_session"):
            del cherrypy.tools.orm_session
        if blueberrypy.template_engine.jinja2_env is not None:
            blueberrypy.template_engine.jinja2_env = None

        # restore stuff
        sys.argv = self.old_sys_argv
        cherrypy.server.bind_addr = self.old_cherrypy_server_bind_addr
        os.path.exists = self.old_exists
        __builtin__.open = self.old_open
        cherrypy.engine.block = self.old_cherrypy_engine_block
        cherrypy.engine.exit()

    def _stub_out_path_and_open(self, path_file_mapping=None, mode='r', buffering=1):

        def proxied_exists(path):
            if path in path_file_mapping:
                return True
            return self.old_exists(path)
        os.path.exists = proxied_exists

        if path_file_mapping is None:
            path_file_mapping = {}

        def proxied_open(filename, mode=mode, buffering=buffering):
            if filename in path_file_mapping:
                return path_file_mapping[filename]
            else:
                return self.old_open(filename, mode, buffering)

        __builtin__.open = proxied_open

    def _setup_basic_app_config(self):
        app_yml_file = FakeFile(textwrap.dedent("""
        global:
            environment: test_suite
        controllers:
            '':
                controller: !!python/name:tests.test_command.Root
            /api:
                controller: !!python/name:tests.test_command.rest_controller
        """))

        path_file_mapping = {"/tmp/dev/app.yml": app_yml_file}
        self._stub_out_path_and_open(path_file_mapping)

    def test_setup_email(self):
        app_yml_file = FakeFile(textwrap.dedent("""
        global:
            environment: test_suite
        controllers:
            '':
                controller: !!python/name:tests.test_command.Root
            /api:
                controller: !!python/name:tests.test_command.rest_controller
        email:
            host: localhost
            port: 1025
        """))

        path_file_mapping = {"/tmp/dev/app.yml": app_yml_file}
        self._stub_out_path_and_open(path_file_mapping)

        sys.argv = ("blueberrypy -C /tmp serve").split()
        main()
        self.assertIsInstance(blueberrypy.email._mailer, blueberrypy.email.Mailer)
        self.assertTrue(not hasattr(cherrypy.engine, "logging"))
        self.assertTrue(not hasattr(cherrypy.lib.sessions, "RedisSession"))
        self.assertTrue(not hasattr(cherrypy.engine, "sqlalchemy"))
        self.assertTrue(not hasattr(cherrypy.tools, "orm_session"))
        self.assertIsNone(blueberrypy.template_engine.jinja2_env)

    def test_setup_cherrypy_logging(self):
        app_yml_file = FakeFile(textwrap.dedent("""
        global:
            engine.logging.on: true
            environment: test_suite
        controllers:
            '':
                controller: !!python/name:tests.test_command.Root
            /api:
                controller: !!python/name:tests.test_command.rest_controller
        """))
        logging_yml_file = FakeFile(textwrap.dedent("""
        version: 1
        disable_existing_loggers: false
        loggers:
            root:
                level: WARNING
                handlers: [stdout]
        handlers:
            stdout:
                class: logging.StreamHandler
                formatter: debug
                stream: ext://sys.stdout
        formatters:
            debug:
                format: '%(asctime)s [%(levelname)s] %(name)s Thread(id=%(thread)d, name="%(threadName)s") %(message)s'
        """))

        path_file_mapping = {"/tmp/dev/app.yml": app_yml_file,
                             "/tmp/dev/logging.yml": logging_yml_file}
        self._stub_out_path_and_open(path_file_mapping)

        sys.argv = ("blueberrypy -C /tmp serve").split()
        main()
        self.assertIsNone(blueberrypy.email._mailer)
        self.assertIsInstance(cherrypy.engine.logging, blueberrypy.plugins.LoggingPlugin)
        self.assertTrue(not hasattr(cherrypy.lib.sessions, "RedisSession"))
        self.assertTrue(not hasattr(cherrypy.engine, "sqlalchemy"))
        self.assertTrue(not hasattr(cherrypy.tools, "orm_session"))
        self.assertIsNone(blueberrypy.template_engine.jinja2_env)

    def test_setup_cherrypy_redis(self):
        app_yml_file = FakeFile(textwrap.dedent("""
        global:
            environment: test_suite
        controllers:
            '':
                controller: !!python/name:tests.test_command.Root
                /:
                    tools.sessions.storage_type: redis
            /api:
                controller: !!python/name:tests.test_command.rest_controller
        """))

        path_file_mapping = {"/tmp/dev/app.yml": app_yml_file}
        self._stub_out_path_and_open(path_file_mapping)

        sys.argv = ("blueberrypy -C /tmp serve").split()
        main()
        self.assertIsNone(blueberrypy.email._mailer)
        self.assertTrue(not hasattr(cherrypy.engine, "logging"))
        self.assertEqual(cherrypy.lib.sessions.RedisSession, blueberrypy.session.RedisSession)
        self.assertTrue(not hasattr(cherrypy.engine, "sqlalchemy"))
        self.assertTrue(not hasattr(cherrypy.tools, "orm_session"))
        self.assertIsNone(blueberrypy.template_engine.jinja2_env)

    def test_setup_sqlalchemy(self):
        app_yml_file = FakeFile(textwrap.dedent("""
        global:
            engine.sqlalchemy.on: true
            environment: test_suite
        controllers:
            '':
                controller: !!python/name:tests.test_command.Root
            /api:
                controller: !!python/name:tests.test_command.rest_controller
        sqlalchemy_engine:
            url: sqlite://
        """))

        path_file_mapping = {"/tmp/dev/app.yml": app_yml_file}
        self._stub_out_path_and_open(path_file_mapping)

        sys.argv = ("blueberrypy -C /tmp serve").split()
        main()
        self.assertIsNone(blueberrypy.email._mailer)
        self.assertTrue(not hasattr(cherrypy.engine, "logging"))
        self.assertTrue(not hasattr(cherrypy.lib.sessions, "RedisSession"))
        self.assertIsInstance(cherrypy.engine.sqlalchemy, blueberrypy.plugins.SQLAlchemyPlugin)
        self.assertIsInstance(cherrypy.tools.orm_session, blueberrypy.tools.SQLAlchemySessionTool)
        self.assertIsNone(blueberrypy.template_engine.jinja2_env)

    def test_setup_jinja2(self):
        app_yml_file = FakeFile(textwrap.dedent("""
        global:
            environment: test_suite
        controllers:
            '':
                controller: !!python/name:tests.test_command.Root
            /api:
                controller: !!python/name:tests.test_command.rest_controller
        jinja2:
            loader: !!python/object:jinja2.loaders.DictLoader
                    mapping: {}
        """))

        path_file_mapping = {"/tmp/dev/app.yml": app_yml_file}
        self._stub_out_path_and_open(path_file_mapping)

        sys.argv = ("blueberrypy -C /tmp serve").split()
        main()
        self.assertIsNone(blueberrypy.email._mailer)
        self.assertTrue(not hasattr(cherrypy.engine, "logging"))
        self.assertTrue(not hasattr(cherrypy.lib.sessions, "RedisSession"))
        self.assertTrue(not hasattr(cherrypy.engine, "sqlalchemy"))
        self.assertTrue(not hasattr(cherrypy.tools, "orm_session"))
        self.assertIsInstance(blueberrypy.template_engine.jinja2_env, jinja2.Environment)

    def test_setup_webassets(self):
        app_yml_file = FakeFile(textwrap.dedent("""
        global:
            environment: test_suite
        controllers:
            '':
                controller: !!python/name:tests.test_command.Root
            /api:
                controller: !!python/name:tests.test_command.rest_controller
        jinja2:
            loader: !!python/object:jinja2.loaders.DictLoader
                    mapping: {}
            use_webassets: true
        """))
        bundles_yml_file = FakeFile(textwrap.dedent("""
        directory: /tmp
        url: /
        bundles:
            nosuchjs.js:
                output: nosuchjs.js
                contents: nosuchjs.js
        """))
        path_file_mapping = {"/tmp/dev/app.yml": app_yml_file,
                             "/tmp/dev/bundles.yml": bundles_yml_file}
        self._stub_out_path_and_open(path_file_mapping)

        sys.argv = ("blueberrypy -C /tmp serve").split()
        main()
        self.assertIsNone(blueberrypy.email._mailer)
        self.assertTrue(not hasattr(cherrypy.engine, "logging"))
        self.assertTrue(not hasattr(cherrypy.lib.sessions, "RedisSession"))
        self.assertTrue(not hasattr(cherrypy.engine, "sqlalchemy"))
        self.assertTrue(not hasattr(cherrypy.tools, "orm_session"))
        self.assertIsInstance(blueberrypy.template_engine.jinja2_env, jinja2.Environment)
        self.assertIsInstance(blueberrypy.template_engine.jinja2_env.assets_environment, webassets.Environment)

    def test_setup_cherrypy_all(self):
        app_yml_file = FakeFile(textwrap.dedent("""
        global:
            engine.logging.on: true
            engine.sqlalchemy.on: true
            environment: test_suite
        controllers:
            '':
                controller: !!python/name:tests.test_command.Root
                /:
                    tools.sessions.storage_type: redis
            /api:
                controller: !!python/name:tests.test_command.rest_controller
        sqlalchemy_engine:
            url: sqlite://
        jinja2:
            loader: !!python/object:jinja2.loaders.DictLoader
                    mapping: {}
            use_webassets: true
        email:
            host: localhost
            port: 1025
        """))
        bundles_yml_file = FakeFile(textwrap.dedent("""
        directory: /tmp
        url: /
        bundles:
            nosuchjs.js:
                output: nosuchjs.js
                contents: nosuchjs.js
        """))
        logging_yml_file = FakeFile(textwrap.dedent("""
        version: 1
        disable_existing_loggers: false
        loggers:
            root:
                level: WARNING
                handlers: [stdout]
        handlers:
            stdout:
                class: logging.StreamHandler
                formatter: debug
                stream: ext://sys.stdout
        formatters:
            debug:
                format: '%(asctime)s [%(levelname)s] %(name)s Thread(id=%(thread)d, name="%(threadName)s") %(message)s'
        """))

        path_file_mapping = {"/tmp/dev/app.yml": app_yml_file,
                             "/tmp/dev/bundles.yml": bundles_yml_file,
                             "/tmp/dev/logging.yml": logging_yml_file}
        self._stub_out_path_and_open(path_file_mapping)

        sys.argv = ("blueberrypy -C /tmp serve").split()
        main()
        self.assertIsInstance(blueberrypy.email._mailer, blueberrypy.email.Mailer)
        self.assertIsInstance(cherrypy.engine.logging, blueberrypy.plugins.LoggingPlugin)
        self.assertEqual(cherrypy.lib.sessions.RedisSession, blueberrypy.session.RedisSession)
        self.assertIsInstance(cherrypy.engine.sqlalchemy, blueberrypy.plugins.SQLAlchemyPlugin)
        self.assertIsInstance(cherrypy.tools.orm_session, blueberrypy.tools.SQLAlchemySessionTool)
        self.assertIsInstance(blueberrypy.template_engine.jinja2_env, jinja2.Environment)
        self.assertIsInstance(blueberrypy.template_engine.jinja2_env.assets_environment, webassets.Environment)

    def test_setup_controller(self):
        app_yml_file = FakeFile(textwrap.dedent("""
        global:
            engine.sqlalchemy.on: true
            environment: test_suite
        controllers:
            '':
                controller: !!python/name:tests.test_command.Root
                /:
                    tools.sessions.storage_type: redis
                    tools.orm_session.on: true
        sqlalchemy_engine:
            url: sqlite://
        email:
            host: localhost
            port: 1025
        """))
        path_file_mapping = {"/tmp/dev/app.yml": app_yml_file}
        self._stub_out_path_and_open(path_file_mapping)

        sys.argv = ("blueberrypy -C /tmp serve").split()
        main()

        app_config = load_yaml(app_yml_file.getvalue())
        controller_config = app_config["controllers"][''].copy()
        controller_config.pop("controller")

        merged_app_config = cherrypy.tree.apps[""].config
        for k, v in controller_config.iteritems():
            self.assertEqual(v, merged_app_config[k])

        for k, v in app_config["global"].iteritems():
            self.assertEqual(v, merged_app_config["global"][k])

        for k, v in app_config["email"].iteritems():
            self.assertEqual(v, merged_app_config["email"][k])

        for k, v in app_config["sqlalchemy_engine"].iteritems():
            self.assertEqual(v, merged_app_config["sqlalchemy_engine"][k])

    def test_setup_rest_controller(self):
        app_yml_file = FakeFile(textwrap.dedent("""
        global:
            engine.sqlalchemy.on: true
            environment: test_suite
        controllers:
            /api:
                controller: !!python/name:tests.test_command.rest_controller
                /:
                    tools.sessions.storage_type: redis
                    tools.orm_session.on: true
        sqlalchemy_engine:
            url: sqlite://
        email:
            host: localhost
            port: 1025
        """))
        path_file_mapping = {"/tmp/dev/app.yml": app_yml_file}
        self._stub_out_path_and_open(path_file_mapping)

        sys.argv = ("blueberrypy -C /tmp serve").split()
        main()

        app_config = load_yaml(app_yml_file.getvalue())
        controller_config = app_config["controllers"]['/api'].copy()
        controller = controller_config.pop("controller")
        controller_config["/"].update({"request.dispatch": controller})

        merged_app_config = cherrypy.tree.apps["/api"].config
        for k, v in controller_config.iteritems():
            self.assertEqual(v, merged_app_config[k])

        for k, v in app_config["global"].iteritems():
            self.assertEqual(v, merged_app_config["global"][k])

        for k, v in app_config["email"].iteritems():
            self.assertEqual(v, merged_app_config["email"][k])

        for k, v in app_config["sqlalchemy_engine"].iteritems():
            self.assertEqual(v, merged_app_config["sqlalchemy_engine"][k])

    def test_bind(self):
        self._setup_basic_app_config()

        # hack to get around problem with not being able to acquire a port
        # after listening on a different ip/port in a previous test 
        old_cherrypy_engine_start = cherrypy.engine.start
        def dummy_start(self):
            pass
        cherrypy.engine.start = dummy_start.__get__(cherrypy.engine, cherrypy.engine.__class__)

        sys.argv = "blueberrypy -C /tmp serve -b 0.0.0.0:9090".split()

        try:
            main()
            self.assertEqual(cherrypy.server.bind_addr, ("0.0.0.0", 9090))
        finally:
            cherrypy.engine.start = old_cherrypy_engine_start
