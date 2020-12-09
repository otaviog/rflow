"""Command-line interfacing workflows"""


import argparse
import os
import sys
import imp
import inspect

import argcomplete

from . import core
from . common import WorkflowError, WORKFLOW_DEFAULT_FILENAME
from . import decorators
from . userargument import USER_ARGS_CONTEXT
from . _ui import ui
from . import _util as util


def _importdir(path, workflow_fname):
    module_name = path.replace('/', '.')
    path = os.path.abspath(path)
    if module_name[0] == '.':
        module_name = module_name[1:]
    fname = os.path.join(path, workflow_fname)
    if not os.path.exists(fname):
        raise WorkflowError('Workflow {} file not found'.format(fname))

    try:
        return imp.load_source('workflow', fname)
    except IOError:
        raise WorkflowError('Workflow {} file not found'.format(fname))


def _get_decorator(func, class_instance):
    if not inspect.isfunction(func):
        return None

    if not hasattr(func, '__closure__') or func.__closure__ is None:
        return None

    for closure in func.__closure__:
        if isinstance(closure.cell_contents, class_instance):
            return closure.cell_contents
    return None


class _GraphDef:
    def __init__(self, graph_name, function, decorator_obj):
        self.name = graph_name
        self.function = function
        self.drecorator_obj = decorator_obj


def _get_all_graph_def(abs_path, workflow_fname):
    with util.work_directory(abs_path):
        module = _importdir(abs_path, workflow_fname)

        graph_def_list = []
        for func_name, member in inspect.getmembers(module):
            decorator_obj = _get_decorator(member, decorators.graph)
            if decorator_obj is None:
                continue

            graph_def_list.append(_GraphDef(func_name, member, decorator_obj))

        return graph_def_list


def open_graph(directory, graph_name, wf_filename=WORKFLOW_DEFAULT_FILENAME):
    """Opens an existing workflow and return the specified graph instance.

    Args:

        directory (str): A directory containg a `workflow.py` file, or
         a file named by the `wf_filename` argument.

        graph_name (str): The graph's name to open, see
         :func:`rflow.decorators.graph`

        wf_filename (str): The workflow python script. Default is
         `"workflow.py"`.

    Returns:

        :obj:`rflow.core.Graph`: DAG object.

    Raises:

        :obj:`rflow.common.WorkflowError`: If the graph
         isn't found.

        `FileNotFoundError`: If the directory doesn't exists or if the
         `workflow.py` or what passed to `wf_filename` does not
         exists.

    """
    if core.exists_graph(graph_name, directory):
        return core.get_graph(graph_name, directory, existing=True)

    graph_def_list = _get_all_graph_def(
        os.path.abspath(directory), wf_filename)

    defgraph_info_list = [graph_def for graph_def in graph_def_list
                          if graph_def.name == graph_name]

    if not defgraph_info_list:
        raise WorkflowError(
            "Graph not {} found on directory {}. Available ones are: {}".format(
                graph_name, directory, ', '.join(
                    [deco.name for _1, _2, deco in defgraph_info_list])))
    else:
        defgraph_info = defgraph_info_list[0]

    defgraph_info.function()

    return core.get_graph(graph_name, directory, existing=True)


def _run_main(graph, argv):
    arg_parser = argparse.ArgumentParser(
        description="Executes the workflow to a node.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    node_names = graph.get_node_names(filter_show=True)
    arg_parser.add_argument(
        'node', choices=node_names,
        metavar='node', help=', '.join(node_names))
    arg_parser.add_argument(
        '--redo', '-r',
        help="Redo the last node, whatever even if it's updated",
        action='store_true')

    name_set = set()
    for name, kwargs in (
            USER_ARGS_CONTEXT.user_arguments):
        # TODO compare if they're exact the same or
        # raise an exception.
        if name in name_set:
            continue
        arg_parser.add_argument(name, **kwargs)
        name_set.add(name)

    args = arg_parser.parse_args(argv)

    USER_ARGS_CONTEXT.register_argparse_args(args)

    goal_node = graph[args.node]
    goal_node.call(redo=args.redo)


def _clean_main(graph, argv):
    arg_parser = argparse.ArgumentParser(
        description="Clean the node resources and last execution parameters.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    node_names = graph.get_node_names()
    arg_parser.add_argument(
        'node', choices=graph.get_node_names(),
        metavar='node', help=', '.join(node_names))

    args = arg_parser.parse_args(argv)

    goal_node = graph[args.node]
    goal_node.clear()


def _touch_main(graph, argv):
    arg_parser = argparse.ArgumentParser(
        description="Set the node's last parameters to the current ones without executing it.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    node_names = graph.get_node_names(filter_show=True)
    arg_parser.add_argument(
        'node', choices=node_names,
        metavar='node', help=', '.join(node_names))

    args = arg_parser.parse_args(argv)
    USER_ARGS_CONTEXT.register_argparse_args(args)

    goal_node = graph[args.node]
    goal_node.touch()


def _help_main(graph, argv):
    arg_parser = argparse.ArgumentParser()

    node_names = graph.get_node_names()
    arg_parser.add_argument(
        'node', choices=graph.get_node_names(),
        metavar='node', help=', '.join(node_names))

    args = arg_parser.parse_args(argv)
    goal_node = graph[args.node]
    sys.stdout.write(goal_node.__doc__)
    sys.stdout.write('\n')


def _viz_main(graph, argv):
    from .viz import dag2dot

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--output', '-o')

    args = arg_parser.parse_args(argv)

    dot = dag2dot(graph)
    if args.output:
        dot.render(args.output, cleanup=True)
    else:
        dot.view(cleanup=True)


ACTIONS = ['run', 'touch', 'print-run', 'viz-dag', 'help', 'clean']


def main(argv=None):
    """Command-line auto main generator.

    Generates a command-line main for executing the graphs defined in
    the current source file. See the decorator
    :class:`rflow.decorators.graph` for how to define
    graphs. The default behavior is quit the process when an error is
    encountered.


    For example::

        @srwf.graph()
        def workflow1(g):
            g.add = Add()
            g.add.args.a = 1

            g.add.args.b = 2

            g.sub = Sub(srwf.FSResource('sub.pkl'))
            g.sub.args.a = 8
            g.sub.args.b = g.add

        if __name__ == '__main__':
            srwf.command.main()

    In a shell execute::

        $ srwf workflow1 run sub

    For passing custom arguments by command-line, use the class
    :class:`rflow.userargument.UserArgument`.

    Args:

        args (str, optional): sys.args like command-line arguments.

    Returns:

        int: exit code.

    """
    # pylint: disable=too-many-return-statements
    try:
        all_graphs = _get_all_graph_def(os.path.abspath(os.path.curdir),
                                        WORKFLOW_DEFAULT_FILENAME)
    except WorkflowError as err:
        print(str(err))
        return 1

    arg_parser = argparse.ArgumentParser(
        description="RFlow workflow runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument(
        'graph', choices=[graph.name for graph in all_graphs])
    arg_parser.add_argument('action', choices=ACTIONS)
    argcomplete.autocomplete(arg_parser)
    if not argv:
        argv = sys.argv

    args = arg_parser.parse_args(argv[1:3])

    if int(os.environ.get("RFLOW_DEBUG", 0)) == 1:
        ui.complete_traceback = True

    abs_path = os.path.abspath('.')
    graph = open_graph(abs_path, args.graph)

    argv = argv[3:]
    if args.action == 'print-run':
        raise NotImplementedError()
    elif args.action == 'run':
        return _run_main(graph, argv)
    elif args.action == 'touch':
        return _touch_main(graph, argv)
    elif args.action == 'clean':
        return _clean_main(graph, argv)
    elif args.action == 'help':
        return _help_main(graph, argv)
    elif args.action == 'viz-dag':
        return _viz_main(graph, argv)

    return 1
