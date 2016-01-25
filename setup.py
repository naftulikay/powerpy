#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = "powerpy",
    description = "A slideshow REST API in Python.",
    version = "0.1.0",
    license = "MIT",
    packages = find_packages('src'),
    package_dir = { '': 'src'},
    install_requires = ['setuptools',
        'tornado == 4.3'
    ],
    entry_points = {
        'console_scripts': [
            'powerpy-web = powerpy.web:start_webserver'
        ],
    },
    zip_safe = True
)
