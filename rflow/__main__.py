#!/usr/bin/env python
"""Entry point for CLI use.
"""

# PYTHON_ARGCOMPLETE_OK

from . import command


def main():
    """rflow Main entry point.
    """
    return command.main()
