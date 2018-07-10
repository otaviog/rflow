"""Node and Graph execution classes.
"""

import sys

from . common import WorkflowError, Uninit, BaseNode
from . _argument import get_sig_difference
from . resource import Resource
from ._ui import ui
from . import _util as util


class BaseNodeLink(BaseNode):
    """Base class to wrap node's calls.
    """
    # pylint: disable=abstract-method

    def __init__(self, node):
        super(BaseNodeLink, self).__init__()
        self._node = node
        self.graph = node.graph

    def get_resource(self):
        return self._node.get_resource()

    def is_dirty(self):
        return self._node.is_dirty()

    def update(self):
        return self._node.update()

    @property
    def args(self):
        """
        The node's arguments.
        """
        return self._node.args

    @property
    def name(self):
        """The node's name.
        """

        return self._node.name

    def get_edges(self):
        return []


class ReturnSelNodeLink(BaseNodeLink):
    """Utility node type for selecting value from call methods that
    return tuples.
    """

    def __init__(self, node, idx):
        """
        Args:

            node (:obj:`rflow.common.BaseNode`): The
             wrapped node.

            idx (int): Which return value this instance's call method
             should return.

        """

        super(ReturnSelNodeLink, self).__init__(node)
        self.return_index = idx

    def call(self):
        value = self._node.call()
        if isinstance(value, (tuple, list)):
            return value[self.return_index]
        return value


class ResourceNodeLink(BaseNodeLink):
    """Wrappers node's resource attribute as node.
    """

    def __init__(self, node, resource):
        super(ResourceNodeLink, self).__init__(node)
        self._resource = resource

    def call(self):
        self._node.call()
        return self._resource


class DependencyLink(object):
    """Placeholder class to hold edged between nodes and dependency nodes,
    i.e. nodes that doesn't appear on evaluation arguments, but add
    with `require` call.

    Attributes:

        name (str): The link name, normally this is the dependency
         node name.

    """

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return '@DependencyLink {}'.format(self.name)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name.__eq__(other)

        return self.name.__eq__(other.name)


class Node(BaseNode):
    def __init__(self, graph, name, evaluate_func,
                 args_namespace, load_func=None, load_arg_list=None):
        super(Node, self).__init__()

        self.name = name
        self.graph = graph
        self.value = Uninit

        self._resource = None
        self._dirty = True

        self.evaluate_func = evaluate_func
        self.load_func = load_func
        self.args = args_namespace
        self.load_arg_list = [] if load_arg_list is None else load_arg_list
        self.dependencies = []

        self.erase_resource_on_fail = False

        # Debugging attributes
        self._curr_signature = None
        self._prev_signature = None
        self._signature_diff = None

    def __getitem__(self, idx):
        return ReturnSelNodeLink(self, idx)

    def fail(self, message):
        ui.error_ocurred(self, message)
        self._asure_erase_res_on_fail()
        sys.exit(0)

    def non_collateral(self):
        # pylint: disable=no-self-use
        return []

    def is_dirty(self):
        return self._dirty

    def get_resource(self):
        return self._resource

    def __enter__(self):
        return self.args

    def __exit__(self, *args):
        pass

    @property
    def resource(self):
        # This might be a problem. If the resource is a relative path
        # and it can be used in different directory.
        return ResourceNodeLink(self, self._resource)

    @resource.setter
    def resource(self, value):
        if isinstance(value, ResourceNodeLink):
            self.args.resource = value
            self._resource = value._resource
        elif isinstance(value, Resource) or value is None:
            self.args.resource = value
            self._resource = value
        else:
            raise WorkflowError('Invalid non resource assignment')

    def require(self, node):
        """Adds an another node as dependency of this one.

        Args:

            node (:obj:`rflow.common.BaseNode`): The node
             that'll be execute before than this one.
        """

        self.dependencies.append(node)

    def get_edges(self, edge_set=None):
        arg_edges = [(argname, self.args.__dict__[argname])
                     for argname in self.args._arg_names
                     if edge_set is None or argname in edge_set]
        dep_edges = []
        if edge_set is None:
            dep_edges = [(DependencyLink(dep.name), dep)
                         for dep in self.dependencies]

        return arg_edges + dep_edges

    def update(self):
        self._dirty = False

        signature = {}
        if self._resource is not None:
            if not self._resource.exists():
                self._dirty = True
                return None

        non_collateral = set(self.non_collateral())
        for edgename, edge in self.get_edges():
            if edgename in non_collateral:
                continue

            if not isinstance(edge, BaseNode):
                signature[edgename] = edge
                continue

            edge.update()

            if edge.is_dirty():
                self._dirty = True
                return None

            if edge.get_resource() is not None:
                with util.work_directory(self.graph.work_directory):
                    signature[edgename] = edge.get_resource().get_hash()

        self._curr_signature = signature
        self._prev_signature = self._get_previous_signature()
        self._signature_diff = get_sig_difference(
            self._prev_signature, self._curr_signature)
        self._dirty = len(self._signature_diff) > 0

        return None

    def call(self, redo=False):
        # pylint: disable=protected-access
        self._check_runnable()
        is_loadable = self._is_loadable()
        self.update()

        is_dirty = self.is_dirty() or redo

        if not is_dirty and self.value is not Uninit:
            return self.value

        if not is_dirty and is_loadable:
            self._check_variables(self.load_arg_list)
            ui.executing_load(self)
            call_values = self._bind_call(self.load_arg_list)
            with util.work_directory(self.graph.work_directory):
                try:
                    self.value = self.load_func(*call_values)
                except Exception as exp:
                    ui.print_traceback(sys.exc_info(), exp)
            ui.done_load(self)
            return self.value

        ui.executing_evaluate(self)
        self._check_variables(self.args._arg_names)
        call_arg_values = self._bind_call(self.args._arg_names)

        for dep in self.dependencies:
            if dep.is_dirty():
                dep.call()

        with util.work_directory(self.graph.work_directory):
            try:
                self.save_measurement({})
                if self._resource is not None and not self._resource.rewritable:
                    self._resource.erase()
                ui.executing_run(self)
                self.value = self.evaluate_func(*call_arg_values)
            except Exception as exp:
                ui.print_traceback(sys.exc_info(), exp)
                self._asure_erase_res_on_fail()

        ui.done_evaluate(self)
        self._update_signature(call_arg_values)

        return self.value

    def touch(self):
        # pylint: disable=protected-access
        self.update()

        ui.executing_touch(self)
        call_arg_values = self._bind_call(self.args._arg_names)

        self._update_signature(call_arg_values)
        ui.done_touch(self)

    def _bind_call(self, bind_args):
        call_values = []

        for _, edge in self.get_edges(set(bind_args)):
            if not isinstance(edge, BaseNode):
                call_values.append(edge)
                continue

            call_values.append(edge.call())

        return call_values

    def _update_signature(self, call_arg_values):
        new_signature = {}
        non_collateral = self.non_collateral()
        for i, (edgename, edge) in enumerate(self.get_edges()):
            if edgename in non_collateral:
                continue
            if not isinstance(edge, BaseNode):
                new_signature[edgename] = call_arg_values[i]
                continue

            if edge.get_resource() is not None:
                with util.work_directory(self.graph.work_directory):
                    new_signature[edgename] = edge.get_resource().get_hash()

        self.graph.args_context.update_argsignature(
            self.graph.name, self.name,
            new_signature)

    def _is_loadable(self):
        # pylint: disable=no-member
        if self.load_func is not None:
            if self._resource is None:
                raise WorkflowError(
                    '{} has load method but without resource'.format(
                        self.name), self.instanciation_lineinfo)
            with util.work_directory(self.graph.work_directory):
                return self._resource.exists()
        return False

    def _check_variables(self, args):
        for edgename, edge in self.get_edges(set(args)):
            if edge == Uninit:
                raise WorkflowError(
                    '{}: Variable {} was never set'.format(self.name, edgename))

    def _check_runnable(self):
        if self.graph is None:
            raise WorkflowError('Node {} not assigned to a graph'.format(
                self.name))

    def _get_previous_signature(self):
        return self.graph.args_context.get_argsignature(
            self.graph.name, self.name)

    def _asure_erase_res_on_fail(self):
        if self.erase_resource_on_fail:
            if self._resource is not None:
                self._resource.erase()

    def save_measurement(self, meas_dict):
        self.graph.args_context.set_measurement(
            self.graph.name, self.name, meas_dict)

    def get_measurement(self):
        return self.graph.args_context.get_measurement(
            self.graph.name, self.name)

    def clear(self):
        resource = self.get_resource()
        if resource is not None:
            print("Removing resource {}".format(str(resource)))
            resource.erase()
        self.graph.args_context.clean_node(
            self.graph.name, self.name)

    def clear_cache(self):
        self.value = Uninit
