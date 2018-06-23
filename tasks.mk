about-tasks:
	@echo "Main project tasks"

doc-create:
	rm -f doc/source/shrkit.*.rst
	sphinx-apidoc -o doc/source/ shrkit
	rm doc/source/modules.rst doc/source/shrkit.rst
	make -C doc/ html

doc-open:
	sensible-browser doc/build/html/index.html

pylint:
	python -m pylint rflow

pep8:
	python -m autopep8 --recursive --in-place rflow

local-ci.pages:
	gitlab-ci-multi-runner exec docker pages\
		--docker-pull-policy=never

local-ci:
	gitlab-ci-multi-runner exec docker test\
		--docker-pull-policy=never
