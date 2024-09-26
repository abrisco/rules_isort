"""Demonstrate mixing first party modules from another package

We should see `library` imports shown as 3rdparty due to the use
of `imports` from `//python/isort/private/imports/deps:library`.
Though, we can still import the same library using repo relative
paths and see it as
"""

import os

import library.first_party_2  # type: ignore

import python.isort.private.tests.imports.deps.library.first_party_3


def example() -> None:
    """Call some code"""
    print(os.curdir)

    library.first_party_2.greeting()

    python.isort.private.tests.imports.deps.library.first_party_3.goodbye()
