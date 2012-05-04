import difflib
import inspect
import logging
import os.path
import textwrap
import warnings
import collections

import cherrypy

from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from blueberrypy.email import Mailer
from blueberrypy.exc import BlueberryPyNotConfiguredError, \
    BlueberryPyConfigurationError


logger = logging.getLogger(__name__)


class BlueberryPyConfiguration(object):

    def __init__(self, config_dir=None, app_config=None, logging_config=None,
                 webassets_env=None, environment=None):
        """Loads BlueberryPy configuration from `config_dir` if supplied.
        
        If `app_config` or `logging_config` or `webassets_env` are given, they
        will be used instead of the configuration files found from `config_dir`.
        
        If `environment` is given, it must be an existing CherryPy environment.
        If `environment` is `production`, and `config_dir` is given, the `prod`
        subdirectory will be searched for configuration files, otherwise the
        `dev` subdirectory` will be searched.
        
        Upon initialization of this configuration object, all the configuration
        will be validated for sanity and either BlueberryPyConfigurationError or
        BlueberryPyNotConfiguredError will be thrown if insane. For less severe
        configuration insanity cases, a warning will be emitted instead.
        
        :arg config_dir: a path, str
        :arg app_config: a CherryPy config, dict
        :arg logging_config: a logging config, dict
        :arg webassets_env: a webassets environment, webassets.Environment
        :arg environment: a CherryPy configuration environment, str
        """

        if config_dir is None:
            self.config_dir = config_dir = os.path.join(os.getcwdu(), "config")
        else:
            self.config_dir = config_dir = os.path.abspath(config_dir)

        if environment == "production":
            self.config_dir = config_dir = os.path.join(config_dir, "prod")
        elif environment == "test_suite" and os.path.exists(os.path.join(config_dir, "test")):
            self.config_dir = config_dir = os.path.join(config_dir, "test")
        else:
            self.config_dir = config_dir = os.path.join(config_dir, "dev")


        config_file_paths = {}
        app_yml_path = os.path.join(config_dir, "app.yml")
        logging_yml_path = os.path.join(config_dir, "logging.yml")
        bundles_yml_path = os.path.join(config_dir, "bundles.yml")

        if os.path.exists(app_yml_path):
            config_file_paths["app_yml"] = app_yml_path

        if os.path.exists(logging_yml_path):
            config_file_paths["logging_yml"] = logging_yml_path

        if os.path.exists(bundles_yml_path):
            config_file_paths["bundles_yml"] = bundles_yml_path

        self._config_file_paths = config_file_paths


        if "app_yml" in config_file_paths and not app_config:
            with open(config_file_paths["app_yml"]) as app_yml:
                self._app_config = load(app_yml, Loader)

        if "logging_yml" in config_file_paths and not logging_config:
            with open(config_file_paths["logging_yml"]) as logging_yml:
                self._logging_config = load(logging_yml, Loader)

        if "bundles_yml" in config_file_paths and not webassets_env:
            from webassets.loaders import YAMLLoader
            self._webassets_env = YAMLLoader(config_file_paths["bundles_yml"]).load_environment()


        if app_config:
            self._app_config = dict(app_config)

        if logging_config:
            self._logging_config = dict(logging_config)

        if webassets_env is not None:
            self._webassets_env = webassets_env

        self.validate()

        if environment == "weberror":
            self.setup_weberror_environment()

    @property
    def config_file_paths(self):
        if self._config_file_paths:
            sorted_kv_pairs = tuple(((k, self._config_file_paths[k]) for k in sorted(self._config_file_paths.iterkeys())))
            paths = collections.namedtuple("config_file_paths", [e[0] for e in sorted_kv_pairs])
            return paths(*[e[1] for e in sorted_kv_pairs])

    @property
    def project_metadata(self):
        return self.app_config["project_metadata"]

    @property
    def use_logging(self):
        return self.app_config.get("global", {}).get("engine.logging.on", False)

    @property
    def use_redis(self):
        if self.controllers_config:
            for _, controller_config in self.controllers_config.iteritems():
                controller_config = controller_config.copy()
                controller_config.pop("controller")
                for path_config in controller_config.itervalues():
                    if path_config.get("tools.sessions.storage_type") == "redis":
                        return True
        return False

    @property
    def use_sqlalchemy(self):
        return self.app_config.get("global", {}).get("engine.sqlalchemy.on", False)

    @property
    def use_jinja2(self):
        return "jinja2" in self.app_config

    @property
    def use_webassets(self):
        return self.use_jinja2 and self.app_config["jinja2"].get("use_webassets", False)

    @property
    def use_email(self):
        return "email" in self.app_config

    @property
    def controllers_config(self):
        return self.app_config.get("controllers")

    @property
    def app_config(self):
        return self._app_config

    @property
    def logging_config(self):
        return getattr(self, "_logging_config", None)

    @property
    def webassets_env(self):
        return getattr(self, "_webassets_env", None)

    @property
    def jinja2_config(self):
        if self.use_jinja2:
            conf = self.app_config["jinja2"].copy()
            conf.pop("use_webassets", None)
            return conf

    @property
    def sqlalchemy_config(self):
        if self.use_sqlalchemy:
            if "sqlalchemy_engine" in self.app_config:
                saconf = self.app_config["sqlalchemy_engine"].copy()
                return {"sqlalchemy_engine": saconf}
            else:
                return dict([(k, v) for k, v in self.app_config.iteritems()
                             if k.startswith("sqlalchemy_engine")])

    @property
    def email_config(self):
        return self.app_config.get("email")

    def setup_weberror_environment(self):
        """Returns a new copy of this configuration object configured to run
        under the weberror environment and ensure the weberror environment
        is created for cherrypy's config object."""

        try:
            from weberror.evalexception import EvalException
        except ImportError:
            warnings.warn("WebError not installed")
            return

        cherrypy._cpconfig.environments["weberror"] = {
            "log.wsgi": True,
            "request.throw_errors": True,
            "log.screen": False,
            "engine.autoreload_on": False
        }

        def remove_error_options(section):
            section.pop("request.handler_error", None)
            section.pop("request.error_response", None)
            section.pop("tools.err_redirect.on", None)
            section.pop("tools.log_headers.on", None)
            section.pop("tools.log_tracebacks.on", None)

            for k in section.copy().iterkeys():
                if k.startswith("error_page.") or \
                        k.startswith("request.error_page."):
                    section.pop(k)

        for section_name, section in self.app_config.iteritems():
            if section_name.startswith("/") or section_name == "global":
                remove_error_options(section)

        wsgi_pipeline = []
        if "/" in self.app_config:
            wsgi_pipeline = self.app_config["/"].get("wsgi.pipeline", [])
        else:
            self.app_config["/"] = {}

        wsgi_pipeline.insert(0, ("evalexc", EvalException))

        self.app_config["/"]["wsgi.pipeline"] = wsgi_pipeline

    def validate(self):
        # no need to check for cp config, which will be checked on startup

        if not hasattr(self, "_app_config") or not self.app_config:
            raise BlueberryPyNotConfiguredError("BlueberryPy application configuration not found.")

        if self.use_sqlalchemy and not self.sqlalchemy_config:
            raise BlueberryPyNotConfiguredError("SQLAlchemy configuration not found.")

        if self.use_webassets:
            if self.webassets_env is None:
                raise BlueberryPyNotConfiguredError("Webassets configuration not found.")
            elif len(self.webassets_env) == 0:
                raise BlueberryPyNotConfiguredError("No bundles found in webassets env.")

        if self.use_jinja2 and not self.jinja2_config:
            raise BlueberryPyNotConfiguredError("Jinja2 configuration not found.")

        if self.use_logging and not self.logging_config:
            warnings.warn("BlueberryPy application-specific logging "
                          "configuration not found. Continuing without "
                          "BlueberryPy's logging plugin.")

        if self.use_email:
            if not self.email_config:
                warnings.warn("BlueberryPy email configuration is empty.")
            else:
                mailer_ctor_argspec = inspect.getargspec(Mailer.__init__)
                argnames = frozenset(mailer_ctor_argspec.args[1:])
                for key in self.email_config.iterkeys():
                    if key not in argnames:
                        closest_match = difflib.get_close_matches(key, argnames, 1)
                        closest_match = (closest_match and " Did you mean %r?" % closest_match[0]) or ""
                        warnings.warn(("Unknown key %r found for [email]." % key) + closest_match)

        if not self.controllers_config:
            raise BlueberryPyConfigurationError("You must declare at least one controller.")
        else:
            for script_name, section in self.controllers_config.iteritems():
                controller = section.get("controller")
                if controller is None:
                    raise BlueberryPyConfigurationError("You must define a controller in the [controllers][%s] section." % script_name)
                elif isinstance(controller, cherrypy.dispatch.RoutesDispatcher):
                    if not controller.controllers:
                        warnings.warn("Controller %r has no connected routes." % script_name)
                else:
                    for member_name, member_obj in inspect.getmembers(controller):
                        if member_name == "exposed" and member_obj:
                            break
                        elif (hasattr(member_obj, "exposed") and
                              member_obj.exposed == True):
                            break
                    else:
                        raise warnings.warn("Controller %r has no exposed method." % script_name)
