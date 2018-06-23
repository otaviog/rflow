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
