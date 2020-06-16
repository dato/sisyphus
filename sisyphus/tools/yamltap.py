#!/usr/bin/env python3

"""Testea un programa con pruebas basadas en entrada/salida.

Las pruebas se especifican en formato YAML, la salida se reporta
en formato TAP (Test Anything Protocol).

También puede generar archivos NN.test/NN_{in,out,err} compatibles
con el script pruebas.sh.
"""

import argparse
import enum
import subprocess
import os
import re
import sys
import textwrap

from typing import Dict, List, Optional

import yaml

from pydantic import BaseModel, Field, ValidationError


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
    program: Optional[str]
    args: List[str] = []  # TODO: use pydantic.Field.
    stdin: Optional[str]
    # Expected return code
    retcode: int = 0
    # These, if present, must match in the specified match policy.
    stdout: Optional[str]
    stderr: Optional[str]
    stdout_policy: Match = Match.LITERAL
    stderr_policy: Match = Match.LITERAL
    # Environment variables (added to the existing environment, or replacing it)
    env: Optional[Dict[str, str]]
    env_policy: Env = Env.EXTEND

    class Config:
        extra = "forbid"
        validate_all = True


# Soporte para !include en YAML. Versión simplificada de:
# https://gist.github.com/joshbode/569627ced3076931b02f
# (siempre leemos el archivo como cadena, no YAML recursivo).


class IncludeLoader(yaml.SafeLoader):
    pass


def yaml_include(loader: IncludeLoader, node: yaml.Node) -> str:
    with open(loader.construct_scalar(node)) as f:
        return f.read()


yaml.add_constructor("!include", yaml_include, IncludeLoader)


def parse_args():
    """Parser para los argumentos del programa.

    Comúnmente, recibe el archivo con las definiciones de los tests, y el
    programa a correr.

    La opción --gen-only fuerza la generación de archivos para pruebas.sh.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("tests", metavar="<tests.yml>")
    parser.add_argument("program", metavar="<binary>")
    parser.add_argument(
        "--plan-offset",
        type=int,
        default=0,
        help="""Empezar numeración de tests con un offset. Si se especifica,
             no se imprime la versión de TAP, y el plan se imprime al final,
             teniendo en cuenta el offset.""",
    )
    parser.add_argument(
        "--gen-only",
        action="store_true",
        help="Solamente generar archivos para pruebas.sh",
    )
    return parser.parse_args()


def main():
    """Función principal del script.
    """
    args = parse_args()
    try:
        with open(args.tests) as ymlfile:
            parse = yaml.load(ymlfile, IncludeLoader)
            tests = [make_test(test_info, args.program) for test_info in parse["tests"]]
    except IOError as ex:
        print(f"no se pudo abrir {args.tests!r}: {ex}", file=sys.stderr)
        return 2
    except KeyError:
        print(f"no se pudo encontraron tests en {args.tests}", file=sys.stderr)
        return 2
    except ValidationError as ex:
        print(f"YAML no válido: {ex}", file=sys.stderr)
        return 2

    if args.gen_only:
        # TODO: use args.plan_offset here?
        gen_tests(tests)
    else:
        return run_tests(tests, offset=args.plan_offset)


def gen_tests(tests):
    """Genera archivos .test, _in, _out y _err a partir de YAML.
    """
    for num, test in enumerate(tests, 1):
        num = f"{num:02}"
        files = [".test", "_in", "_out", "_err"]
        filedata = [test.name, test.stdin or "", test.stdout, test.stderr]

        for fname, data in zip(files, filedata):
            with open(f"{num}{fname}", "w") as f:
                f.write(data)


def make_test(test_info, program: str = None, test_number: int = None):
    """Construye un objeto Test desde un diccionario.

    Args:
      test_info: un diccionario obtenido del archivo YAML.
      program (opcional): default program si test_info no lo especifica.
      number_test (opcional): número con que prefijar el nombre.

    Returns:
      a Test object.
    """
    test_info.setdefault("program", program)
    test = Test.parse_obj(test_info)

    if test_number is not None:
        test.name = f"{test_number:02}: {test.name}"

    return test


def run_test(test):
    """Corre un test y reporta las diferencias encontradas.

    Returns:
      una tupla (result, report_dict).
    """
    proc_env = None
    proc_stdin = None if test.stdin is not None else subprocess.DEVNULL

    if test.env is not None:
        if test.env_policy == Env.REPLACE:
            proc_env = test.env
        else:
            assert test.env_policy == Env.EXTEND
            proc_env = os.environ.copy()
            proc_env.update(test.env)

    proc = subprocess.run(
        [test.program] + test.args,
        env=proc_env,
        text=True,
        input=test.stdin,
        stdin=proc_stdin,
        capture_output=True,
        errors="backslashreplace",
    )
    report = {}

    if proc.returncode != test.retcode:
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
