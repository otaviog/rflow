#!/usr/bin/env python
"""Test the workflow.command functions.
"""

from pathlib import Path
import unittest

import rflow

from rflow._util import work_directory

# pylint: disable=missing-docstring


class TestCommand(unittest.TestCase):
    WORKFLOW1_PATH = str(Path(__file__).parent / 'resources' /
                         'workflow1')

    def test_open_graph(self):
        wf_graph = rflow.open_graph(TestCommand.WORKFLOW1_PATH,
                                   'workflow1')
        self.assertIsNotNone(wf_graph)

        with self.assertRaises(rflow.WorkflowError):
            rflow.open_graph(
                TestCommand.WORKFLOW1_PATH,
                'no-workflow')

        with self.assertRaises(FileNotFoundError):
            rflow.open_graph(TestCommand.WORKFLOW1_PATH + "bar", 'workflow1')

    def test_main(self):
        task_result = (Path(__file__).parent / 'resources' /
                       'workflow1' / 'sub.pkl')

        with work_directory(TestCommand.WORKFLOW1_PATH):
            rflow.command.main(['', 'workflow1', 'run', 'sub'])

        self.assertTrue(task_result.exists())
        g = rflow.open_graph(TestCommand.WORKFLOW1_PATH,
                            'workflow1')
        g.sub.update()
        self.assertFalse(g.sub.is_dirty())

        with work_directory(TestCommand.WORKFLOW1_PATH):
            rflow.command.main(['', 'workflow1', 'clean', 'sub'])

        self.assertFalse(task_result.exists())
        g = rflow.open_graph(TestCommand.WORKFLOW1_PATH,
                            'workflow1')
        g.sub.update()
        self.assertTrue(g.sub.is_dirty())

        with work_directory(TestCommand.WORKFLOW1_PATH):
            rflow.command.main(['', 'workflow1', 'touch', 'sub'])
        self.assertFalse(task_result.exists())
        g.sub.update()
        self.assertTrue(g.sub.is_dirty())

        with work_directory(TestCommand.WORKFLOW1_PATH):
            rflow.command.main(['', 'workflow1', 'help', 'sub'])

        viz_path = (Path(__file__).parent / 'resources' /
                    'workflow1' / 'workflow.png')
        with work_directory(TestCommand.WORKFLOW1_PATH):
            rflow.command.main(['', 'workflow1', 'viz-dag', '--output',
                               'workflow'])
        self.assertTrue(viz_path.exists())
