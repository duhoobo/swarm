#!/usr/bin/env python

import os.path

from setuptools import setup, find_packages


ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))


setup(
    name="swarm",
    version="0.1",
    author="Hungpo DU",
    author_email="alecdu@gmail.com",
    url="https://github.com/duhoobo/swarm",
    description="TODO",
    long_description=open(os.path.join(ROOT, "README.md")).read(),
    license="PSF",
    keywords="",

    packages=find_packages(
        exclude=("tests", "tests.*")
    ),

    include_package_data=True,

    install_requires=[
        "click>=6.2",
        "gevent>=1.0.2",
        "PyYAML>=3.11",
    ],
    entry_points={
        "console_scripts": [
            "swarm = swarm.server:run"
        ]
    },

    classifiers=[],
)
