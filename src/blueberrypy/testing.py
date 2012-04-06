import cherrypy

from cherrypy.test.helper import CPWebCase

from blueberrypy.config import BlueberryPyConfiguration
from blueberrypy import email
from blueberrypy.plugins import LoggingPlugin
from blueberrypy.session import RedisSession
from blueberrypy.plugins import SQLAlchemyPlugin
from blueberrypy.tools import SQLAlchemySessionTool
from blueberrypy.template_engine import configure_jinja2


from testconfig import config as testconfig


class ControllerTestCase(CPWebCase):

    @staticmethod
    def setup_server():

        config = BlueberryPyConfiguration(app_config=testconfig)

        if config.use_email and config.email_config:
            email.configure(config.email_config)

        if config.use_logging and config.logging_config:
            cherrypy.engine.logging = LoggingPlugin(cherrypy.engine,
                                                    config=config.logging_config)

        if config.use_redis:
            cherrypy.lib.sessions.RedisSession = RedisSession

        if config.use_sqlalchemy:
            cherrypy.engine.sqlalchemy = SQLAlchemyPlugin(cherrypy.engine,
                                                          config=config.sqlalchemy_config)
            cherrypy.tools.orm_session = SQLAlchemySessionTool()

        if config.use_jinja2:
            if config.webassets_env:
                configure_jinja2(assets_env=config.webassets_env,
                                        **config.jinja2_config)
            else:
                configure_jinja2(**config.jinja2_config)

        cherrypy.config.update(config.app_config)

        if config.use_controller:
            controllers_config = config.controllers_config
            controller = controllers_config["controller"]
            script_name = controllers_config.get("script_name", '')
            cherrypy.tree.mount(controller(),
                                script_name=script_name,
                                config=config.app_config)

        if config.use_rest_controller:
            controllers_config = config.controllers_config
            rest_controller = controllers_config["rest_controller"]
            rest_config = {"/": {"request.dispatch": rest_controller}}
            extra_rest_config = controllers_config.get("rest_config", {})
            for k in extra_rest_config.iterkeys():
                if k in rest_config:
                    rest_config[k].update(extra_rest_config[k])
                else:
                    rest_config[k] = dict(extra_rest_config[k])
            rest_script_name = controllers_config.get("rest_script_name", "/api")
            cherrypy.tree.mount(None,
                                script_name=rest_script_name,
                                config=rest_config)
