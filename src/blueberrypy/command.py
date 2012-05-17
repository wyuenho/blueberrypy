from __future__ import print_function

import sys
try:
    import cdecimal
    sys.modules["decimal"] = cdecimal
except:
    pass

import argparse
import logging
import os
import re
import textwrap

from datetime import datetime

import cherrypy
from cherrypy.process import servers
from cherrypy.process.plugins import Daemonizer, DropPrivileges, PIDFile

import blueberrypy
from blueberrypy.config import BlueberryPyConfiguration
from blueberrypy.project import create_project
from blueberrypy.console import Console
from blueberrypy.template_engine import configure_jinja2
from blueberrypy.exc import BlueberryPyNotConfiguredError


def create(args, config_dir=None):

    path = None
    if args.path:
        path = os.path.abspath(args.path)
        if not os.path.exists(path):
            os.mkdir(path)
            print("Path not found, a directory '%s' has been created." % path, file=sys.stderr)

    valid_version_re = re.compile(r"^\d+.\d+(.\d+)*(a|b|c|rc\d+(.\d+)?)?(.post\d+)?(.dev\d+)?$")
    valid_email_re = re.compile(r"^.+@.+$")

    blueberrypy_config = {}
    blueberrypy_config["path"] = path or os.getcwdu()
    blueberrypy_config["current_year"] = datetime.now().year

    blueberrypy_config["project_name"] = raw_input("Project name: ")

    while True:
        blueberrypy_config["package"] = package = raw_input("Package name: ")
        if not package:
            print("Package name cannot be empty.", file=sys.stderr)
        else:
            break

    while True:
        blueberrypy_config["version"] = version = raw_input("Version (PEP 386): ")
        if not valid_version_re.match(version):
            print("'%s' does not match the required version format." % version, file=sys.stderr)
        else:
            break

    blueberrypy_config["author"] = raw_input("Author name: ")

    while True:
        blueberrypy_config["email"] = email = raw_input("Email: ")
        if not valid_email_re.match(email):
            print("'%s' is an invalid email address." % email, file=sys.stderr)
        else:
            break

    while True:
        use_controller = raw_input("Use controllers backed by a templating engine? [Y/n] ").lower()
        if use_controller and (not use_controller.startswith('y') and not use_controller.startswith('n')):
            print("Please answer Y or N.", file=sys.stderr)
        else:
            blueberrypy_config["use_controller"] = True if not use_controller or use_controller[0] == 'y' else False
            break

    while True:
        use_rest_controller = raw_input("Use RESTful controllers? [y/N] ").lower()
        if use_rest_controller and (not use_rest_controller.startswith('y') and not use_rest_controller.startswith('n')):
            print("Please answer Y or N.", file=sys.stderr)
        else:
            blueberrypy_config["use_rest_controller"] = False if not use_rest_controller or use_rest_controller[0] == 'n' else True
            break

    if blueberrypy_config["use_controller"]:
        while True:
            use_jinja2 = raw_input("Use Jinja2 templating engine? [Y/n] ").lower()
            if use_jinja2 and (not use_jinja2.startswith('y') and not use_jinja2.startswith('n')):
                print("Please answer Y or N.", file=sys.stderr)
            else:
                blueberrypy_config["use_jinja2"] = True if not use_jinja2 or use_jinja2[0] == 'y' else False
                break

        while True:
            use_webassets = raw_input("Use webassets asset management framework? [Y/n] ").lower()
            if use_webassets and (not use_webassets.startswith('y') and not use_webassets.startswith('n')):
                print("Please answer Y or N.", file=sys.stderr)
            else:
                blueberrypy_config["use_webassets"] = True if not use_webassets or use_webassets[0] == 'y' else False
                break
    else:
        blueberrypy_config["use_jinja2"] = False
        blueberrypy_config["use_webassets"] = False

    while True:
        use_redis = raw_input("Use redis session? [y/N] ").lower()
        if use_redis and (not use_redis.startswith('y') and not use_redis.startswith('n')):
            print("Please answer Y or N.", file=sys.stderr)
        else:
            blueberrypy_config["use_redis"] = False if not use_redis or use_redis[0] == 'n' else True
            break

    while True:
        use_sqlalchemy = raw_input("Use SQLAlchemy ORM? [Y/n] ").lower()
        if use_sqlalchemy and (not use_sqlalchemy.startswith('y') and not use_sqlalchemy.startswith('n')):
            print("Please answer Y or N.", file=sys.stderr)
        else:
            blueberrypy_config["use_sqlalchemy"] = True if not use_sqlalchemy or use_sqlalchemy[0] == 'y' else False
            if blueberrypy_config["use_sqlalchemy"]:
                blueberrypy_config["sqlalchemy_url"] = sqlalchemy_url = raw_input("SQLAlchemy database connection URL: ")
                if sqlalchemy_url.strip():
                    try:
                        from sqlalchemy.engine import url as sa_url
                        blueberrypy_config["driver"] = sa_url.make_url(sqlalchemy_url).get_dialect().driver
                    except ImportError, e:
                        pass
                break
            break

    create_project(blueberrypy_config, dry_run=args.dry_run)

    footer = textwrap.dedent("""
    ===========================================================================
    Your project skeleton has been created under {path}.
 
    Subsystems chosen
    -----------------
    Routes (RESTful controllers): {use_rest_controller}
    Jinja2: {use_jinja2}
    webassets: {use_webassets}
    redis: {use_redis}
    SQLAlchemy: {use_sqlalchemy}
    
    If you now install your package now the packages above will be automatically
    installed as well.

    e.g. $ pip install -e .
 
    In unrestricted environments, you may also install 'MarkupSafe' and
    'cdecimal' to speed up Jinja2 and SQLAlchemy's queries on Decimal fields
    respectively. You may also install 'hiredis' if you have opted for the Redis
    session storage.

    e.g. $ pip install blueberrypy[speedups]
    
    You should also install the appropriate database driver if you have decided
    to use BlueberryPy's SQLAlchemy support.

    For more information, the BlueberryPy documentation is available at
    http://blueberrypy.readthedocs.org.

    Happy coding!
    """.format(**blueberrypy_config))

    print(footer)

def bundle(args, config_dir=None):

    config = BlueberryPyConfiguration(config_dir=config_dir)

    assets_env = config.webassets_env
    if not assets_env:
        raise BlueberryPyNotConfiguredError("Webassets configuration not found.")

    logging.basicConfig()
    logger = logging.getLogger(__name__)

    from webassets.script import CommandLineEnvironment
    assets_cli = CommandLineEnvironment(assets_env, logger)

    if args.build:
        try:
            assets_cli.build()
        except AttributeError:
            assets_cli.rebuild()
    elif args.watch:
        assets_cli.watch()
    elif args.clean:
        assets_cli.clean()

def serve(args, config_dir=None):

    config = BlueberryPyConfiguration(config_dir=config_dir)

    cpengine = cherrypy.engine

    cpenviron = args.environment
    if cpenviron:
        config = BlueberryPyConfiguration(config_dir=config_dir,
                                          environment=cpenviron)
        cherrypy.config.update({"environment": cpenviron})

    if config.use_email and config.email_config:
        from blueberrypy import email
        email.configure(config.email_config)

    if config.use_logging and config.logging_config:
        from blueberrypy.plugins import LoggingPlugin
        cpengine.logging = LoggingPlugin(cpengine, config=config.logging_config)

    if config.use_redis:
        from blueberrypy.session import RedisSession
        cherrypy.lib.sessions.RedisSession = RedisSession

    if config.use_sqlalchemy:
        from blueberrypy.plugins import SQLAlchemyPlugin
        cpengine.sqlalchemy = SQLAlchemyPlugin(cpengine,
                                               config=config.sqlalchemy_config)
        from blueberrypy.tools import SQLAlchemySessionTool
        cherrypy.tools.orm_session = SQLAlchemySessionTool()

    if config.use_jinja2:
        if config.webassets_env:
            configure_jinja2(assets_env=config.webassets_env,
                             **config.jinja2_config)
        else:
            configure_jinja2(**config.jinja2_config)

    # update global config first, so subsequent command line options can
    # override the settings in the config files
    cherrypy.config.update(config.app_config)

    if args.binding:
        address, port = args.binding.strip().split(":")
        cherrypy.server.socket_host = address
        cherrypy.server.socket_port = int(port)

    if args.daemonize:
        cherrypy.config.update({'log.screen': False})
        Daemonizer(cpengine).subscribe()

    if args.drop_privilege:
        cherrypy.config.update({'engine.autoreload_on': False})
        DropPrivileges(cpengine, umask=args.umask or 022,
                       uid=args.uid or "www",
                       gid=args.gid or "www").subscribe()

    if args.pidfile:
        PIDFile(cpengine, args.pidfile).subscribe()

    fastcgi, scgi = getattr(args, 'fastcgi'), getattr(args, 'scgi')
    if fastcgi and scgi:
        cherrypy.log.error("You may only specify one of the fastcgi and "
                           "scgi options.", 'ENGINE')
        sys.exit(1)
    elif fastcgi or scgi:
        # Turn off autoreload when using *cgi.
        cherrypy.config.update({'engine.autoreload_on': False})
        # Turn off the default HTTP server (which is subscribed by default).
        cherrypy.server.unsubscribe()

        addr = cherrypy.server.bind_addr
        if fastcgi:
            f = servers.FlupFCGIServer(application=cherrypy.tree,
                                       bindAddress=addr)
        elif scgi:
            f = servers.FlupSCGIServer(application=cherrypy.tree,
                                       bindAddress=addr)
        s = servers.ServerAdapter(cpengine, httpserver=f, bind_addr=addr)
        s.subscribe()

    if hasattr(cpengine, 'signal_handler'):
        cpengine.signal_handler.subscribe()

    # for win32 only
    if hasattr(cpengine, "console_control_handler"):
        cpengine.console_control_handler.subscribe()

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
                    routes_config.update(section[path])
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

    # Add the blueberrypy config files into CP's autoreload monitor
    # Jinja2 templates are monitored by Jinja2 itself and will autoreload if
    # needed
    if config.config_file_paths:
        for path in config.config_file_paths:
            cpengine.autoreload.files.add(path)

    try:
        cpengine.start()
    except:
        sys.exit(1)
    else:
        cpengine.block()

def console(args, config_dir=None):
    banner = """
*****************************************************************************
* If the configuration file you specified contains a [sqlalchemy_engine*]   *
* section, a default SQLAlchemy engine and session should have been created *
* for you automatically already.                                            *
*****************************************************************************
"""
    cherrypy.config.update({"environment": args.environment})
    Console(BlueberryPyConfiguration(config_dir=config_dir,
                                     environment=args.environment)).interact(banner)

def create_parser(config_dir=None):
    parser = argparse.ArgumentParser(prog="create",
                                     description="Create a project skeleton.")
    parser.add_argument("-p", "--path", help="the path to create the project. "
                        "default is the current directory")
    parser.add_argument("-d", "--dry-run", action="store_true", default=False,
                         help="do not write skeleton. prints out the content instead")
    return parser

def bundle_parser(config_dir=None):

    description = textwrap.dedent("""Webassets bundle management.
    
    Before you can use this command to bundle up your Web assets, you should
    have created either a project skeleton using the 'create' command or
    provided a configuration directory using the global option -c --config_dir.
    """)

    config = BlueberryPyConfiguration(config_dir=config_dir)
    if not config.use_webassets:
        print(description)
        sys.exit(1)

    parser = argparse.ArgumentParser(prog="bundle", description=description)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-b", "--build", action="store_true", dest="build",
                        help="build the asset bundles")

    group.add_argument("-w", "--watch", action="store_true", dest="watch",
                        help="automatically rebuild the asset bundles upon changes in the static directory")

    group.add_argument("-c", "--clean", action="store_true", dest="clean",
                        help="delete the generated asset bundles")
    return parser

def serve_parser(config_dir=None):

    parser = argparse.ArgumentParser(prog="serve",
                                     description="spawn a new running cherrypy process")

    parser.add_argument("-b", "--bind", dest="binding",
                         default="127.0.0.1:8080",
                         help="the address and port to bind to. [default: %(default)s]")
    parser.add_argument("-e", "--environment", dest="environment",
                         default=None,
                         help="apply the given config environment")
    parser.add_argument("-f", action="store_true", dest="fastcgi",
                         help="start a fastcgi server instead of the default HTTP server")
    parser.add_argument("-s", action="store_true", dest="scgi",
                         help="start a scgi server instead of the default HTTP server")
    parser.add_argument("-d", "--daemonize", action="store_true",
                         default=False,
                         help="run the server as a daemon. [default: %(default)s]")
    parser.add_argument("-p", "--drop-privilege", action="store_true",
                         default=False,
                         help="drop privilege to separately specified umask, "
                         "uid and gid. [default: %(default)s]")
    parser.add_argument('-P', '--pidfile', dest='pidfile', default=None,
                         help="store the process id in the given file")
    parser.add_argument("-u", "--uid", default="www",
                         help="setuid to uid [default: %(default)s]")
    parser.add_argument("-g", "--gid", default="www",
                         help="setgid to gid [default: %(default)s]")
    parser.add_argument("-m", "--umask", default="022", type=int,
                         help="set umask [default: %(default)s]")
    return parser

def console_parser(config_dir=None):

    parser = argparse.ArgumentParser(prog="bundle",
                                     description="An REPL fully configured for experimentation.")
    parser.add_argument("-e", "--environment", dest="environment",
                         default=None,
                         help="apply the given config environment")

    return parser

def main():
    description = textwrap.dedent("""BlueberryPy lightweight pluggable Web application framework command line interface.
    
    Type 'blueberrypy -h' or 'blueberrypy --help' for general help.
    Type 'blueberrypy help <command>' for help on that specific command.
    
    commands:
    
    help                print this help or a command's if an argument is given
    create              create a project skeleton
    console             BlueberryPy REPL for experimentations
    bundle              bundles up web assets (type 'blueberrypy help bundle' for details)
    serve               spawn a new CherryPy server process
    """)

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=description)
    parser.add_argument("-v", "--version", action="store_true", default=False,
                        help="print version information and exit.")

    parser.add_argument("-C", "--config_dir", help="path to the config directory")

    parser.add_argument("command", nargs="?", default="help", help="the action to perform")

    args, extraargs = parser.parse_known_args()
    if args.version:
        print("BlueberryPy version %s" % blueberrypy.__version__)
        parser.exit(0)

    def get_command_parser_and_callback(command):
        if command == "create":
            return (create_parser(args.config_dir), create)
        elif command == "console":
            return (console_parser(args.config_dir), console)
        elif command == "bundle":
            return (bundle_parser(args.config_dir), bundle)
        elif command == "serve":
            return (serve_parser(args.config_dir), serve)

        parser.error("Unknown command %r" % args.command)

    if args.command == "help":
        if extraargs:
            subparser, _ = get_command_parser_and_callback(extraargs[0])
            subparser.print_help()
        else:
            parser.print_help()
    else:
        subparser, func = get_command_parser_and_callback(args.command)
        cmdargs = subparser.parse_args(extraargs)
        func(cmdargs, args.config_dir)
