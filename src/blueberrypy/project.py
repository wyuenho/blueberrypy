import os.path
import re
import shutil

from jinja2 import Environment as Jinja2Environment


def project_template_filter(blueberrypy_config, path):

    if path.endswith(".html_tmpl"):
        return Jinja2Environment(block_start_string="<%",
                                 block_end_string="%>",
                                 variable_start_string="<<",
                                 variable_end_string=">>",
                                 comment_start_string="<#",
                                 comment_end_string="#>")

    if path.endswith("_tmpl"):
        path = path[:-5]

    if path.endswith("rest_controller.py"):
        return blueberrypy_config.get("use_rest_controller")
    if path.endswith("controller.py") or path.find("static") != -1:
        return blueberrypy_config.get("use_controller")
    if path.find("/templates") != -1:
        return blueberrypy_config.get("use_controller") and \
            blueberrypy_config.get("use_jinja2")
    if path.endswith("bundles.yml"):
        return blueberrypy_config.get("use_webassets")
    if path.endswith(".hidden"):
        return False
    if path.endswith("model.py") or path.endswith("api.py"):
        return blueberrypy_config.get("use_sqlalchemy")

    return True

def create_project(blueberrypy_config, dry_run=False,
                   project_template_filter=project_template_filter):

    filename_var_re = re.compile(r"\+(.+)\+")

    blueberrypy_config = blueberrypy_config.copy()
    dest = blueberrypy_config["path"]

    project_template_dir = os.path.join(os.path.dirname(__file__), "project_template")

    def replace_path(path):
        matcher = filename_var_re.search(path)
        while matcher:
            var = matcher.group(1)
            val = blueberrypy_config[var]
            start, end = matcher.span(1)
            path = path[:start - 1] + val + path[end + 1:]
            matcher = filename_var_re.search(path)
        return path

    def process_dir(root, directory=''):

        currentpath = os.path.join(root, directory)

        for listing in os.listdir(currentpath):

            relpath = os.path.join(directory, listing)
            fullpath = os.path.join(currentpath, listing)
            replaced_relpath = replace_path(relpath)

            proceed = project_template_filter(blueberrypy_config, relpath)

            # hack to preprocess jinja2 html templates
            if isinstance(proceed, Jinja2Environment):
                jinja2_env = proceed
            else:
                jinja2_env = Jinja2Environment()

            if proceed:

                if os.path.isdir(fullpath):
                    dest_fullpath = os.path.join(dest, replaced_relpath)

                    if not dry_run:
                        if not os.path.exists(dest_fullpath):
                            os.makedirs(dest_fullpath)
                    else:
                        print "created directory " + dest_fullpath

                    process_dir(root, relpath)
                else:
                    dest_fullpath = os.path.join(dest, replaced_relpath)

                    head, tail = os.path.split(dest_fullpath)

                    if tail.endswith("_tmpl"):
                        dest_fullpath = os.path.join(head, tail[:-5])

                        with open(fullpath) as infile:
                            tmpl = jinja2_env.from_string(infile.read())

                        if not dry_run:
                            with open(dest_fullpath, 'w') as outfile:
                                outfile.write(tmpl.render(blueberrypy_config))
                        else:
                            print "created file " + dest_fullpath
                            print tmpl.render(blueberrypy_config)
                    else:
                        if not dry_run:
                            shutil.copy(fullpath, dest_fullpath)
                        else:
                            print "copied file " + dest_fullpath

    process_dir(project_template_dir)
