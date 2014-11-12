#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import wordgames
version = wordgames.__version__

setup(
    name='wordgames',
    version=version,
    author='',
    author_email='fspoon64+wordgames@gmail.com',
    packages=[
        'wordgames',
    ],
    include_package_data=True,
    install_requires=[
        'Django>=1.6.5',
    ],
    zip_safe=False,
    scripts=['wordgames/manage.py'],
)
