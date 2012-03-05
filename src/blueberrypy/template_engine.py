from jinja2 import Environment as Jinja2Environment

from blueberrypy.exc import BlueberryPyNotConfiguredError

__all__ = ["jinja2_env", "configure_jinja2", "get_template"]


jinja2_env = None


def configure_jinja2(assets_env=None, **kwargs):
    global jinja2_env

    autoescape = kwargs.pop("autoescape", False)
    extensions = kwargs.pop("extensions", [])

    if assets_env:
        from webassets.ext.jinja2 import AssetsExtension
        extensions.append(AssetsExtension)

    if autoescape:
        autoescape = lambda filename: filename.rsplit('.', 1)[1] in ('html', 'xml', 'htm') if isinstance(filename, basestring) else False
        extensions.append("jinja2.ext.autoescape")

    jinja2_env = Jinja2Environment(autoescape=autoescape, extensions=extensions,
                                  **kwargs)

    if assets_env:
        jinja2_env.assets_environment = assets_env

    return jinja2_env

def get_template(*args, **kwargs):
    if not jinja2_env:
        raise BlueberryPyNotConfiguredError("Jinja2 not configured")
    return jinja2_env.get_template(*args, **kwargs)
