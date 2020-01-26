# -*- coding: utf-8 -*-
"""
Extension that creates a base structure for the project using django-admin.py.

Warning:
    *Deprecation Notice* - In the next major release the Django extension
    will be extracted into an independent package.
    After PyScaffold v4.0, you will need to explicitly install
    ``pyscaffoldext-django`` in your system/virtualenv in order to be
    able to use it.
"""
import os
import shutil
from os.path import join as join_path

import re
from pyscaffold.api import Extension, helpers
from pyscaffold.shell import ShellCommand
from pyscaffold.warnings import UpdateNotSupported

django_admin = ShellCommand("django-admin.py")


def replace_in_place(file_name, regex, new_string):
    if os.path.exists(file_name):
        with open(file_name, 'r') as infile:
            text = infile.read()    
        replaced = re.sub(regex, new_string, text)
        with open(file_name, 'w') as outfile:
            outfile.write(replaced)
        return True
    else:
        return False


class Django(Extension):
    """Generate Django project files"""

    mutually_exclusive = True

    def activate(self, actions):
        """Register hooks to generate project using django-admin.

        Args:
            actions (list): list of actions to perform

        Returns:
            list: updated list of actions
        """

        # `get_default_options` uses passed options to compute derived ones,
        # so it is better to prepend actions that modify options.
        actions = helpers.register(
            actions, enforce_django_options, before="get_default_options"
        )
        # `apply_update_rules` uses CWD information,
        # so it is better to prepend actions that modify it.
        actions = helpers.register(
            actions, create_django_proj, before="apply_update_rules"
        )

        actions = helpers.register(
            actions, fix_django_settings, before="apply_update_rules"
        )

        return actions


def enforce_django_options(struct, opts):
    """Make sure options reflect the Django usage.

    Args:
        struct (dict): project representation as (possibly) nested
            :obj:`dict`.
        opts (dict): given options, see :obj:`create_project` for
            an extensive list.

    Returns:
        struct, opts: updated project representation and options
    """
    opts["package"] = opts["project"]  # required by Django
    opts["force"] = True
    opts.setdefault("requirements", []).append("django")

    return struct, opts

def fix_django_settings(struct, opts):
    
    new_string = "src.{0}".format(opts['project'])
    regex = "{0}".format(opts['project'])
    src_dir = join_path(opts["project"], "src")
    config_dir = join_path(src_dir, opts["project"])

    replace_in_place(join_path(config_dir, 'settings.py'), regex, new_string)
    replace_in_place(join_path(config_dir, 'wsgi.py'), regex, new_string)
    replace_in_place(join_path(opts["project"], "manage.py"), regex, new_string)

    return struct, opts

def create_django_proj(struct, opts):
    """Creates a standard Django project with django-admin.py

    Args:
        struct (dict): project representation as (possibly) nested
            :obj:`dict`.
        opts (dict): given options, see :obj:`create_project` for
            an extensive list.

    Returns:
        struct, opts: updated project representation and options

    Raises:
        :obj:`RuntimeError`: raised if django-admin.py is not installed
    """
    if opts.get("update"):
        helpers.logger.warning(UpdateNotSupported(extension="django"))
        return struct, opts

    try:
        django_admin("--version")
    except Exception as e:
        raise DjangoAdminNotInstalled from e

    pretend = opts.get("pretend")
    django_admin("startproject", opts["project"], log=True, pretend=pretend)
    if not pretend:
        src_dir = join_path(opts["project"], "src")
        
        os.mkdir(src_dir)
        shutil.move(
            join_path(opts["project"], opts["project"]),
            join_path(src_dir, opts["package"]),
        )

    return struct, opts


class DjangoAdminNotInstalled(RuntimeError):
    """This extension depends on the ``django-admin.py`` cli script."""

    DEFAULT_MESSAGE = "django-admin.py is not installed, " "run: pip install django"

    def __init__(self, message=DEFAULT_MESSAGE, *args, **kwargs):
        super(DjangoAdminNotInstalled, self).__init__(message, *args, **kwargs)
