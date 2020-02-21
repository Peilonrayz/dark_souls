#!/usr/bin/env python
from setuptools import find_packages, setup

try:
    import ConfigParser as configparser
except ImportError:
    import configparser

with open("README.rst") as f:
    LONG_DESCRIPTION = f.read()

config = configparser.ConfigParser()
config.read("setup.cfg")

setup(
    name="dark_souls",
    version=config.get("src", "version"),
    license="MIT",
    description="Min max Dark Souls 3 builds",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/x-rst",
    author="Peilonrayz",
    author_email="peilonrayz@gmail.com",
    url="https://peilonrayz.github.io/dark_souls",
    project_urls={
        "Bug Tracker": "https://github.com/Peilonrayz/dark_souls/issues",
        "Documentation": "https://peilonrayz.github.io/dark_souls",
        "Source Code": "https://github.com/Peilonrayz/dark_souls",
    },
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    install_requires=["requests", "matplotlib"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="",
    entry_points={"console_scripts": ["dark_souls=dark_souls.__main__:main"]},
)
