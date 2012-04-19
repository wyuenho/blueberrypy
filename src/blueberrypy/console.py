import os
import sys
from code import InteractiveConsole


class Console(InteractiveConsole):

    def __init__(self, config):

        self.config = config

        try:
            import readline
        except ImportError, e:
            print(e)
        else:
            import rlcompleter

        startupfile = os.environ.get("PYTHONSTARTUP")
        if startupfile: execfile(startupfile, {}, {})

        proj_meta = config.project_metadata
        if proj_meta:
            package = proj_meta.get("package", None)

            sys.ps1 = "[%s]>>> " % package
            sys.ps2 = "[%s]... " % package

            self.prompt = package

        InteractiveConsole.__init__(self, locals=self.get_locals())

    def make_sqlalchemy_engine(self, prefix="sqlalchemy_engine"):

        config = self.config.sqlalchemy_config

        if prefix in config:
            section = config[prefix]
            from sqlalchemy.engine import engine_from_config
            return engine_from_config(section, '')
        else:
            engine_bindings = {}
            for section_name, section in config.iteritems():
                if section_name.startswith(prefix):
                    model_fqn = section_name[len(prefix) + 1:]
                    model_fqn_parts = model_fqn.rsplit('.', 1)
                    model_mod = __import__(model_fqn_parts[0], globals(), locals(), [model_fqn_parts[1]])
                    model = getattr(model_mod, model_fqn_parts[1])
                    engine_bindings[model] = engine_from_config(section)
            return engine_bindings

    def get_locals(self):
        import sys, os, os.path, time, datetime, pprint, inspect
        import sqlalchemy
        import sqlalchemy.orm
        import cherrypy
        import blueberrypy

        lcls = dict(locals())

        package_name = self.config.project_metadata and self.config.project_metadata["package"]
        if package_name:
            model = __import__(package_name + ".model", globals(), locals(), ["model"])
            if getattr(model, '__all__'):
                for name in model.__all__:
                    lcls[name] = getattr(model, name)
            else:
                for name, obj in vars(model).iteritems():
                    if not name.startswith("_"):
                        lcls[name] = obj

        if self.config.use_sqlalchemy:
            engine = self.make_sqlalchemy_engine()
            if isinstance(engine, dict):
                Session = sqlalchemy.orm.sessionmaker(twophase=True)
                Session.configure(binds=engine)
            else:
                Session = sqlalchemy.orm.sessionmaker()
                Session.configure(bind=engine)
            metadata = model.metadata
            metadata.bind = engine
            lcls['create_all'] = metadata.create_all
            lcls['drop_all'] = metadata.drop_all
            lcls['session'] = session = Session()
            session.bind.echo = True
            import atexit
            atexit.register(session.close)

        return lcls

    def raw_input(self, *args, **kw):
        try:
            r = InteractiveConsole.raw_input(self, *args, **kw)
            for encoding in (getattr(sys.stdin, 'encoding', None),
                             sys.getdefaultencoding(), 'utf-8', 'latin-1'):
                if encoding:
                    try:
                        return r.decode(encoding)
                    except UnicodeError:
                        pass
                    return r
        except EOFError:
            self.write(os.linesep)
            session = self.locals.get("session")
            if session is not None and \
                session.new or \
                session.dirty or \
                session.deleted:

                r = raw_input("Do you wish to commit your "
                              "database changes? [Y/n]")
                if not r.lower().startswith("n"):
                    self.push("session.flush()")
            raise
