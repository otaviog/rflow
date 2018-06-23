"""Utilities functions of the module.
"""

import sys
import os
import inspect
import copy
from contextlib import contextmanager


@contextmanager
def work_directory(path):
    """Change the current directory while in the scope of this context
    manager.

    Args:
        path (str): Target directory path.
    """
    cur_dir = os.path.abspath(os.curdir)
    os.chdir(path)

    try:
        yield
    finally:
        os.chdir(cur_dir)


def here():
    """Returns the file directory of the calling .py file.

    Returns:
        str: The directory of the calling .py file.
    """
    return os.path.abspath(os.path.dirname(
        inspect.getfile(sys._getframe(1))))


def get_caller_filepath(stack_level=1):
    stack = copy.copy(inspect.stack())
    instance_filename = os.path.abspath(inspect.getfile(
        stack[stack_level + 1][0]))
    return instance_filename


def is_eq_override(obj):
    return obj.__class__.__eq__ != object.__class__.__eq__
