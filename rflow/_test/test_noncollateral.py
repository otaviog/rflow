#!/usr/bin/env python
"""Tests whatever if the non_collateral flag is workking.
"""

import unittest
from pathlib import Path

import rflow

# pylint: disable=no-self-use,invalid-name,missing-docstring,protected-access

HERE = Path(__file__).parent


class A(rflow.Interface):
    eval_count = 0
    load_count = 0

    def non_collateral(self):
        return ["v2"]

    def evaluate(self, resource, v1, v2):
        A.eval_count += 1
        resource.pickle_dump(v1)

        if v2:
            print(v1)
        return v1

    def load(self, resource, v2):
        A.load_count += 1
        v1 = resource.pickle_load()
        if v2:
            print(v1)
        return v1


class TestNonCollateral(unittest.TestCase):
    def test_non_collateral(self):
        with rflow.begin_graph("collateral-test", HERE) as g:
            g.a = A()
            g.a.resource = rflow.FSResource("collateral-v1.pkl")

            g.a.args.v1 = 1
            g.a.args.v2 = True
            g.a.call()

            g.a.args.v2 = False
            g.a._is_dirty = True
            g.a.value = rflow.Uninit
            g.a.call()

            g.a.args.v1 = 2
            g.a._is_dirty = True
            g.a.value = rflow.Uninit
            g.a.call()

        self.assertEqual(1, A.load_count)
        self.assertEqual(2, A.eval_count)


if __name__ == "__main__":
    unittest.main()
