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

import platform

from setuptools import find_packages, setup
from setuptools.command.build_ext import build_ext

long_description = """
A generic resource library""".strip().replace("\n", " ")
install_requires = {}
install_requires["Linux"] = [
    "psutil",
    "pyvisa",
    "pyvisa-py",
    "typing_extensions==4.0.1",
    "requests==2.26.0",
    "pyserial==3.4",
    "robotframework==6.0",
    "pure-python-adb==0.2.3.dev0",
    "imutils==0.5.4",
    "opencv-python==4.5.4.60",
    "robotframework-sshlibrary==3.4.0",
    "pyttsx3==2.7",
    "schedule==1.1.0",
    "jira==3.2.0",
    "xlrd==1.2.0",
    "pytesseract",
]
install_requires["Windows"] = [
    "pyaudio",
    "pyvisa",
    "pyvisa-py",
    "psutil",
    "typing_extensions==4.0.1",
    "python-can==3.3.4",
    "requests==2.26.0",
    "pyserial==3.4",
    "robotframework==6.0",
    "pure-python-adb==0.2.3.dev0",
    "pywin32==304",
    "scikit-image==0.19.1",
    "imutils==0.5.4",
    "opencv-python==4.5.4.60",
    "nidaqmx==0.6.2",
    "robotframework-sshlibrary==3.4.0",
    "pyttsx3==2.7",
    "schedule==1.1.0",
    "jira==3.2.0",
    "xlrd==1.2.0",
    "pymediainfo",
    "pytesseract",
    "matplotlib",
]
setup(
    name="rfw",
    version="4.7.3",
    cmdclass={"build_ext": build_ext},
    description="Resource library",
    long_description=long_description,
    author="Vashanthkumar PG",
    author_email="Vashanth.KumarPG@in.bosch.com",
    license="For Bosch-internal use only",
    install_requires=install_requires[platform.system()],
    # test_requires=[],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Framework :: Pytest",
    ],
    keywords="bosch setuptools",
    zip_safe=True,
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    # Below example adds few dummy binaries.
    package_data={
        "rfw": [
        "lib/*.pyd",
        "lib/*/*.pyd",
        "lib/*/*/*.pyd",
        "gm/*.*",
        ],
    },
)
