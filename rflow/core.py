"""Base DAG workflows management.

"""

import os
from contextlib import contextmanager

from . _argument import ArgumentSignatureDB
from . common import WorkflowError, DOT_DATABASE_FILENAME
from . import _util as util
from ._reflection import get_caller_lineinfo


class BaseNode:
    """Base methods for nodes. Should be used to create new node types.

    Attributes:

        show (bool): Whatever the node is show on the command line
         help.

    """

    def __init__(self):
        self.show = True

    def call(self):
        """
        Executes the node main logic and returns its value.
        """

        raise NotImplementedError()

    def update(self):
        """
        Should update the dirty state of function :func:`is_dirty`.
        """
        pass

    def is_dirty(self):
        """Returns if the node should be call or it's already update.
        """

        raise NotImplementedError()

    def get_resource(self):
        """Returns the attched node's resource"""
        raise NotImplementedError()

    def get_view_name(self):
        """Returns how the node should be labeled to the user. Default is returning its name."""
        return self.name


class Subgraph:
    """Graph wrapper for prefixing node with a given input string. See :func:`Graph.prefix`

    Attributes:

        graph (Graph):

        prefix (str): The prefix which should be add to the new node
         names.

    """

    def __init__(self, graph, prefix):
        self.graph = graph
        self.prefix = prefix

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __setattr__(self, name, value):
        if isinstance(value, BaseNode):
            self.__dict__[name] = value
            if self.prefix is None:
                self.graph.__setattr__(name, value)
                return
            self.graph.__setattr__('{}{}'.format(self.prefix, name), value)
        else:
            super(Subgraph, self).__setattr__(name, value)


class Graph:
    """A workflow DAG. Nodes are added by setting as new instance
    attributes. Use the functions:

    * :func:`get_graph` to get an existing graph.

    * :func:`shrkit.workflow.command.open_graph` to open an existing one from
      a script file. The graphs are created by functions decorated
      with :class:`shrkit.workflow.decorators.graph`.

    * :func:`begin_graph` to create a graph
      interactively

    Example:

    >>> import shrkit.workflow
    >>> class HelloNode(shrkit.workflow.Interface):
    ...     def evaluate(self, message):
    ...         print(message)
    >>> with begin_graph("my_graph", '.') as g:
    ...     g.hello = HelloNode()
    ...     g.hello.args.message = "Hello"
    ...     g.hello.call()
    Hello
    >>> g.name
    'my_graph'
    >>> g.node_list[0].name
    'hello'

    Attributes:

        work_directory (str): Working directory of the graph. All nodes
         `evaluate` and `load` calls are always executed with this
         directory set as current.

        name (str): The graph's name. A graph is uniquely identified
         by its directory and name.

        node_list (List[BaseNode]): All graph nodes.

    """

    def __init__(self, work_directory, name=None):
        self.work_directory = str(work_directory)
        if name is not None:
            self.name = name
        else:
            self.name = os.path.basename(self.work_directory)

        self.node_list = []
        self._node_set = set()

        self.args_context = ArgumentSignatureDB()
        self.args_context.open(os.path.join(
            self.work_directory, DOT_DATABASE_FILENAME))

        self._signature_diff = None
        self._previous_signature = None
        self._saved_cur_dir = None

    def _add_node(self, name, node):
        if node not in self._node_set:
            self.node_list.append(node)
            self._node_set.add(node)
            if node.graph is None:
                node.graph = self
                node.instanciation_lineinfo = get_caller_lineinfo(2)
                node.name = name
                if name.startswith('_'):
                    node.show = False

    def get_node_names(self, filter_show=False):
        """ Get all node's name on the graph.

        Args:

            filter_show (bool, optional): Return only the nodes that are marked
             with show. Default is `False`.

        Returns:
            List[str]: The node names in this graph.
        """

        return [node.name for node in self.node_list
                if (not filter_show) or node.show]

    def get_node(self, node_name):
        """Finds a node by name.

        Args:

            node_name (str): The node's name.

        Returns:
            :obj:`BaseNode`: The found node or `None`.
        """

        return next((node for node in self.node_list
                     if node.name == node_name), None)

    def prefix(self, prefix_name):
        """Creates a graph wrapper, in which new every node is prefixed with a
        string.

        This is useful to compose a DAG with different tests. Like (pseudo-code)::

            with begin_graph("my_graph") as g:
                g.features = FeatureExtractor()

                def create_ranking(s, dist_func, g=g):
                    s.ranker = NearestNeihgborsNode()
                    s.ranker.args.features = g.features
                    s.ranker.args.dist_func = dist_func

                    s.mAP_eval = MAPEvalNode()
                    s.mAP_eval.args.ranker = s.ranker

                create_ranking(g.prefix("cos_"),
                    shrkit.ranking.nearestneighbors.cosine)
                create_ranking(g.prefix("euc_"),
                    shrkit.ranking.nearestneighbors.euclidean)

        The code above adds the nodes `cos_ranker`, `cos_mAP_eval`,
        `euc_ranker` and `euc_mAP_eval` to the graph `g`. So users can
        evaluate those ranking possibilities.

        """
        return Subgraph(self, prefix_name)

    def clear_cache(self):
        """Clears previous in-memory saved values from node calls.
        """
        for node in self.node_list:
            if hasattr(node, 'clear_cache'):
                node.clear_cache()

    def __getitem__(self, node_name):
        node_names = self.get_node_names()
        if node_name not in node_names:
            raise KeyError(node_name)
        return self.get_node(node_name)

    def __setitem__(self, name, value):
        if isinstance(value, BaseNode):
            self.__setattr__(name, value)
        else:
            raise WorkflowError('Only nodes can be set as items')

    def __setattr__(self, name, value):
        if isinstance(value, BaseNode):
            if name in self.__dict__:
                raise WorkflowError("Overwrting node {} on graph {}".format(
                    name, self.name))
            self.__dict__[name] = value
            self._add_node(name, value)
        else:
            super(Graph, self).__setattr__(name, value)


class UID:
    """Unique identification for graph and nodes.

    Attributes:

        directory (str): The graph's directory.

        graph_name (str): The graph's name.

        node_name (str, optional): The node's name. It's setted to
         `None` when it's a graph identification. Only node
         identification have this field.

    """

    def __init__(self, directory, graph_name, node_name=None):
        self.directory = directory
        self.graph_name = graph_name
        self.node_name = node_name
        self.str_rep = directory + ':' + graph_name

        if node_name is not None:
            self.str_rep += ':' + node_name

    def __hash__(self):
        return hash(self.str_rep)

    def __eq__(self, other):
        return self.str_rep == other.str_rep

    def __str__(self):
        return self.str_rep

    def __repr__(self):
        return self.str_rep


_GRAPH_DICT = {}


def get_graph(name, directory=None, existing=False, overwrite=False):
    """Returns or creates a new graph. To open a graph from a existing
    workflow script, see :func:`shrkit.command.open_graph`:

    Args:

        name (str): The graph's name.

        directory (optional, str): The graph's run directory. Pass
         `None` to use the current directory.

        existing (optional, bool): Pass `True` to not create a new
          graph if the named one doesn't exists.

        overwrite (optional, bool): Pass `True` to clean any previous
         graph with the same name and directory.

    Returns: (:obj:`shrkit.workflow.graph.Graph`): The graph instance.

    Raises: (WorkflowError): If existing is `True` and the graph was
     not previously created. Or if the directory doesn't exists.

    """

    if directory is None:
        directory = os.path.dirname(util.get_caller_filepath(1))
    else:
        directory = str(directory)
        directory = os.path.abspath(directory)

    if not os.path.isdir(directory):
        raise WorkflowError(
            'Graphs must be associated to a directory, passed: {}'.format(
                directory))
    uid = UID(directory, name)

    if uid not in _GRAPH_DICT:
        if existing:
            raise WorkflowError("Graph {} in {} doesn't exsits".format(
                name, directory))
        _GRAPH_DICT[uid] = Graph(directory, name)
    elif overwrite:
        _GRAPH_DICT[uid] = Graph(directory, name)

    return _GRAPH_DICT[uid]


@contextmanager
def begin_graph(graph_name, path):
    """Use this context manager to create a graph and add node to
    it. Using this important, because it will bind the graph to the
    current context, as for example, setting the graph directory.

    See the :class:`Graph` documentation for example use.

    """
    path = str(path)
    graph = get_graph(graph_name, path)
    cur_dir = os.path.abspath(os.curdir)
    os.chdir(path)

    try:
        yield graph
    finally:
        os.chdir(cur_dir)


def exists_graph(name, directory=None):
    """Returns whatever a graph exists.

    Args:

        name (str): The graph's name.

        directory (optional, str): The graph's directory. Pass `None` to use
         the caller's directory.

    Returns: (bool): The graph exists.
    """

    if directory is None:
        directory = os.path.dirname(util.get_caller_filepath(1))
    else:
        directory = str(directory)

    return UID(os.path.abspath(directory), name) in _GRAPH_DICT


def get_all_graphs_nodes():
    """Get all nodes from all graphs.

    Returns: Dict[:obj:`shrkit.workflow.graph.UID`:
     :obj:`shrkit.workflow.graph.Node`]: All found nodes.

    """

    nodes = {}
    for graph_uid, graph in _GRAPH_DICT.items():
        for node in graph.node_list:
            node_id = UID(graph_uid.directory, graph_uid.graph_name,
                          node.name)
            nodes[node_id] = node
    return nodes


def get_graphs():
    """Returns a dict with all in memory graphs.

    Returns:

        Dict[str: :obj:`shrkit.workflow.core`]

        All graph instances.
    """
    return _GRAPH_DICT
