import cherrypy

from blueberrypy.plugins import SQLAlchemyPlugin

class EngineTest(object):

    def engine(self):
        return str(cherrypy.engine.sqlalchemy.engine)
    engine.exposed = True

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


saconf = {'sqlalchemy_engine': {'url': 'sqlite://'}}
cherrypy.engine.sqlalchemy = SQLAlchemyPlugin(cherrypy.engine, saconf)
cherrypy.config.update({'environment': 'test_suite',
                        'engine.sqlalchemy.on': True})
cherrypy.tree.mount(EngineTest())
