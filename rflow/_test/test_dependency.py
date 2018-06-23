#!/usr/bin/env python
"""Test using dependencies style connections.

"""

import unittest
import os

import rflow
from rflow import _ui

# pylint: disable=missing-docstring,invalid-name,no-self-use

HERE = os.path.dirname(__file__)


class GenFile(rflow.Interface):

    def evaluate(self, resource, p1, p2):
        with open(resource.filepath, 'w') as file:
            file.write('{} - {}\n'.format(p1, p2))


class ExplictUseFile(rflow.Interface):

    def evaluate(self, input_resource):
        with open(input_resource.filepath, 'r') as file:
            return file.readlines()


class ImplicitUseFile(rflow.Interface):
    def evaluate(self, input_filename):

        with open(input_filename, 'r') as file:
            return file.readlines()


class DependencyTest(unittest.TestCase):
    GENFILE_PATH = os.path.join('resources', 'gen-file.txt')

    @classmethod
    def setUpClass(cls):
        _ui.ui.set_traceback_policy('raise-exp')

    def setUp(self):
        try:
            os.remove(os.path.join(HERE, DependencyTest.GENFILE_PATH))
        except:
            pass

    def test_resource_link(self):
        with rflow.begin_graph('explict', HERE) as gh:
            gh.g = GenFile()
            gh.g.resource = rflow.FSResource(DependencyTest.GENFILE_PATH)
            gh.g.args.p1 = 4
            gh.g.args.p2 = 'Hello'

            gh.u = ExplictUseFile()
            gh.u.args.input_resource = gh.g.resource

        self.assertEqual(['4 - Hello\n'], gh.u.call())

    def test_implicit(self):
        with rflow.begin_graph('implicit', HERE) as gh:
            gh.g = GenFile()
            gh.g.resource = rflow.FSResource(DependencyTest.GENFILE_PATH)
            gh.g.args.p1 = 5
            gh.g.args.p2 = 'bye'

            gh.u = ImplicitUseFile()
            gh.u.args.input_filename = DependencyTest.GENFILE_PATH

        with self.assertRaises(IOError):
            gh.u.call()

        gh.u.require(gh.g)
        self.assertEqual(['5 - bye\n'], gh.u.call())


if __name__ == '__main__':
    unittest.main()
