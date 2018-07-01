"""Reflection utilities.
"""

import inspect
import copy
from collections import namedtuple
from pathlib import Path


def hasmethod(instance, method_name):
    """Wrapper for testing if a instance has a given method.

    Args:

        instance (object): A class instance.

        method_name (str): The method name to test if exists.

    Returns:
        bool: The method's existance.

    """
    attr = getattr(instance, method_name, None)
    return callable(attr)


LineInfo = namedtuple("LineInfo", ["filepath", "line", "function"])

HERE = Path(__file__).parent


def is_frame_on_rflow(frame_summ):
    """Returns if a :obj:`traceback` is inside the rflow
    module.

    >>> import traceback
    >>> is_frame_on_rflow(traceback.FrameSummary(
    ...   "/home/foo/workflow.py", 10, "foo"))
    False
    >>> import rflow.node
    >>> is_frame_on_rflow(traceback.FrameSummary(
    ...   rflow.node.__file__,10, "foo"))
    True
    """

    frame_path = Path(frame_summ.filename)

    # frame_path = Path(frame_summ.tb_frame.f_code.co_filename)
    try:
        frame_path.relative_to(HERE)
        return True
    except ValueError:
        return False


def get_caller_lineinfo(stack_level=1):
    stack = copy.copy(inspect.stack())
    stack_entry = stack[stack_level + 1]

    instance_filename = stack_entry[1]
    lineno = stack_entry[2]
    function = stack_entry[3]

    return LineInfo(instance_filename, lineno, function)


def get_caller_filepath(stack_level=1):
    return get_caller_lineinfo(stack_level + 1).filepath
