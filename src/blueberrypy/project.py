from __future__ import print_function

import difflib
import os.path
import re
import shutil

from cherrypy.test.webtest import getchar
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


class ProjectCreator(object):

    def __init__(self, blueberrypy_config, dry_run=False,
                 project_template_filter=project_template_filter):

        self.dry_run = dry_run
        self.filename_var_re = re.compile(r"\+(.+)\+")
        self.blueberrypy_config = blueberrypy_config.copy()
        self.dest = blueberrypy_config["path"]
        self.project_template_dir = os.path.join(os.path.dirname(__file__), "project_template")
        self.overwrite = False

        self.process_dir(self.project_template_dir)

    def replace_path(self, path):
        matcher = self.filename_var_re.search(path)
        while matcher:
            var = matcher.group(1)
            val = self.blueberrypy_config[var]
            start, end = matcher.span(1)
            path = path[:start - 1] + val + path[end + 1:]
            matcher = self.filename_var_re.search(path)
        return path

    def process_dir(self, root, directory=''):

        currentpath = os.path.join(root, directory)

        for listing in os.listdir(currentpath):

            relpath = os.path.join(directory, listing)
            src_fullpath = os.path.join(currentpath, listing)
            replaced_relpath = self.replace_path(relpath)

            proceed = project_template_filter(self.blueberrypy_config, relpath)

            # hack to preprocess jinja2 html templates
            if isinstance(proceed, Jinja2Environment):
                jinja2_env = proceed
            else:
                jinja2_env = Jinja2Environment()

            if proceed:

                if os.path.isdir(src_fullpath):
                    dest_fullpath = os.path.join(self.dest, replaced_relpath)

                    if not self.dry_run:
                        if not os.path.exists(dest_fullpath):
                            os.makedirs(dest_fullpath)
                    else:
                        print("created directory " + dest_fullpath)

                    self.process_dir(root, relpath)
                else:
                    dest_fullpath = os.path.join(self.dest, replaced_relpath)

                    head, tail = os.path.split(dest_fullpath)

                    if tail.endswith("_tmpl"):
                        dest_fullpath = os.path.join(head, tail[:-5])

                        with open(src_fullpath) as infile:
                            tmpl = jinja2_env.from_string(infile.read())

                        if not self.dry_run:
                            if self.overwrite or not os.path.exists(dest_fullpath):
                                with open(dest_fullpath, 'w') as outfile:
                                    outfile.write(tmpl.render(self.blueberrypy_config))
                            elif os.path.exists(dest_fullpath):
                                while True:
                                    print("%s already exists, do you wish to overwrite it?" % dest_fullpath,
                                    "[Y]es [N]o [A]ll [C]ompare the files >> ", sep='\n', end='')
                                    i = getchar().upper()

                                    if not isinstance(i, type("")):
                                        i = i.decode('ascii')

                                    if i not in "YNAC":
                                        continue

                                    print(i.upper())

                                    if i == 'Y' or i == 'A':
                                        with open(dest_fullpath, 'w') as outfile:
                                            outfile.write(tmpl.render(self.blueberrypy_config))

                                        if i == 'A':
                                            self.overwrite = True

                                        break

                                    elif i == 'N':
                                        print("%s has been skipped." % dest_fullpath)
                                        break

                                    elif i == 'C':
                                        with open(dest_fullpath) as infile:
                                            old = infile.read()
                                        new = tmpl.render(self.blueberrypy_config)
                                        print("\n".join(difflib.unified_diff(old.splitlines(), new.splitlines(), dest_fullpath + ".old", dest_fullpath + ".new")))
                                        continue
                        else:
                            print("created file " + dest_fullpath)
                            print(tmpl.render(self.blueberrypy_config))
                    else:
                        if not self.dry_run:
                            if self.overwrite or not os.path.exists(dest_fullpath):
                                shutil.copy(src_fullpath, dest_fullpath)
                            elif os.path.exists(dest_fullpath):
                                while True:
                                    print("\n%s already exists, do you wish to overwrite it?" % dest_fullpath,
                                    "[Y]es [N]o [A]ll [C]ompare the files >> ", sep='\n', end='')
                                    i = getchar().upper()

                                    if not isinstance(i, type("")):
                                        i = i.decode('ascii')

                                    if i not in "YNAC":
                                        continue

                                    print(i.upper())

                                    if i == 'Y' or i == 'A':
                                        shutil.copy(src_fullpath, dest_fullpath)

                                        if i == 'A':
                                            self.overwrite = True

                                        break

                                    elif i == 'N':
                                        print("%s has been skipped." % dest_fullpath)
                                        break

                                    elif i == 'C':
                                        with open(dest_fullpath) as infile:
                                            old = infile.read()
                                        with open(src_fullpath) as infile:
                                            new = infile.read()
                                        print("\n".join(difflib.unified_diff(old.splitlines(), new.splitlines(), dest_fullpath + ".old", dest_fullpath + ".new")))
                                        continue
                        else:
                            print("copied file " + dest_fullpath)

create_project = ProjectCreator
