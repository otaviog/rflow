import os
import inspect
import copy
from collections import namedtuple


def hasmethod(instance, method_name):
    attr = getattr(instance, method_name, None)
    return callable(attr)


LineInfo = namedtuple("LineInfo", ["filepath", "line", "function"])


def get_caller_lineinfo(stack_level=1):
    stack = copy.copy(inspect.stack())
    stack_entry = stack[stack_level + 1]

    instance_filename = stack_entry[1]
    lineno = stack_entry[2]
    function = stack_entry[3]

    return LineInfo(instance_filename, lineno, function)


def get_caller_filepath(stack_level=1):
    return get_caller_lineinfo(stack_level + 1).filepath
