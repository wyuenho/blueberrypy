import logging
import os.path
import sys

try:
    from logging.config import dictConfig
except:
    from logutils.dictconfig import dictConfig

import cherrypy

from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


logger = logging.getLogger(__name__)


# TODO
class ConfigurationValidator(object):
    pass


class BlueberryPyConfiguration(object):

    def __init__(self, config_dir=None, app_config=None, environment=None):

        if app_config:
            self.app_config = dict(app_config)
        else:
            if config_dir is None:
                self.config_dir = config_dir = os.path.join(os.getcwdu(), "config")
            else:
                self.config_dir = config_dir = os.path.abspath(config_dir)

            if environment == "production":
                self.config_dir = config_dir = os.path.join(config_dir, "prod")
            else:
                self.config_dir = config_dir = os.path.join(config_dir, "dev")

            self.app_yml_path = os.path.join(config_dir, "app.yml")
            self.logging_yml_path = os.path.join(config_dir, "logging.yml")
            self.bundles_yml_path = os.path.join(config_dir, "bundles.yml")

            if os.path.exists(self.app_yml_path):
                with open(self.app_yml_path) as app_yml:
                    self.app_config = load(app_yml, Loader)

    @property
    def config_file_paths(self):
        paths = []

        if self.app_yml_path and os.path.exists(self.app_yml_path):
            paths.append(self.app_yml_path)

        if self.logging_yml_path and os.path.exists(self.logging_yml_path):
            paths.append(self.logging_yml_path)

        if self.bundles_yml_path and os.path.exists(self.bundles_yml_path):
            paths.append(self.bundles_yml_path)

        return paths

    def __ensure_configured(f):
        def _f(self, *args, **kwargs):
            if hasattr(self, "app_config") and self.app_config:
                return f(self, *args, **kwargs)
        return _f

    @property
    @__ensure_configured
    def project_metadata(self):
        return self.app_config["project_metadata"]

    @property
    @__ensure_configured
    def cherrypy_environment(self):
        return self.app_config["global"].get("environment")

    @property
    @__ensure_configured
    def use_redis(self):
        for section in self.app_config.itervalues():
            if ("tools.sessions.storage_type" in section and
                 section["tools.sessions.storage_type"] == "redis"):
                return True
        return False

    @property
    @__ensure_configured
    def use_sqlalchemy(self):
        return self.app_config["global"].get("engine.sqlalchemy.on")

    @property
    @__ensure_configured
    def use_jinja2(self):
        return "jinja2" in self.app_config

    @property
    @__ensure_configured
    def use_webassets(self):
        return self.use_jinja2 and self.app_config["jinja2"].get("use_webassets")

    @property
    @__ensure_configured
    def use_controller(self):
        return "controller" in self.app_config["controllers"]

    @property
    @__ensure_configured
    def use_rest_controller(self):
        return "rest_controller" in self.app_config["controllers"]

    @property
    @__ensure_configured
    def controllers_config(self):
        return self.app_config["controllers"]

    @property
    def logging_config(self):
        if self.config_dir and os.path.exists(self.logging_yml_path):
            with open(self.logging_yml_path) as logging_yml:
                return load(logging_yml, Loader)

    @property
    def webassets_env(self):
        from webassets.loaders import YAMLLoader
        if self.config_dir and os.path.exists(self.bundles_yml_path):
            return YAMLLoader(self.bundles_yml_path).load_environment()

    @property
    @__ensure_configured
    def jinja2_config(self):
        conf = self.app_config["jinja2"].copy()
        conf.pop("use_webassets", None)
        return conf

    @property
    @__ensure_configured
    def sqlalchemy_config(self):
        if self.use_sqlalchemy:
            if "sqlalchemy_engine" in self.app_config:
                saconf = self.app_config["sqlalchemy_engine"].copy()
                return {"sqlalchemy_engine": saconf}
            else:
                return dict([(k, v) for k, v in self.app_config.iteritems() if k.startswith("sqlalchemy_engine")])
