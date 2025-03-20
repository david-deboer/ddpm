#! /usr/bin/env python
# -*- mode: python; coding: utf-8 -*-
# Copyright 2024 David DeBoer
# Licensed under the 2-clause BSD license.

from setuptools import setup
import glob

setup_args = {
    'name': "ddpm",
    'description': "Data Detail Project Management",
    'license': "BSD",
    'author': "David DeBoer",
    'author_email': "david.r.deboer@gmail.com",
    'version': '0.3.3',
    'scripts': glob.glob('scripts/*'),
    'packages': ['ddpm'],
    'include_package_data': True
}

if __name__ == '__main__':
    setup(**setup_args)
