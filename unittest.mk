about:
	@echo Unit testing automation

all:
	python -m unittest discover

doctest:
	python doc/doctest_runner.py

node:
	python -m unittest rflow._test.test_node

node.simple:
	python -m unittest\
		rflow._test.test_node.NodeTest.test_simple

node.task:
	python -m unittest rflow._test.test_node.NodeTest.test_task

reentrancy:
	python -m unittest rflow._test.test_reentrancy

dependency:
	python -m unittest rflow._test.test_dependency

dependency.implicit:
	python -m unittest\
		rflow._test.test_dependency.DependencyTest.test_implicit

dependency.resource_link:
	python -m unittest\
		rflow._test.test_dependency.DependencyTest.resource_link

noncollateral:
	python -m unittest\
		rflow._test.test_noncollateral

shell.template:
	python -m unittest rflow._test.test_template

util:
	python -m unittest rflow._test.test_util

command:
	python -m unittest rflow._test.test_command

graph:
	python -m unittest rflow._test.test_graph
