#!/usr/bin/env python
"""Test reentrancy capabilities of the workflow module.
"""

import unittest
import os
import pickle
from pathlib import Path
from contextlib import suppress

import rflow
from rflow.common import Uninit


# pylint: disable=missing-docstring,no-self-use,invalid-name

HERE = Path(__file__).parent


class T1(rflow.Interface):
    """Simple resource task. Counts how many times eval (`eval_count`) and
    load were called. Verifies if reentrancy is being OK.
    """
    eval_count = 0
    load_count = 0

    def evaluate(self, resource, v1):
        T1.eval_count += 1
        v = v1 * 100
        with open(resource.filepath, "wb") as stream:
            pickle.dump(v, stream)
        return v

    def load(self):
        T1.load_count += 1

        with open(self.resource.filepath, "rb") as stream:
            return pickle.load(stream)


class T2(rflow.Interface):
    eval_count = 0
    load_count = 0

    def evaluate(self, resource, x2):
        T2.eval_count += 1
        v = x2 * 8
        with open(resource.filepath, "wb") as stream:
            pickle.dump(v, stream)
        return v

    def load(self, resource):
        T2.load_count += 1
        with open(resource.filepath, "rb") as stream:
            return pickle.load(stream)


class NodeTest(unittest.TestCase):
    def setUp(self):
        with suppress(FileNotFoundError):
            os.remove(HERE / "T1.pickle")
            os.remove(HERE / "T2.pickle")

    def test_simple(self):
        with rflow.begin_graph("reentrancy", HERE) as g:
            g.t1 = T1()
            g.t1.args.v1 = 5
            g.t1.resource = rflow.FSResource("T1.pickle")

            g.t2 = T2()
            g.t2.args.x2 = g.t1
            g.t2.resource = rflow.FSResource("T2.pickle")

        # First call, all evals must be 1
        self.assertEqual(4000, g.t2.call())
        self.assertEqual(1, T1.eval_count)
        self.assertEqual(1, T2.eval_count)
        self.assertEqual(0, T1.load_count)
        self.assertEqual(0, T2.load_count)

        # Next test will forget the values, and expects only t2 be
        # loaded. Because t1 didn't change values and t2 has a
        # resource.

        # forget values
        g.t1._is_dirty = True
        g.t2._is_dirty = True
        g.t1.value = Uninit
        g.t2.value = Uninit

        self.assertEqual(4000, g.t2.call())

        self.assertEqual(1, T1.eval_count)
        self.assertEqual(1, T2.eval_count)
        self.assertEqual(0, T1.load_count)
        self.assertEqual(1, T2.load_count)


if __name__ == "__main__":
    unittest.main()
