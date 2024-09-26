"""# rules_isort

## Overview

Rules for the Python formatter [isort][is]

### Setup

To setup the rules for `isort`, define a [py_isort_toolchain](#py_isort_toolchain) within your
project and register it within your workspace. For example say you have the following `BUILD.bazel`
file in the root of your workspace:

```python
load("@rules_isort//python/isort:defs.bzl", "py_isort_toolchain")

package(default_visibility = ["//visibility:public"])

py_isort_toolchain(
    name = "py_isort_toolchain",
    isort = "@pip_deps//:isort",
)

toolchain(
    name = "toolchain",
    toolchain = ":py_isort_toolchain",
    toolchain_type = "@rules_isort//python/isort:toolchain_type",
)
```

You would then add the following to your `WORKSPACE.bazel` file.

```python
register_toolchains("//tools/isort:toolchain")
```


With dependencies loaded in the workspace, python code can be formatted by simply running:
`bazel run @rules_isort//python/isort`.

Note that any python target (`py_library`, `py_binary`, `py_test`, etc) which adds `imports ["."]`
will have all directories within that location considered first party packages.

In addition to this formatter, a check can be added to your build phase using the [py_isort_aspect](#py_isort_aspect)
aspect. Simply add the following to a `.bazelrc` file to enable this check.

```text
build --aspects=@rules_isort//python/isort:defs.bzl%py_isort_aspect
build --output_groups=+py_isort_checks
```

These rules use a global flag to determine the location of the configuration file to use with isort. To wire up a custom
config file, simply add the following to your `.bazelrc` file

```text
build build --@rules_isort//python/isort:config=//:.isort.cfg
```

Note the flag above assumes you have a `.isort.cfg` in the root of your repository.

It's recommended to only enable this aspect in your CI environment so formatting issues do not
impact user's ability to rapidly iterate on changes.


## First/third party packages

First and third party packages are identified using the following rules.

### First party

- Repo relative packages.
- Direct sources (the `srcs` attribute) imported in combination with the `imports` attribute.
E.g. if a Bazel target `//example:py_app` depends on the source `//example:app/foo.py` and
`//example:app/bar.py`, `bar.py` may use `import foo` and have it considered a first party
dependency.

### Third party

- Any source files from a dependency (the `deps` attribute) with the exception
of imports using repo relative paths.

## Tips

Isort is very sensitive to the [`legacy_create_init`][legacy_init] attribute on python rules.
It's recommended to set [`--incompatible_default_to_explicit_init_py`][incompat_init] to avoid
random directories unexpectedly being considered first party packages.

[legacy_init]: https://bazel.build/reference/be/python#py_binary.legacy_create_init
[incompat_init]: https://github.com/bazelbuild/bazel/issues/10076
[is]: https://pycqa.github.io/isort/

## Rules

- [py_isort_aspect](#py_isort_aspect)
- [py_isort_test](#py_isort_test)
- [isort](#isort)

---
---
"""

load(
    "//python/isort/private:isort.bzl",
    _py_isort_aspect = "py_isort_aspect",
    _py_isort_test = "py_isort_test",
)
load(
    "//python/isort/private:isort_toolchain.bzl",
    _py_isort_toolchain = "py_isort_toolchain",
)

py_isort_aspect = _py_isort_aspect
py_isort_test = _py_isort_test
py_isort_toolchain = _py_isort_toolchain
