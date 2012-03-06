import logging

from sqlalchemy.engine import engine_from_config

try:
    from logging.config import dictConfig
except ImportError:
    from logutils.dictconfig import dictConfig

from cherrypy.process.plugins import SimplePlugin


__all__ = ['LoggingPlugin', 'SQLAlchemyPlugin']


class LoggingPlugin(SimplePlugin):
    """ Sets up process-wide application specific loggers
    """

    def __init__(self, bus,
                 raiseExceptions=logging.raiseExceptions,
                 config={}):

        SimplePlugin.__init__(self, bus)

        self.raiseExceptions = raiseExceptions
        self.config = config

    def start(self):
        try:
            logging.raiseExceptions = self.raiseExceptions
            dictConfig(self.config)
            self.bus.log("Loggers configured")
        except Exception:
            self.bus.log(traceback=True)
    start.priority = 80

    def exit(self):
        self.bus.log("Flushing and closing loggers.")
        logging.shutdown()


class SQLAlchemyPlugin(SimplePlugin):
    """Sets up process-wide SQLAlchemy engines.
    
    This plugin setups basic machinary to attach and clean up engine bindings.
    Engine bindings are in the exact format as the `binds` keyword in
    `Session.configure()`.
    
    In the future in case we ever get to horizontal sharding, this plugin will
    need to be updated.
    """

    def __init__(self, bus, config, prefix="sqlalchemy_engine"):
        SimplePlugin.__init__(self, bus)
        self.config = config
        self.prefix = prefix

    def start(self):
        self._configure_engines()
        self.bus.log("SQLAlchemy Plugin started")
    start.priority = 83

    def graceful(self):
        if hasattr(self, "engine_bindings"):
            engine_bindings = self.engine_bindings
            for engine in engine_bindings.itervalues():
                self.bus.log("Disposing SQLAlchemy engine %s ..." % engine.url)
                engine.dispose()
        elif hasattr(self, "engine"):
            engine = self.engine
            self.bus.log("Disposing SQLAlchemy engine %s ..." % engine.url)
            engine.dispose()
    stop = graceful

    def _configure_engines(self):
        """Sets up engine bindings based on the given config.
        
        Given a configuration dictionary, and optionally a key `prefix`, this
        method iterates all its sections looking for sections with names that
        start with `prefix`. The suffix of the name is fully qualified name to
        a model. A SQLAlchemy engine is then set up with the section value as
        configuration parameters to `sqlalchemy.engine_form_config`. The
        configured engine bindings are to be found in
        `cherrypy.engine.sqlalchemy.engine_bindings` (or wherever you've
        attached this plugin to).
        
        If there is a section that is named exactly the same as the `prefix`,
        that section's values are use to configure only one SQLAlchemy engine
        attached to `cherrypy.engine.sqlalchemy.engine`.
        
        Example::
        
            # The model to be imported starts after the _ following the prefix
            [sqlalchemy_engine_myproject.models.User]
            url = ...
            pool_recycle = ...
            
            # If this section exists, only 1 engine will be configured
            [sqlalchemy_engine]
            url = ...
        
        
        :py:func: sqlalchemy.engine_from_config
        """

        if self.prefix in self.config:
            section = self.config[self.prefix]
            self.engine = engine_from_config(section, '')
            self.bus.log("SQLAlchemy engine configured")
        else:
            engine_bindings = {}

            for section_name, section in self.config.iteritems():
                if section_name.startswith(self.prefix):
                    model_fqn = section_name[len(self.prefix) + 1:]
                    model_fqn_parts = model_fqn.rsplit('.', 1)
                    model_mod = __import__(model_fqn_parts[0], globals(), locals(), [model_fqn_parts[1]])
                    model = getattr(model_mod, model_fqn_parts[1])
                    engine_bindings[model] = engine_from_config(section, '')

            self.engine_bindings = engine_bindings

            self.bus.log("SQLAlchemy engines configured")
