"""
Common definitions of the workflow module.
"""

WORKFLOW_DEFAULT_FILENAME = 'workflow.py'
DOT_DATABASE_FILENAME = '.workflow.lmdb'


class Uninit(object):
    """Sentinel for unitialized values on the framework context. Python's
    `None` can't be used, because `None` can be a valid for the user.

    """

    pass


class WorkflowError(Exception):
    """Base exception for all workflow module errors.

    Args:

        message (str): Error message

        lineinfo (:obj:`._reflection.LineInfo`, optional): Source line
          information. Pointer to errors in user's code.

    """

    def __init__(self, message, lineinfo=None):
        if lineinfo is not None:
            message = '"{}", line {}, in {}\n {}'.format(
                lineinfo.filepath, lineinfo.line, lineinfo.function,
                message)
        super(WorkflowError, self).__init__(message)


class BaseNode:
    """Base methods for nodes. Should be used to create new node types.

    Attributes:

        show (bool): Whatever the node is show on the command line
         help.

    """

    def __init__(self):
        self.show = True

    def call(self, redo=False):
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
