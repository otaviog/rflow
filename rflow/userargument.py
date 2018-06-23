"""User arguments functionality.
"""

from collections import namedtuple
import sys

from . import core


class _UserArgumentsContext:
    ArgumentEntry = namedtuple("ArgumentEntry", [
        "name", "type", "help", "default", "action"])

    def __init__(self):
        self.user_arguments = []
        self._parsed_args = None

    def add_user_argument(self, name, kwargs):
        """Adds an argument to the context. The values added here will be add
        in next command execution.

        Args:

            name (str): The argument name that will be displayed on
             command-line. It's specified with `--`  at front;

            type (type): Expected parameter type.

            help (str): Help message about this argument.

            default (object, optional): Default value if the user
             don't specify one.

        """

        if not next((prev_arg for prev_arg in self.user_arguments
                     if prev_arg == name), False):
            self.user_arguments.append(
                (name, kwargs))

        return name.replace('--', '').replace('-', '_')

    def register_argparse_args(self, args):
        """Register an argparse's arg in this context, so UserArgument nodes
        can get its values.

        Args:

            args (argparse): Whatever argparse.parsers().args
             returns...

        """

        self._parsed_args = args

    def get_user_arg(self, arg_name):
        """Gets a command line from the registered argparse object.

        Args:

            arg_name (str): The argument name, same as if using
             args.<argument_name>. Dashes '-' are converted to
             '_'. Starting prefix '--' should be removed.

        Returns:
            object:

        """
        return self._parsed_args.__getattribute__(arg_name)


USER_ARGS_CONTEXT = _UserArgumentsContext()


class UserArgument(core.BaseNode):
    """Use this class to create node that can be filled by the user.

    Args:

        name (str): The argument name that will be displayed on
         command-line. It's specified with `--`  at front;

        kwargs (dict): Keyword arguments, parsed directly to
         argparse.
    """

    def __init__(self, name, **kwargs):
        # pylint: disable=redefined-builtin
        super(UserArgument, self).__init__()
        self.arg_name = USER_ARGS_CONTEXT.add_user_argument(
            name, kwargs)
        self.name = name
        self.graph = None

    def call(self):
        value = USER_ARGS_CONTEXT.get_user_arg(self.arg_name)
        if value is None:
            print('Required program option {} not set'.format(self.name))
            sys.exit(1)
        return value

    def update(self):
        pass

    def get_hash(self):
        return None

    def is_dirty(self):
        return True

    def get_resource(self):
        return None

    def get_edges(self):
        return []
