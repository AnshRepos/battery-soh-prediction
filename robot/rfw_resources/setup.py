#!/usr/bin/python
# vim: set fileencoding=utf-8 :

# Copyright (C) Robert Bosch GmbH 2015-2024.
#
# All rights reserved, also regarding any disposal, exploitation,
# reproduction, editing, distribution, as well as in the event of
# applications for industrial property rights.
#
# This program and the accompanying materials are made available
# under the terms of the Bosch Internal Open Source License v4
# which accompanies this distribution, and is available at
# http://bios.intranet.bosch.com/bioslv4.txt
from setuptools import find_packages, setup
from setuptools.command.build_ext import build_ext

long_description = """
A generic resource library""".strip().replace("\n", " ")

setup(
    name="rfwresourcelib",
    version="4.7.3",
    description="Resource library",
    long_description=long_description,
    author="Vashanthkumar PG",
    author_email="Vashanth.KumarPG@in.bosch.com",
    license="For Bosch-internal use only",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Framework :: Pytest",
    ],
    keywords="bosch setuptools",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "rfwresourcelib": [
            "ClewareDLL/*.*",
            "gm/ADB_Shell/*.*",
            "gm/DLT_Connector/*.*",
            "gm/DLT_Connector/plugins/*.*",
            "gm/DLT_Connector/platform/*.*",
            "gm/DLT_Receive/*.*",
        ],
    },
    py_modules=["rfw_resources"],
    zip_safe=False,
    cmdclass={
        "build_ext": build_ext,
    },
)
