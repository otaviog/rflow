"""A setuptools based setup module for rflow
"""

import sys
from os import path
from codecs import open
from setuptools import setup, find_packages


def _forbid_publish():
    argv = sys.argv
    blacklist = ['register', 'upload']

    for command in blacklist:
        if command in argv:
            values = {'command': command}
            print('Command "%(command)s" has been blacklisted, exiting...' %
                  values)
            sys.exit(2)


_forbid_publish()

HERE = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

REQUIREMENTS = [
    'argcomplete',
    'graphviz',
    'lmdb',
    'requests',
    'tabulate',
    'termcolor',
    'tqdm'
]


setup(
    name='rflow',
    version='0.0.1',
    description='Framework for creating end-to-end experiments on Machine Learning and Information Retrieval',
    long_description=LONG_DESCRIPTION,
    url='https://gitlab.com/shrkit/rflow/',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7'
    ],
    keywords='end-to-end workflow reentrant make machine-learning ',
    packages=find_packages(),
    install_requires=REQUIREMENTS,
    extras_require={
        'dev': ['Sphinx',
                'sphinx_rtd_theme',
                'sphinxcontrib-napoleon',
                'docutils',
                'pylint',
                'autopep8'],
        'test': ['coverage'],
    },
    entry_points={
        'console_scripts': [
            'rflow=rflow.__main__:main'
        ]
    }
)
