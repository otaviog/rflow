#!/usr/bin/env python
"""
Tests the templating node.
"""

import unittest
from pathlib import Path

import rflow

# pylint: disable=missing-docstring,invalid-name,no-self-use

HERE = Path(__file__).parent
RESOURCES = HERE / "resources"


class NodeTemplate(unittest.TestCase):
    def _textfile_equals(self, text_filepath, expected):
        with open(str(text_filepath), 'r') as file:
            self.assertEqual(file.readline(), expected)

    def test_template(self):
        g = rflow.get_graph('test_template')
        g.template = rflow.shell.TemplateFile(['HELLO', 'WHAT'])
        with g.template as args:
            args.HELLO = "Hello"
            args.WHAT = "World"
            args.template_resource = rflow.FSResource(
                RESOURCES / 'txt1.txt.template')

        g.template.resource = rflow.FSResource(RESOURCES / 'txt1.txt')
        g.template.call()
        self._textfile_equals(RESOURCES / 'txt1.txt',
                              'Hello this is a World ?')

        g.template.resource = rflow.FSResource(RESOURCES / 'txt2.txt')
        g.template.call()
        self._textfile_equals(RESOURCES / 'txt2.txt',
                              'Hello this is a World ?')

        g.template.args.template_resource = rflow.FSResource(
            RESOURCES / 'txt2.txt.template')

        g.template.call()
        self._textfile_equals(RESOURCES / 'txt2.txt', 'World, Hello ?')


if __name__ == '__main__':
    unittest.main()
