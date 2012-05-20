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

        # mount the controllers
        for script_name, section in config.controllers_config.iteritems():
            section = section.copy()
            controller = section.pop("controller")
            if isinstance(controller, cherrypy.dispatch.RoutesDispatcher):
                routes_config = {'/': {"request.dispatch": controller}}
                for path in section.iterkeys():
                    if path.strip() == '/':
                        routes_config['/'].update(section['/'])
                    else:
                        routes_config[path] = section[path].copy()
                app_config = config.app_config.copy()
                app_config.pop("controllers")
                routes_config.update(app_config)
                cherrypy.tree.mount(None, script_name=script_name,
                                    config=routes_config)
            else:
                app_config = config.app_config.copy()
                app_config.pop("controllers")
                controller_config = section.copy()
                controller_config.update(app_config)
                cherrypy.tree.mount(controller(), script_name=script_name,
                                    config=controller_config)

