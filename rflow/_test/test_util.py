#!/usr/bin/env python
"""Tests the private util package.
"""

import unittest
import os

import rflow._util as util
from . import resources

#pylint: disable=missing-docstring


class TestUtil(unittest.TestCase):
    def test_work_directory(self):
        """Test working directory context"""
        curdir = os.path.abspath(os.curdir)
        resources_dir = os.path.abspath(os.path.dirname(resources.__file__))
        with util.work_directory(resources_dir):
            self.assertEqual(os.path.abspath(os.curdir),
                             resources_dir)

        self.assertEqual(curdir, os.path.abspath(os.curdir))


if __name__ == '__main__':
    unittest.main()
