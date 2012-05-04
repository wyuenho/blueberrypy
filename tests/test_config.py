import __builtin__
import textwrap
try:
    import unittest2 as unittest
except ImportError:
    import unittest
import warnings
from StringIO import StringIO

from jinja2.loaders import DictLoader
from webassets import Environment

from blueberrypy.config import BlueberryPyConfiguration
from blueberrypy.exc import BlueberryPyConfigurationError, BlueberryPyNotConfiguredError


# dummy controllers
import cherrypy

class Root(object):

    def index(self):
        return "hello world!"
    index.exposed = True

class DummyRestController(object):

    def dummy(self, **kwargs):
        return "hello world!"

rest_controller = cherrypy.dispatch.RoutesDispatcher()
rest_controller.connect("dummy", "/dummy", DummyRestController, action="dummy")


class BlueberryPyConfigurationTest(unittest.TestCase):

    def setUp(self):
        self.basic_valid_app_config = {"controllers": {'': {"controller": Root},
                                                       "/api": {"controller": rest_controller,
                                                                '/': {"request.dispatch": rest_controller}}}}

    def test_validate(self):
        self.assertRaisesRegexp(BlueberryPyNotConfiguredError,
                                "BlueberryPy application configuration not found.",
                                BlueberryPyConfiguration)

    def test_config_file_paths(self):
        # stub out os.path.exists
        import os.path
        old_exists = os.path.exists
        def proxied_exists(path):
            if path == "/tmp/dev/app.yml":
                return True
            elif path == "/tmp/dev/bundles.yml":
                return True
            elif path == "/tmp/dev/logging.yml":
                return True
            return old_exists(path)
        os.path.exists = proxied_exists
        old_open = __builtin__.open

        # stub out open
        class FakeFile(StringIO):
            def __enter__(self):
                return self
            def __exit__(self, exc_type=None, exc_value=None, traceback=None):
                return False
        def proxied_open(filename, mode='r', buffering=1):
            if filename == "/tmp/dev/app.yml":
                return FakeFile()
            elif filename == "/tmp/dev/bundles.yml":
                return FakeFile(textwrap.dedent("""
                directory: /tmp
                url: /
                """))
            elif filename == "/tmp/dev/logging.yml":
                return FakeFile()
            else:
                return old_open(filename, mode, buffering)
        __builtin__.open = proxied_open

        # stub out validate()
        old_validate = BlueberryPyConfiguration.validate
        BlueberryPyConfiguration.validate = lambda self: None

        try:
            config = BlueberryPyConfiguration(config_dir="/tmp")
            config_file_paths = config.config_file_paths
            self.assertEqual(len(config_file_paths), 3)
            self.assertEqual(config_file_paths[0], "/tmp/dev/app.yml")
            self.assertEqual(config_file_paths[1], "/tmp/dev/bundles.yml")
            self.assertEqual(config_file_paths[2], "/tmp/dev/logging.yml")
        finally:
            BlueberryPyConfiguration.validate = old_validate
            os.path.exists = old_exists
            __builtin__.open = old_open

    def test_use_email(self):
        app_config = self.basic_valid_app_config.copy()
        app_config.update({"email": {}})

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("error")
            self.assertRaisesRegexp(UserWarning,
                                    "BlueberryPy email configuration is empty.",
                                    callable_obj=BlueberryPyConfiguration,
                                    app_config=app_config)

        app_config.update({"email": {"debug": 1}})
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("error")
            self.assertRaisesRegexp(UserWarning,
                                    "Unknown key 'debug' found for \[email\]. Did you mean 'debuglevel'?",
                                    callable_obj=BlueberryPyConfiguration,
                                    app_config=app_config)

        app_config.update({"email": {"host": "localhost",
                                     "port": 1025}})
        config = BlueberryPyConfiguration(app_config=app_config)
        self.assertTrue(config.use_email)

    def test_use_redis(self):
        app_config = self.basic_valid_app_config.copy()
        config = BlueberryPyConfiguration(app_config=app_config)
        self.assertFalse(config.use_redis)

        app_config["controllers"][''].update({"/": {"tools.sessions.storage_type": "redis"}})

        config = BlueberryPyConfiguration(app_config=app_config)
        self.assertTrue(config.use_redis)

    def test_use_sqlalchemy(self):
        app_config = self.basic_valid_app_config.copy()
        app_config.update({"global": {"engine.sqlalchemy.on": True}})

        self.assertRaisesRegexp(BlueberryPyNotConfiguredError,
                                "SQLAlchemy configuration not found.",
                                callable_obj=BlueberryPyConfiguration,
                                app_config=app_config)

        app_config.update({"global": {"engine.sqlalchemy.on": True},
                           "sqlalchemy_engine": {"url": "sqlite://"}})

        config = BlueberryPyConfiguration(app_config=app_config)
        self.assertTrue(config.use_sqlalchemy)

        app_config.update({"global": {"engine.sqlalchemy.on": True},
                           "sqlalchemy_engine_Model": {"url": "sqlite://"}})

        config = BlueberryPyConfiguration(app_config=app_config)
        self.assertTrue(config.use_sqlalchemy)

    def test_use_jinja2(self):
        app_config = self.basic_valid_app_config.copy()
        app_config.update({"jinja2": {}})
        self.assertRaisesRegexp(BlueberryPyNotConfiguredError,
                                "Jinja2 configuration not found.",
                                callable_obj=BlueberryPyConfiguration,
                                app_config=app_config)

        app_config.update({"jinja2": {"loader": DictLoader({})}})
        config = BlueberryPyConfiguration(app_config=app_config)
        self.assertTrue(config.use_jinja2)

    def test_use_webassets(self):
        app_config = self.basic_valid_app_config.copy()
        app_config.update({"jinja2": {"use_webassets": True,
                                      "loader": DictLoader({})}})
        self.assertRaisesRegexp(BlueberryPyNotConfiguredError,
                                "Webassets configuration not found.",
                                callable_obj=BlueberryPyConfiguration,
                                app_config=app_config)

        webassets_env = Environment("/tmp", "/")
        self.assertRaisesRegexp(BlueberryPyNotConfiguredError,
                                "No bundles found in webassets env.",
                                callable_obj=BlueberryPyConfiguration,
                                app_config=app_config,
                                webassets_env=webassets_env)

        webassets_env = Environment("/tmp", "/")
        webassets_env.register("js", "dummy.js", "dummy2.js", output="dummy.js")
        config = BlueberryPyConfiguration(app_config=app_config,
                                          webassets_env=webassets_env)
        self.assertTrue(config.use_webassets)

    def test_jinja2_config(self):
        app_config = self.basic_valid_app_config.copy()
        dict_loader = DictLoader({})
        app_config.update({"jinja2": {"loader": dict_loader,
                                      "use_webassets": True}})

        webassets_env = Environment("/tmp", "/")
        webassets_env.register("js", "dummy.js", "dummy2.js", output="dummy.js")
        config = BlueberryPyConfiguration(app_config=app_config,
                                          webassets_env=webassets_env)
        self.assertEqual(config.jinja2_config, {"loader": dict_loader})

    def test_sqlalchemy_config(self):
        app_config = self.basic_valid_app_config.copy()
        app_config.update({"global": {"engine.sqlalchemy.on": True},
                           "sqlalchemy_engine": {"url": "sqlite://"}})

        config = BlueberryPyConfiguration(app_config=app_config)
        self.assertEqual(config.sqlalchemy_config, {"sqlalchemy_engine": {"url": "sqlite://"}})

        app_config = self.basic_valid_app_config.copy()
        app_config.update({"global": {"engine.sqlalchemy.on": True},
                           "sqlalchemy_engine_Model1": {"url": "sqlite://"},
                           "sqlalchemy_engine_Model2": {"url": "sqlite://"}})

        config = BlueberryPyConfiguration(app_config=app_config)
        self.assertEqual(config.sqlalchemy_config, {"sqlalchemy_engine_Model1": {"url": "sqlite://"},
                                                    "sqlalchemy_engine_Model2": {"url": "sqlite://"}})

    def test_controllers_config(self):
        app_config = {"global": {}}
        self.assertRaisesRegexp(BlueberryPyConfigurationError,
                                "You must declare at least one controller\.",
                                callable_obj=BlueberryPyConfiguration,
                                app_config=app_config)

        app_config = {"controllers": {}}
        self.assertRaisesRegexp(BlueberryPyConfigurationError,
                                "You must declare at least one controller\.",
                                callable_obj=BlueberryPyConfiguration,
                                app_config=app_config)

        app_config = {"controllers": {'api': {'tools.json_in.on': True}}}
        self.assertRaisesRegexp(BlueberryPyConfigurationError,
                                "You must define a controller in the \[controllers\]\[api\] section\.",
                                callable_obj=BlueberryPyConfiguration,
                                app_config=app_config)

        class Root(object):
            def index(self):
                return "hello world!"

        app_config = {"controllers": {"": {"controller": Root}}}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("error")
            self.assertRaisesRegexp(UserWarning,
                                    "Controller '' has no exposed method\.",
                                    callable_obj=BlueberryPyConfiguration,
                                    app_config=app_config)

        class Root(object):
            def index(self):
                return "hello world!"
            index.exposed = True

        app_config = {"controllers": {"": {"controller": Root}}}
        config = BlueberryPyConfiguration(app_config=app_config)

        rest_controller = cherrypy.dispatch.RoutesDispatcher()

        app_config = {"controllers": {"/api": {"controller": rest_controller}}}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("error")
            self.assertRaisesRegexp(UserWarning,
                                    "Controller '/api' has no connected routes\.",
                                    callable_obj=BlueberryPyConfiguration,
                                    app_config=app_config)

        class DummyRestController(object):
            def dummy(self, **kwargs):
                return "hello world!"

        rest_controller.connect("dummy", "/dummy", DummyRestController, action="dummy")
        app_config = {"controllers": {"/api": {"controller": rest_controller}}}
        config = BlueberryPyConfiguration(app_config=app_config)
