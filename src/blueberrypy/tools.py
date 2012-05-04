import logging

import cherrypy
from cherrypy import Tool

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError


__all__ = ["SQLAlchemySessionTool"]


logger = logging.getLogger(__name__)


class SQLAlchemySessionTool(Tool):
    """A CherryPy tool to process SQLAlchemy ORM sessions for requests.

    This tools sets up a scoped, possibly multi-engine SQLAlchemy ORM session to
    `cherrypy.request.orm_session` at the beginning of a request. This tool does
    not commit changes for you automatically, you must do you explicitly inside
    your controller code. At the end of each requests, this tool will rollback
    if errors occured. The session is guaranteed to be removed from the request
    in the end.

    As this tool hooks up _3_ callables to the request, this tools will also
    accept 3 `priority` options - `on_start_resource_priority`, 
    `before_finalize_priority` and `after_error_response`. The `priority` option
    is still accepted as a default for all 3 hook points.
    """

    def __init__(self):
        doc = self.__doc__
        Tool.__init__(self, "on_start_resource", self.on_start_resource)
        # Revert the changed doc Tool.__init__ did.
        self.__doc__ = doc
        # Remove the self attr set by _setargs().
        del self.self

    def __call__(self, *args, **kwargs):
        raise NotImplementedError, "This %r instance cannot be called directly." % \
            self.__class__.__name__

    def _setup(self):
        request = cherrypy.request
        conf = self._merged_args()

        if "bindings" in conf:
            self.bindings = conf["bindings"]
        if "passable_exceptions" in conf:
            self.passable_exceptions = conf["passable_exceptions"]

        on_start_resource_priority = conf.pop("on_start_resource_priority", 10)
        if on_start_resource_priority is None:
            on_start_resource_priority = getattr(self.on_start_resource, "priority",
                                                 self._priority)
        request.hooks.attach(self._point, self.on_start_resource,
                             priority=on_start_resource_priority)

        before_finalize_priority = conf.pop("before_finalize_priority", None)
        if before_finalize_priority is None:
            before_finalize_priority = getattr(self.before_finalize, "priority",
                                               self._priority)
        request.hooks.attach("before_finalize", self.before_finalize,
                             priority=before_finalize_priority)

        after_error_response_priority = conf.pop("after_error_response_priority",
                                                 None)
        if after_error_response_priority is None:
            after_error_response_priority = getattr(self.after_error_response,
                                                    "priority", self._priority)
        request.hooks.attach("after_error_response", self.after_error_response,
                             priority=after_error_response_priority)

    def on_start_resource(self):
        if hasattr(self, "bindings"):

            bindings = self.bindings

            if len(bindings) > 1:
                Session = scoped_session(sessionmaker(twophase=True))
            else:
                Session = scoped_session(sessionmaker())

            session_bindings = {}
            engine_bindings = cherrypy.engine.sqlalchemy.engine_bindings
            for binding in bindings:
                session_bindings[binding] = engine_bindings[binding]

            Session.configure(binds=session_bindings)

        else:
            Session = scoped_session(sessionmaker())
            Session.configure(bind=cherrypy.engine.sqlalchemy.engine)

        cherrypy.request.orm_session = Session

    def before_finalize(self):
        req = cherrypy.request
        session = req.orm_session
        session.remove()

    def after_error_response(self):
        req = cherrypy.request
        session = req.orm_session

        try:
            session.rollback()
            session.expunge_all()
        except SQLAlchemyError, e:
            logger.error(e, exc_info=True)
            cherrypy.log.error(msg=e, severity=logging.ERROR, traceback=True)
        finally:
            session.remove()
