"""rules_isort dependencies"""

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("@bazel_tools//tools/build_defs/repo:utils.bzl", "maybe")

# buildifier: disable=unnamed-macro
def rules_isort_dependencies():
    """Defines isort dependencies"""
    maybe(
        http_archive,
        name = "rules_venv",
        integrity = "sha256-9XskSxoCowVITC99PqumMKisgX/GRYHrX3qyciI7LgU=",
        urls = ["https://github.com/periareon/rules_venv/releases/download/0.0.2/rules_venv-0.0.2.tar.gz"],
    )

# buildifier: disable=unnamed-macro
def isort_register_toolchains(register_toolchains = True):
    """Defines pytest dependencies"""
    if register_toolchains:
        native.register_toolchains(
            str(Label("//python/isort/toolchain")),
        )
