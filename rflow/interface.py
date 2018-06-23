# -*- coding: utf-8 -*-

import inspect
from ._argument import ArgNamespace
from .node import Node
from ._reflection import hasmethod

# pylint: disable=no-member


class Interface(Node):
    def __init__(self, resource=None):
        evaluate_argspec = inspect.getfullargspec(self.evaluate)
        if 'self' in evaluate_argspec.args:
            evaluate_argspec.args.remove('self')

        defaults_map = {}
        if evaluate_argspec.defaults is not None:
            defaults_map = dict(zip(
                evaluate_argspec.args[-len(evaluate_argspec.defaults):],
                inspect.getfullargspec(self.evaluate).defaults))

        args = ArgNamespace(evaluate_argspec.args, defaults_map)

        load_func = None
        load_arg_list = []
        if hasmethod(self, 'load'):
            load_argspec = inspect.getfullargspec(self.load)
            load_arg_list = load_argspec.args
            if 'self' in load_arg_list:
                load_arg_list.remove('self')
            if not set(load_arg_list).issubset(evaluate_argspec.args):
                raise RuntimeError(
                    'Load arguments must be a subset of evaluate')
            load_func = self.load
        super(Interface, self).__init__(None,
                                        self.__class__.__name__,
                                        self.evaluate, args, load_func,
                                        load_arg_list)
        if resource is not None:
            self.resource = resource


class VarNode(Interface):
    def __init__(self, obj):
        super(VarNode, self).__init__()
        self.show = False
        self.obj = obj

    def evaluate(self):
        return self.obj

    def get_view_name(self):
        return "{}({})".format(self.obj.__class__.__name__, str(self.obj))
