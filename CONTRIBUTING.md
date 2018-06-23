# Development Values

* Reproducible research;
* Precise and accurate implementations from authors;
* Easy deploy;
* Good Documentation;
* Simple API.

# Environment setup

Grab it:

```Shell
$ git clone git@gitlab.com:shrkit/shape-retrieval-toolkit.git
```

## Linux

Prepare [ShapeLab](shapelab/CONTRIBUTING.md) for development.

```Shell
shape-retrieval-toolkit$ pip install -e .
shape-retrieval-toolkit$ pip install -r requirements-dev.txt
```

## Code Guidelines

* Python docstring format is Google's style, [more
  info](http://www.sphinx-doc.org/en/1.5.1/ext/example_google.html#example-google)

## Code checklist

* Unit testing (except for some datasets and database tasks)
  - [ ] _test package
  - [ ] target in tasks-unittest.mk
  - [ ] all tests passing
* API documentation
  - [ ] Generation OK
* Deployment
  - [ ] [setup.py](setup.py) package and entry points
  - [ ] Continuous build
* UI check:
  - [ ] progressbar
  
