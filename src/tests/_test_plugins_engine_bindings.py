import cherrypy

from sqlalchemy import Column, Unicode
from sqlalchemy.ext.declarative import declarative_base

from blueberrypy.plugins import SQLAlchemyPlugin

class EngineBindingsTest(object):

    def engine_bindings(self):
        return str(sorted(cherrypy.engine.sqlalchemy.engine_bindings.iteritems()))
    engine_bindings.exposed = True

    def exit(self):
        # This handler might be called before the engine is STARTED if an
        # HTTP worker thread handles it before the HTTP server returns
        # control to engine.start. We avoid that race condition here
        # by waiting for the Bus to be STARTED.
        cherrypy.engine.wait(state=cherrypy.engine.states.STARTED)
        cherrypy.engine.exit()
    exit.exposed = True


def log_test_case_name():
    if cherrypy.config.get('test_case_name', False):
        cherrypy.log("STARTED FROM: %s" % cherrypy.config.get('test_case_name'))
cherrypy.engine.subscribe('start', log_test_case_name, priority=6)


Base = declarative_base()
class User(Base):
    __tablename__ = 'user'
    name = Column(Unicode, primary_key=True)

class Group(Base):
    __tablename__ = 'group'
    name = Column(Unicode, primary_key=True)


saconf = {'sqlalchemy_engine_tests._test_plugins_engine_bindings.User':
          {'url': "sqlite://"},
          'sqlalchemy_engine_tests._test_plugins_engine_bindings.Group':
          {'url': "sqlite://"}}
cherrypy.engine.sqlalchemy = SQLAlchemyPlugin(cherrypy.engine, saconf)
cherrypy.config.update({'environment': 'test_suite',
                        'engine.sqlalchemy.on': True})
cherrypy.tree.mount(EngineBindingsTest())
