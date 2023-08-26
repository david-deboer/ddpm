#! /usr/bin/env python
# -*- mode: python; coding: utf-8 -*-
# Copyright 2024 David DeBoer
# Licensed under the 2-clause BSD license.

from setuptools import setup
import glob

setup_args = {
    'name': "ddgantt",
    'description': "simple gantt",
    'license': "BSD",
    'author': "David DeBoer",
    'author_email': "david.r.deboer@gmail.com",
    'version': '0.1',
    'packages': ['ddgantt']
    #'install_requires': ['pyyaml', 'json']
}

if __name__ == '__main__':
    setup(**setup_args)
