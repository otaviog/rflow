"""
Workflow visualization.
"""

from collections import OrderedDict
from io import StringIO

import tabulate as tab
import graphviz

from .core import BaseNode
from .node import Node, ReturnSelNodeLink, DependencyLink


def _break_multi_line(string, max_line=40):
    strio = StringIO()

    line_len = 0
    for char in string:
        if char == '\n':
            line_len = 0
            continue

        strio.write(char)
        if line_len == max_line:
            strio.write('\n')
            line_len = 0
            continue

        line_len += 1
    return strio.getvalue()


class _LinkIDGen:
    def __init__(self):
        self.counter = 0

    def __call__(self):
        nid = '__xyz{}'.format(self.counter)
        self.counter += 1
        return nid


def tabulate(in_dict):
    """Pretty print a dictionary into a table.

    Keys are set as table headers.

    Args:

        in_dict (dict): Source dictionary.

    Returns:
        str:

        Pretty table.
    """
    clean_dict = OrderedDict()
    for key, value in in_dict.items():
        if not isinstance(value, list):
            value = [value]
        clean_dict[key] = value

    return tab.tabulate(clean_dict, headers="keys", tablefmt='psql')


def dag2dot(graph):
    """Creates a graphviz view of a Graph.

    Args:

        graph (:obj:`shrkit.workflow.Graph`): Target graph.

    Returns:
        :obj:`graphviz.Digraph`:

        Graphviz representation of the workflow using the
        graphviz (https://github.com/xflr6/graphviz) library.

    """
    dot = graphviz.Digraph(graph.name, format='png')
    link_id_gen = _LinkIDGen()

    outgraph_nodes = []

    def _put_measurement(node, link_id_gen=link_id_gen):
        if not isinstance(node, Node):
            return
        meas = node.get_measurement()
        if not meas:
            return
        meas_id = link_id_gen()
        meas = tabulate(meas)
        dot.node(meas_id, str(meas), shape="box", style="filled",
                 fontname="monospace", fillcolor="MistyRose")
        dot.edge(node.name, meas_id)

    for node in graph.node_list:
        dot.node(node.name, _break_multi_line(node.get_view_name()),
                 shape="rect", style="rounded,filled", fillcolor="LightCyan",
                 fontname="Roboto")

        for edgename, edge in node.get_edges():
            line_style = {"fontname": "Roboto"}
            if edgename in node.non_collateral():
                continue
            if isinstance(edge, BaseNode):
                edge_id = edge.name
                edge_graph = edge.__dict__.get("graph", None)
                if edge_graph and edge_graph != graph:
                    outgraph_nodes.append(edge)

                if isinstance(edgename, DependencyLink):
                    label = ""
                    line_style.update({"style": "dashed"})
                else:
                    label = edgename

                if isinstance(edge, ReturnSelNodeLink) and edge.name == edgename:
                    label = "{}[{}]".format(label, edge.return_index)
            else:
                label = edgename
                edge_id = link_id_gen()

                content = "{}({})".format(edge.__class__.__name__,
                                          _break_multi_line(str(edge), 40))
                dot.node(edge_id, content,
                         shape="rectangle", style="dotted,filled", fillcolor="Beige",
                         fontname="Helvetica")

                if edgename == "resource":
                    line_style = line_style.update(
                        dict(style="bold,dotted", arrowhead="none"))

            dot.edge(edge_id, node.name, label, line_style)

        _put_measurement(node)

    for other_node in outgraph_nodes:
        dot.node(other_node.get_view_name(), "{}.{}".format(
            other_node.graph.name, other_node.get_view_name()),
            fontname="Roboto")
        _put_measurement(other_node)

    return dot
