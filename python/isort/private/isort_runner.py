"""The process wrapper for isort aspects."""

import argparse
import configparser
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Sequence

from python.runfiles import Runfiles


def _rlocation(runfiles: Runfiles, rlocationpath: str) -> Path:
    """Look up a runfile and ensure the file exists

    Args:
        runfiles: The runfiles object
        rlocationpath: The runfile key

    Returns:
        The requested runifle.
    """
    runfile = runfiles.Rlocation(rlocationpath, source_repo=os.getenv("TEST_WORKSPACE"))
    if not runfile:
        raise FileNotFoundError(f"Failed to find runfile: {rlocationpath}")
    path = Path(runfile)
    if not path.exists():
        raise FileNotFoundError(f"Runfile does not exist: ({rlocationpath}) {path}")
    return path


def _maybe_runfile(arg: str) -> Path:
    """Parse an argument into a path while resolving runfiles.

    Not all contexts this script runs in will use runfiles. In
    these cases the functon is a noop.
    """
    if "BAZEL_TEST" not in os.environ:
        return Path(arg)

    runfiles = Runfiles.Create()
    if not runfiles:
        raise EnvironmentError("Failed to locate runfiles")
    return _rlocation(runfiles, arg)


def parse_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse command line arguments

    Returns:
        A struct of parsed arguments.
    """
    parser = argparse.ArgumentParser("isort process wrapper")

    parser.add_argument(
        "--marker",
        type=Path,
        help="The file to create as an indication that the 'PyISortFormatCheck' action succeeded.",
    )
    parser.add_argument(
        "--src",
        dest="sources",
        action="append",
        type=_maybe_runfile,
        required=True,
        help="The source file to perform formatting on.",
    )
    parser.add_argument(
        "--import",
        dest="imports",
        action="append",
        default=[],
        type=Path,
        help="Import paths for first party directories.",
    )
    parser.add_argument(
        "--settings-path",
        type=_maybe_runfile,
        required=True,
        help="The path to an isort config file.",
    )
    parser.add_argument(
        "isort_args",
        nargs="*",
        help="Remaining arguments to forward to isort.",
    )

    return parser.parse_args(args)


def locate_first_party_src_paths(imports: Sequence[str]) -> List[str]:
    """Determine the list of first party packages.

    Args:
        imports: The runfiles import paths.

    Returns:
        The names of top level modules in the given root.
    """

    # Determined by rules_venv
    if "PY_VENV_RUNFILES_DIR" in os.environ:
        runfiles_dir = Path(os.environ["PY_VENV_RUNFILES_DIR"])
    elif "RUNFILES_DIR" in os.environ:
        runfiles_dir = Path(os.environ["RUNFILES_DIR"])
    else:
        raise EnvironmentError("Unable to locate runfiles directory.")

    return [str(runfiles_dir / path) for path in imports]


def generate_config_with_projects(
    existing: Path, output: Path, src_paths: List[str]
) -> None:
    """Write a new config file with first party imports merged into it.

    Args:
        existing: The location of an existing config file
        output: The output location for the new config file.
        src_paths: A list of directories to consider source paths
    """
    cfg_pairs = [
        (".isort.cfg", "settings"),
        (".cfg", "isort"),
        (".ini", "isort"),
        ("pyproject.toml", "tool.isort"),
    ]
    for suffix, section in cfg_pairs:
        if not existing.name.endswith(suffix):
            continue

        if suffix.endswith(".toml"):
            raise NotImplementedError("There is no writer for tomllib")

        config = configparser.ConfigParser()
        config.read(str(existing))

        if section not in config.sections():
            config.add_section(section)

        known_src_paths = config.get(section, "src_paths", fallback="")

        config.set(
            section,
            "src_paths",
            ",".join(
                pkg
                for pkg in sorted(set(src_paths + known_src_paths.split(",")))
                if pkg
            ),
        )

        with output.open("w", encoding="utf-8") as fhd:
            config.write(fhd)

        return

    raise ValueError(f"Unexpected isort config file '{existing}'.")


def main() -> None:
    """The main entrypoint."""
    if "BAZEL_TEST" in os.environ and "PY_ISORT_RUNNER_ARGS_FILE" in os.environ:
        runfiles = Runfiles.Create()
        if not runfiles:
            raise EnvironmentError("Failed to locate runfiles")
        arg_file = _rlocation(runfiles, os.environ["PY_ISORT_RUNNER_ARGS_FILE"])
        args = parse_args(arg_file.read_text(encoding="utf-8").splitlines())
    else:
        args = parse_args()

    environ = dict(os.environ)
    environ["PY_ISORT_MAIN"] = __file__

    imports = locate_first_party_src_paths(args.imports)

    temp_dir = tempfile.mkdtemp(
        prefix="bazel_rules_isort-", dir=os.getenv("TEST_TMPDIR")
    )
    try:
        isort_args = [
            sys.executable,
            __file__,
        ]

        settings_path = Path(temp_dir) / args.settings_path.name
        generate_config_with_projects(args.settings_path, settings_path, imports)

        isort_args.extend(["--settings-path", str(settings_path)])
        isort_args.extend(args.isort_args)
        isort_args.extend([str(src) for src in args.sources])

        # Run isort on all requested sources
        result = subprocess.run(
            isort_args,
            check=False,
            encoding="utf-8",
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            env=environ,
        )
    finally:
        # Only cleanup the temp dir when running outside of a test.
        if "TEST_TMPDIR" not in os.environ:
            shutil.rmtree(temp_dir)

    if result.returncode:
        # Sanitize error messages
        output = result.stdout
        if "RUNFILES_DIR" in os.environ:
            output = output.replace(os.environ["RUNFILES_DIR"], "//")
        output = output.replace(str(Path.cwd()), "/")

        print(output, file=sys.stderr)

        sys.exit(result.returncode)

    # Satisfy the action by writing a consistent output file.
    if args.marker:
        args.marker.write_bytes(b"")


def _no_realpath(path, **_kwargs):  # type: ignore
    """Redirect realpath, with any keyword args, to abspath."""
    return os.path.abspath(path)


if __name__ == "__main__":
    # Conditionally run the `isort` entrypoint from the `isort` package. This
    # environment variable is set above and acts as the toggle for running the
    # underlying tool this script is wrapping. This is done because running
    # python entrypoints can be expensive (in environments that don't support
    # runfiles/symlinks) and complicated (needing to deal with a regenerated
    # PYTHONPATH variable). If this variable is set and matches an expected
    # value then it's assumed this script is running as an subprocess and we
    # want to instead run a different entrypoint.
    if os.getenv("PY_ISORT_MAIN") == __file__:
        os.path.realpath = _no_realpath  # type: ignore

        # isort gets confused seeing itself in a file, explicitly skip sorting this
        # isort: off
        from isort.main import main as isort_main

        isort_main()
    else:
        main()
