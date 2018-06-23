"""Basic Shell UI
"""
import sys
import traceback

from termcolor import colored


def _sys_exit(_):
    sys.exit(1)


def _raise_exception(exp):
    raise exp


BAR_SYMBOL = "."
END_SYMBOL = "^"


class ShellIO:
    """Workflow input/output interface for command-line output.
    """

    def __init__(self):
        self.call_depth = 0
        self._out = sys.stdout
        self._color_stack = []
        self._avail_colors = ["green", "yellow",
                              "blue", "magenta", "cyan", "white", "grey"]
        self._color_count = 0
        self._traceback_policy = None
        self.set_traceback_policy()

    def set_traceback_policy(self, policy="sys-exit"):
        """Sets what the interface should we an print_traceback
        happens. Default is exit the process. But it may raise a
        exception.

        Args:

            policy (str): Policy type. Use "sys-exit" to quit the
             process or "raise-exp" to raise a
             :obj:`rflow.common.WorkflowError`. The later is
             useful for unit-testing.

        """
        policy_map = {"sys-exit": _sys_exit,
                      "raise-exp": _raise_exception}

        try:
            self._traceback_policy = policy_map[policy]
        except KeyError:
            raise Exception("Unknown policy {}".format(policy))

    def _get_new_color(self):
        idx = self._color_count % len(self._avail_colors)
        color = self._avail_colors[idx]
        self._color_stack.append(color)
        self._color_count += 1
        return color

    def _pop_color(self):
        color = self._color_stack.pop()
        self._color_count -= 1

        return color

    def executing_evaluate(self, node):
        """Shows evaluation execution info.
        """
        color = self._get_new_color()
        self._out.write(BAR_SYMBOL * self.call_depth)
        self._out.flush()
        self._out.write(
            colored("RUN  {}:{}\n".format(node.graph.name, node.name), color))
        self._out.flush()
        self.call_depth += 1

    def done_evaluate(self, node):
        """Shows evaluation done info.
        """

        self.call_depth -= 1
        color = self._pop_color()

        self._out.write(BAR_SYMBOL * self.call_depth)
        self._out.write(END_SYMBOL)
        self._out.write(colored(
            "{}:{}\n".format(node.graph.name, node.name),
            color))
        self._out.flush()

    def executing_load(self, node):
        """Shows load execution info.
        """

        self._out.write(BAR_SYMBOL * self.call_depth)
        self._out.write(colored(
            "LOAD {}:{}\n".format(node.graph.name, node.name),
            self._get_new_color()))
        self._out.flush()
        self.call_depth += 1

    def done_load(self, node):
        """Shows load done info.
        """

        self.call_depth -= 1
        self._out.write(BAR_SYMBOL * self.call_depth)
        self._out.write(END_SYMBOL)
        self._out.write(colored(
            "DONE {}:{}\n".format(node.graph.name, node.name),
            self._pop_color()))
        self._out.flush()

    def error_ocurred(self, node, error_message):
        # pylint: disable=no-self-use
        """Shows an error. Does not call the :func:`print_traceback`.
        """

        print(colored("{}:{}, {}".format(
            node.graph.name,
            node.name, error_message), "red"))

    def executing_touch(self, node):
        """Shows touch execution info."""
        self._out.write(BAR_SYMBOL*self.call_depth)
        self._out.write(colored("{}:{}.touch\n".format(
            node.graph.name,
            node.name), "magenta"))

        self._out.flush()
        self.call_depth += 1

    def done_touch(self, node):
        """Shows touch done info."""
        self.call_depth -= 1
        self._out.write(BAR_SYMBOL*self.call_depth)
        self._out.write(colored("DONE {}:{}\n".format(
            node.graph.name,
            node.name), "magenta"))
        self._out.flush()

    def print_traceback(self, exec_info, exp, cnt=1):
        """Prints an error traceback. It will call the traceback policy. See
        :func:`set_traceback_policy`"""

        extracts = traceback.extract_tb(exec_info[2])
        count = len(extracts)
        traceback.print_exc(limit=-count + cnt)
        self._traceback_policy(exp)


ui = ShellIO()
