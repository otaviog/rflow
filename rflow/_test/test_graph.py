#!/usr/bin/env python
"""graph.py unit-testing.
"""

import unittest
from pathlib import Path

import rflow

# pylint: disable=missing-docstring,no-self-use,invalid-name

HERE = Path(__file__).parent


class _HelloNode(rflow.Interface):
    def evaluate(self, message):
        print(message)


class TestUtil(unittest.TestCase):
    def test_get(self):
        self.assertFalse(rflow.core.exists_graph("foo"))
        with self.assertRaises(rflow.WorkflowError):
            rflow.get_graph("foo", existing=True)

        g = rflow.get_graph("foo")
        g.hello = _HelloNode()
        g.hello.args.message = "Hello"

        self.assertEqual("foo", g.name)
        self.assertEqual("hello", g.hello.name)

        g = rflow.get_graph("foo", overwrite=True)
        self.assertEqual(0, len(g.node_list))

        gg = rflow.get_graph("foo", HERE / "resources")
        self.assertNotEqual(g, gg)

        self.assertTrue(rflow.core.exists_graph("foo"))
        self.assertTrue(rflow.core.exists_graph("foo", HERE))
        self.assertTrue(rflow.core.exists_graph("foo", HERE / "resources"))

    def test_begin(self):
        with rflow.begin_graph("test_graph", HERE) as g:
            g.hello = _HelloNode()
            g.hello.args.message = "Hello"

        gg = rflow.get_graph("test_graph", existing=True)
        self.assertEqual(g, gg)

    def test_prefix(self):
        with rflow.begin_graph("test_prefix", HERE) as g:
            with g.prefix("p1_") as g1:
                g1.hello = _HelloNode()
                g1.hello.args.message = "Hello 1"

            with g.prefix("p2_") as g2:
                g2.hello = _HelloNode()
                g2.hello.args.message = "Hello 2"

        self.assertEqual(["p1_hello", "p2_hello"],
                         [n.name for n in g.node_list])


if __name__ == '__main__':
    unittest.main()
