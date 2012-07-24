import logging
import warnings

import cherrypy
from cherrypy._cptools import Tool, _getargs

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError


__all__ = ["SQLAlchemySessionTool"]


logger = logging.getLogger(__name__)


class MultiHookPointTool(Tool):
    """MultiHookPointTool provides subclasses the infrastructure for writing
    Tools that need to run at more than one request hook point.
    
    Subclasses can simply provide methods with the same name as the hook points
    and MuiltiHookPointTool will automatically wire each hook up to the request
    hook points when turned on in the configuration.
    """

    def __init__(self, name=None, priority=50):
        """Subclasses of MultiHookPointTool do not need to provide a default
        hook point and a callable because there's no such thing. As such,
        subclasses will most likely only provide a default priority for the
        hook point callables the subclasses provide.
        
        Same as the Tool class CherryPy supplies, the `name` parameter is set
        automatically when a MultiHookPointTool instance is attached to a
        ToolBox if not supplied.
        
        Lastly, similar to Tool, this constructor will also loop through all
        the hooks and attach their arguments directly to the Tool instance.
        The only difference is all the tool arguments are prefixed with their
        hook point names to avoid name conflicts.
        
        Example::
            
            app_config = {
                "/": {
                    "tools.my_multipoint_tool.on": True,
                    "tools.my_multipoint_tools.before_handler.echo": True,
                    "tools.my_multipoint_tools.before_finalize.priority": 80
                }
            }
        """
        self._name = name
        self._priority = priority
        self._setargs()

    def _setargs(self):
        for hook_point in cherrypy._cprequest.hookpoints:
            if hasattr(self, hook_point):
                hook = getattr(self, hook_point)
                try:
                    for arg in _getargs(hook):
                        setattr(self, hook_point + "_" + arg, None)
                # IronPython 1.0 raises NotImplementedError because
                # inspect.getargspec tries to access Python bytecode
                # in co_code attribute.
                except NotImplementedError:
                    pass
                # IronPython 1B1 may raise IndexError in some cases,
                # but if we trap it here it doesn't prevent CP from working.
                except IndexError:
                    pass

    def _setup(self):

        request = cherrypy.request

        conf = self._merged_args()

        for hook_point in cherrypy._cprequest.hookpoints:

            if hasattr(self, hook_point):
                hook = getattr(self, hook_point)
                if not callable(hook):
                    warnings.warn("%r is not a callable." % hook)

                hook_conf = {}
                for k, v in conf.iteritems():
                    if k.startswith(hook_point):
                        k = k.replace(hook_point, "").split(".", 1)[-1]
                        hook_conf[k] = v

                priority_key = hook_point + ".priority"
                hook_priority = self._priority if priority_key not in hook_conf else hook_conf[priority_key]
                request.hooks.attach(hook_point, hook, hook_priority, **hook_conf)

    def __call__(self, *args, **kwargs):
        raise NotImplementedError("This %r instance cannot be called directly." % \
            self.__class__.__name__)


class SQLAlchemySessionTool(MultiHookPointTool):
    """A CherryPy tool to process SQLAlchemy ORM sessions for requests.

    This tools sets up a scoped, possibly multi-engine SQLAlchemy ORM session to
    `cherrypy.request.orm_session` at the beginning of a request. This tool does
    not commit changes for you automatically, you must do you explicitly inside
    your controller code. At the end of each requests, this tool will rollback
    if errors occured. The session is guaranteed to be removed from the request
    in the end.

    As this tool hooks up _3_ callables to the request, this tools will also
    accept 3 `priority` options - `on_start_resource.priority`, 
    `before_finalize.priority` and `after_error_response.priority`. The `priority`
    option is still accepted as a default for all 3 hook points.
    """

    def on_start_resource(self, bindings=None):
        if bindings:

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
