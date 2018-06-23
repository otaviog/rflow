#!/usr/bin/env python

"""Tests Node/Interface executions.
"""

import os
import shutil
import unittest
import pickle
from pathlib import Path
from contextlib import suppress

import rflow
from . import resources


HERE = Path(__file__).parent

# pylint: disable=no-self-use,invalid-name,missing-docstring


class A(rflow.Interface):

    """ Simple node definition in rflow.
    """

    def evaluate(self, v1, v2, v3):
        """Node's computation.
        """

        return v1 + v2 + v3


class B(rflow.Interface):
    """Another simple node definition.
    """

    def evaluate(self, v1):
        """
        Nodes's "computation"
        """
        return v1


class C(rflow.Interface):
    """Another simple node definition. Return two values.
    """

    def evaluate(self, v1, v2):
        """
        Nodes's "computation"
        """

        return v1, v2


class T(rflow.Interface):
    """Node definition using resource.
    """

    def evaluate(self, resource, v1, v2, v3):
        v = v1 * v2 + v3
        with open(resource.filepath, "wb") as stream:
            pickle.dump(v, stream)
        return v

    def load(self, resource):
        with open(resource.filepath, "rb") as stream:
            return pickle.load(stream)


class DependsOnFile(rflow.Interface):
    def evaluate(self, resource):
        with open(resource.filepath, "r") as stream:
            return [line.strip() for line in stream.readlines()]


class NodeTest(unittest.TestCase):
    def _clean(self):
        db_path = HERE / rflow.core.DOT_DATABASE_FILENAME
        if db_path.exists():
            shutil.rmtree(str(db_path))

        with suppress(FileNotFoundError):
            os.remove(HERE / "T1.pickle")
            os.remove(HERE / "T2.pickle")

    def tearDown(self):
        self._clean()

    def setUp(self):
        self._clean()

    def test_simple(self):
        with rflow.begin_graph("simple", HERE) as g:
            a = g.a = A()

            a.args.v1 = 1
            a.args.v2 = 3
            a.args.v3 = 4

            self.assertEqual(8, g.a.call())

    def test_link_simple(self):
        with rflow.begin_graph("link-simple", HERE) as g:
            a = g.a = A()
            a.args.v1 = 3
            a.args.v2 = 2
            a.args.v3 = 4

            b = g.b = B()
            b.args.v1 = a

        self.assertEqual(9, b.call())

    def test_link_simple2output(self):
        with rflow.begin_graph("link-simple2output", HERE) as g:
            c = g.c = C()
            c.args.v1 = 4
            c.args.v2 = 5

            a = g.a = A()
            a.args.v1 = c[0]
            a.args.v2 = c[1]
            a.args.v3 = 4

        self.assertEqual(13, a.call())

    def test_task(self):
        with rflow.begin_graph("task", HERE) as g:
            t1 = g.t1 = T()
            t1.args.v1 = 4
            t1.args.v2 = 3
            t1.args.v3 = 2

            # R = 4 * 3 + 2 = 14
            t1.resource = rflow.FSResource("T1.pickle")

            t2 = g.t2 = T()
            t2.args.v1 = t1
            t2.args.v2 = 5
            t2.args.v3 = t1
            # 14 * 5 + 14 = 84
            t2.resource = rflow.FSResource("T2.pickle")

            c = g.c = C()
            c.args.v1 = t2
            c.args.v2 = t2

        self.assertEqual(84, c.call()[0])
        self.assertEqual(84, c.call()[1])

    def test_depends_on_file(self):
        with rflow.begin_graph("depends_on_file", HERE) as g:
            t = g.t = DependsOnFile()
            t.resource = rflow.FSResource(os.path.join(
                resources.HERE, "sample-lines.txt"))

        self.assertEqual(["line 1", "line 2", "line 3"], t.call())

    def test_arg_not_set(self):
        with rflow.begin_graph("arg_not_set", HERE) as g:
            a = g.a = A()
            a.args.v1 = 3
            # a.args.v2 = 2
            a.args.v3 = 4

            g.b = b = B()
            b.args.v1 = a

        with self.assertRaises(rflow.WorkflowError):
            b.call()

    def test_resource_not_set(self):
        with rflow.begin_graph("resource_node_set", HERE) as g:
            t1 = g.t1 = T()
            t1.args.v1 = 4
            t1.args.v2 = 3
            t1.args.v3 = 2
            # t1.resource = rflow.FSResource("T1.pickle")

        with self.assertRaises(rflow.WorkflowError):
            t1.call()


if __name__ == "__main__":
    unittest.main()
