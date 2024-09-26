"""Show that imports are not considered first party despite duplicate package names

This repo has a root level package called `python` but that package does not have a
`py_dep` package in it. This comes from a different dependency that uses
`imports = ["."]`. As a result, it should be grouped with 3rdparty packages
"""

import os

# pylint: disable-next=no-name-in-module
from python.within_second_python.py_dep import print_greeting  # type: ignore
from tomlkit import __name__ as toml_name


def print_data() -> None:
    """Print a greeting"""
    print_greeting("Guten Tag!")
    print(os.curdir)
    print(toml_name)
