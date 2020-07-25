#!/usr/bin/env python3

"""Testea un programa con pruebas basadas en entrada/salida.

Las pruebas se especifican en formato YAML, la salida se reporta
en formato TAP (Test Anything Protocol).
"""

import argparse
import enum
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import textwrap

from typing import Dict, List, Optional

import yaml

from pydantic import BaseModel, Field, ValidationError

from ..common.yaml import IncludeLoader


class Env(str, enum.Enum):
    EXTEND = "extend"
    REPLACE = "replace"


class Match(str, enum.Enum):
    LITERAL = "literal"
    MULTI_REGEX = "regex"
    SINGLE_REGEX = "multiline_regex"


class Result(enum.Enum):
    OK = enum.auto()
    FAIL = enum.auto()
    # TODO: SKIP, WARN


class Test(BaseModel):
    name: str
    program: str
    args: List[str] = []  # TODO: use pydantic.Field.
    stdin: Optional[str]
    # Expected return code (specify -1 for non-zero)
    retcode: int = 0
    # These, if present, must match in the specified match policy.
    stdout: Optional[str]
    stderr: Optional[str]
    stdout_policy: Match = Match.LITERAL
    stderr_policy: Match = Match.LITERAL
    # Environment variables (added to the existing environment, or replacing it)
    env: Optional[Dict[str, str]]
    env_policy: Env = Env.EXTEND
    # Support for creating and verifying files.
    files_in: Dict[str, bytes] = Field(default_factory=dict)
    files_out: Dict[str, bytes] = Field(default_factory=dict)

    class Config:
        extra = "forbid"
        validate_all = True


class Defaults(BaseModel):
    program: Optional[str]
    args: Optional[List[str]]
    env_policy: Optional[Env]
    stdout: Optional[str]
    stderr: Optional[str]
    stdout_policy: Optional[Match]
    stderr_policy: Optional[Match]
    files_in: Optional[Dict[str, bytes]]

    class Config:
        extra = "forbid"
        validate_all = True


def parse_args():
    """Parser para los argumentos del programa.

    Comúnmente, recibe el archivo con las definiciones de los tests, y el
    programa a correr.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("tests", metavar="<tests.yml>")
    parser.add_argument("program", metavar="<binary>", nargs="?")
    parser.add_argument(
        "--plan-offset",
        type=int,
        default=0,
        help="""Empezar numeración de tests con un offset. Si se especifica,
             no se imprime la versión de TAP, y el plan se imprime al final,
             teniendo en cuenta el offset.""",
    )
    return parser.parse_args()


def main():
    """Función principal del script.
    """
    args = parse_args()
    try:
        with open(args.tests) as ymlfile:
            parse = yaml.load(ymlfile, IncludeLoader)
            tests_in = parse["tests"]
            defaults = parse.get("defaults", {})
    except (IOError, yaml.YAMLError) as ex:
        print(f"error al procesar {args.tests!r}: {ex}", file=sys.stderr)
        return 2
    except KeyError:
        print(f"no se pudo encontraron tests en {args.tests}", file=sys.stderr)
        return 2

    if args.program is not None:
        defaults["program"] = args.program

    try:
        Defaults.parse_obj(defaults)  # Ensure they're OK.
        tests = [make_test(test_info, defaults) for test_info in tests_in]
    except ValidationError as ex:
        print(f"YAML no válido: {ex}", file=sys.stderr)
        return 2

    return run_tests(tests, offset=args.plan_offset)


def make_test(test_info, defaults=None, test_number: int = None):
    """Construye un objeto Test desde un diccionario.

    Args:
      test_info: un diccionario obtenido del archivo YAML.
      program (opcional): default program si test_info no lo especifica.
      number_test (opcional): número con que prefijar el nombre.

    Returns:
      a Test object.
    """
    if defaults is not None:
        # Python 3.9:
        # test_info = defaults | test_info
        test_info.update((k, v) for k, v in defaults.items() if k not in test_info)

    test = Test.parse_obj(test_info)

    if test_number is not None:
        test.name = f"{test_number:02}: {test.name}"

    return test


def run_test(test):
    """Corre un test y reporta las diferencias encontradas.

    Returns:
      una tupla (result, report_dict).
    """
    report = {}
    proc_env = None
    proc_stdin = None if test.stdin is not None else subprocess.DEVNULL
    program = pathlib.Path(test.program)

    if test.env is not None:
        if test.env_policy == Env.REPLACE:
            proc_env = test.env
        else:
            assert test.env_policy == Env.EXTEND
            proc_env = os.environ.copy()
            proc_env.update(test.env)

    with tempfile.TemporaryDirectory(prefix=program.name) as tmpdir:
        tmpdir = pathlib.Path(tmpdir)

        for filename, contents in test.files_in.items():
            with open(tmpdir / filename, "wb") as fileobj:
                fileobj.write(contents)

        # XXX fisop shell
        if proc_env is None:
            proc_env = os.environ.copy()

        proc_env["HOME"] = tmpdir

        proc = subprocess.run(
            [program.resolve()] + test.args,
            env=proc_env,
            cwd=tmpdir,
            text=True,
            input=test.stdin,
            stdin=proc_stdin,
            capture_output=True,
            errors="backslashreplace",
        )

        for filename, expected_contents in test.files_out.items():
            actual = open(tmpdir / filename, "rb").read()
            if result := report_diff(expected_contents, actual, Match.LITERAL):
                report[f"file<{filename}>"] = result

    if (
        test.retcode == -1
        and proc.returncode == 0
        or test.retcode != -1
        and proc.returncode != test.retcode
    ):
        report["retcode"] = f"retcode={proc.returncode}, se esperaba {test.retcode}"

    # TODO: diff línea a línea, como en csvdiff.py

    if test.stdout is not None:
        if result := report_diff(test.stdout, proc.stdout, test.stdout_policy):
            report["stdout"] = result

    if test.stderr is not None:
        if result := report_diff(test.stderr, proc.stderr, test.stderr_policy):
            report["stderr"] = result

    return (Result.FAIL if report else Result.OK, report)


def run_tests(tests, *, offset=0):
    """
    """
    if offset == 0:
        print("TAP version 13")
        print(f"1..{len(tests)}")

    for num, test in enumerate(tests, offset + 1):
        result, report = run_test(test)
        if result == Result.OK:
            print(f"ok {num} {test.name}")
        elif result == Result.FAIL:
            message = f"not ok {num} {test.name}\n"
            if report:
                message += textwrap.indent(
                    yaml.dump(report, explicit_start=True, explicit_end=True), "  "
                )
            print(message, end="")

    if offset > 0:
        print(f"1..{len(tests) + offset}")


def report_diff(expected: str, actual: str, policy: Match):
    if policy == Match.LITERAL:
        if expected != actual:
            # TODO: better reporting
            return f"{actual}, se esperaba {expected}"

    if policy == Match.SINGLE_REGEX:
        regex = re.compile(expected, re.M)
        if not regex.search(actual):
            return f"{actual}\nno contiene regex\n{regex.pattern}"


if __name__ == "__main__":
    sys.exit(main())
