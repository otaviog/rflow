"""Argument handling. The instances are created by other modules of
shaperetrieval.workflow.
"""

import os
import pickle
from enum import Enum
from collections import namedtuple
from inspect import isfunction

import lmdb

from .common import Uninit, WorkflowError, BaseNode
from .resource import Resource
from ._util import is_eq_override

_LAMBDA_NAME = (lambda x: x).__name__


def _can_object_be_graph_argument(obj):
    if isinstance(obj, (BaseNode, Resource, int, bool, float, str,
                        Enum, type)):
        return True
    if isinstance(obj, (list, set)):
        return all(map(_can_object_be_graph_argument, obj))
    if is_eq_override(obj):
        return True
    if isinstance(obj, dict):
        return all([_can_object_be_graph_argument(value)
                    for value in obj.itervalues()])
    if isfunction(obj):
        return obj.__name__ != _LAMBDA_NAME
    return False


class ArgNamespace:
    """Dynamically holds the evaluation and load function arguments of its
    nodes. A resource attribute is always created with None.
    """

    def __init__(self, arg_name_list, value_map):
        """Creates a object with attribute being the ones in arg_list
        parameter. The arguments are initialized to
        :class:`shaperetrieval.workflow.core.Uninit`, except if has
        entry in `value_map`.

        Args:

            arg_name_list (list of str): List of attribute names to
             countain in this instances.

            value_map (dict of str: object): Map of values to the
             given argument names.
        """

        self.__dict__['_arg_names'] = arg_name_list
        self.__dict__['resource'] = None
        for argname in arg_name_list:
            if argname in value_map:
                self.__dict__[argname] = value_map[argname]
            else:
                self.__dict__[argname] = Uninit

    def __setattr__(self, name, value):
        if name not in self.__dict__:
            raise WorkflowError(
                'Variable `{}` not contained on this node'.format(name))

        if not _can_object_be_graph_argument(value):
            raise WorkflowError(
                "Assigning a non equalable value that is not derived from BaseNode or Resource")

        self.__dict__[name] = value


ArgDiff = namedtuple("ArgDiff", ["bef", "now"])


def get_sig_difference(other_args, curr_args):
    """Computes the difference between two argument signatures.

    Args:

        other_args (dict of str: object): Previous arguments signature.
        curr_args (dict of str: curr_args): Current arguments signature.

    Returns: (dict of str:
     :obj:`shaperetrieval.workflow.argument.ArgDiff`): A dictionaty
     where its keys are the argument names and each value is a tuple
     of two values: previous and current values.

    """

    diff_dict = {}

    oargs = other_args
    sargs = curr_args

    self_keys = set(sargs.keys())
    other_keys = set(oargs.keys())

    commnon_keys = self_keys.intersection(other_keys)
    keys_only_in_self = self_keys.difference(commnon_keys)
    keys_only_in_others = other_keys.difference(commnon_keys)

    for key in keys_only_in_self:
        diff_dict[key] = ArgDiff(None, sargs[key])

    for key in keys_only_in_others:
        diff_dict[key] = ArgDiff(oargs[key], None)

    for key in commnon_keys:
        self_value = sargs[key]
        other_value = oargs[key]

        if not isinstance(self_value, type(other_value)):
            diff_dict[key] = ArgDiff(type(self_value), type(other_value))

        if not self_value == other_value:
            diff_dict[key] = ArgDiff(other_value, self_value)

    return diff_dict


class ArgumentSignatureDB:
    """
    Store and retrive node's argument signatures.
    """

    __g_env = {}

    def __init__(self):
        self.dbenv = None

    def open(self, database_path):
        """
        Opens the database with the given path.

        Args:

            database_path (str): Path to lmdb database.
        """
        database_path = os.path.abspath(database_path)

        if database_path not in ArgumentSignatureDB.__g_env:
            dbenv = lmdb.open(database_path)
            ArgumentSignatureDB.__g_env[database_path] = dbenv
            self.dbenv = dbenv
        else:
            self.dbenv = ArgumentSignatureDB.__g_env[database_path]

    def get_argsignature(self, graph_id, node_id):
        """Retrieves a node's arguments signature.

        Args:

            graph_id (str): The source graph's name.

            node_id (str): The source node's name.

        Returns (dict str: :object:`object`): The node's arguments
         signature. An empty dictionaty if no signature was stored.

        """

        if self.dbenv is None:
            raise WorkflowError('Database is not opened')
        sig_id = self._get_db_id(graph_id, node_id)
        with self.dbenv.begin(write=False) as txn:
            value = txn.get(sig_id.encode())
            if value is not None:
                try:
                    return pickle.loads(value)
                except AttributeError:
                    return {}  # ignore attribute errors and return as
                    # empty dict.
        return {}

    def update_argsignature(self, graph_id, node_id, arg_sig):
        """Write a node's arguments signature to the database.
        Overwrites the previous value.

        Args:
            graph_id (str): The source graph's name.  node_id (str):
            The source node's name.

            arg_sig (dict of str: object): The node's aguments
            signature.
        """

        if self.dbenv is None:
            raise WorkflowError('Database is not opened')
        sig_id = self._get_db_id(graph_id, node_id)
        with self.dbenv.begin(write=True) as txn:
            txn.put(sig_id.encode(), pickle.dumps(
                arg_sig, pickle.HIGHEST_PROTOCOL))

    def clean_node(self, graph_id, node_id):
        """Deletes the node's previous signature.

        Args:

            graph_id (str): The source graph's name.

            node_id (str): The source node's name.

        """

        sig_id = self._get_db_id(graph_id, node_id)
        with self.dbenv.begin(write=True) as txn:
            txn.delete(sig_id.encode())

    def get_measurement(self, graph_id, node_id):
        """Retrieve from the workflow database a node's measurement
        dictionary.

        Args:

            graph_id (str): The source graph's name.

            node_id (str): The source node's name.

        Returns:

            dict: The measurement dict. Can be any user information.

        """
        if self.dbenv is None:
            raise WorkflowError('Database is not opened')
        meas_id = self._get_db_meas_id(graph_id, node_id)
        with self.dbenv.begin(write=False) as txn:
            value = txn.get(meas_id.encode())
            if value is not None:
                return pickle.loads(value)
        return {}

    def set_measurement(self, graph_id, node_id, meas_dict):
        """Save to the workflow database a node's measurement dictionary.

        Args:

            graph_id (str): The source graph's name.

            node_id (str): The source node's name.

            meas_dict (dict): The user's measurement dictionary.
        """

        if self.dbenv is None:
            raise WorkflowError('Database is not opened')

        meas_id = self._get_db_meas_id(graph_id, node_id)
        with self.dbenv.begin(write=True) as txn:
            txn.put(meas_id.encode(), pickle.dumps(
                meas_dict, pickle.HIGHEST_PROTOCOL))

    @staticmethod
    def _get_db_id(graph_id, node_id):
        return graph_id + ':' + node_id

    @staticmethod
    def _get_db_meas_id(graph_id, node_id):
        return ArgumentSignatureDB._get_db_id(graph_id, node_id) + ':' + "__meas__"
