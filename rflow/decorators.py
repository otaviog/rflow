"""Decorators
"""

import os
import sys

from . import core, _util as util
from ._ui import ui

# pylint: disable=invalid-name


class graph:
    """Graph decorator.
    """

    def __init__(self, *args):
        n_args = len(args)
        self.name = None
        if n_args == 0:
            self.directory = os.path.abspath(os.path.curdir)
        elif n_args == 1:
            self.directory = os.path.abspath(args[0])
        else:
            self.name = args[0]
            self.directory = args[1]

    def __call__(self, func):
        def _wrapped():
            if self.name is None:
                name = func.__name__
            else:
                name = self.name
            gph = core.get_graph(name, self.directory, False)
            with util.work_directory(self.directory):
                try:
                    return func(gph)
                except Exception as ex:
                    ui.print_traceback(sys.exc_info(), ex)
                    sys.exit(1)
        return _wrapped
