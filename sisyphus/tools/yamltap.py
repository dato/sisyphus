#!/usr/bin/env python3

"""Testea un programa con pruebas basadas en entrada/salida.

Las pruebas se especifican en formato YAML, la salida se reporta
en formato TAP (Test Anything Protocol).

También puede generar archivos NN.test/NN_{in,out,err} compatibles
con el script pruebas.sh.
"""

import argparse
import collections
import enum
import subprocess
import sys
import textwrap

import yaml


class Result(enum.Enum):
    OK = enum.auto()
    FAIL = enum.auto()
    # TODO: SKIP, WARN


Test = collections.namedtuple("Test", "name, args, stdin, stdout, stderr, retcode")


# Soporte para !include en YAML. Versión simplificada de:
# https://gist.github.com/joshbode/569627ced3076931b02f
# (siempre leemos el archivo como cadena, no YAML recursivo).


class IncludeLoader(yaml.SafeLoader):
    pass


def yaml_include(loader: IncludeLoader, node: yaml.Node) -> str:
    with open(loader.construct_scalar(node)) as f:
        return f.read()


yaml.add_constructor("!include", yaml_include, IncludeLoader)

##
## La primera parte del archivo genera archivos compatibles con pruebas.sh.
##


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
            tests = parse["tests"]
    except IOError as ex:
        print(f"no se pudo abrir {args.tests!r}: {ex}", file=sys.stderr)
        return 2
    except KeyError:
        print(f"no se pudo encontraron tests en {args.tests}", file=sys.stderr)
        return 2

    if args.gen_only:
        gen_tests(tests)
    else:
        return run_tests(tests, args.program)


def gen_tests(tests):
    """Genera archivos .test, _in, _out y _err a partir de YAML.
    """
    for num, test in enumerate(tests, 1):
        num = f"{num:02}"
        test = make_test(test)
        files = [".test", "_in", "_out", "_err"]
        filedata = [test.name, test.stdin or "", test.stdout, test.stderr]

        for fname, data in zip(files, filedata):
            with open(f"{num}{fname}", "w") as f:
                f.write(data)


def make_test(test_info, test_number=None):
    """Construye un objeto Test desde un diccionario.

    Args:
      test_info: un diccionario obtenido del archivo YAML.
      number_test (opcional): número con que prefijar el nombre.

    Returns:
      a Test object.

    Los posibles elementos de test_info son:

      - name: nombre del test (required)
      - args: argumentos al programa (default: [])
      - stdin: entrada para el programa (default: /dev/null)
      - stdout, stderr: salidas esperadas (estándar y de error; default: "")
      - retcode: valor de salida esperado (default: 0)
    """
    name = test_info["name"]

    if test_number is not None:
        name = f"{test_number:02}: {name}"

    return Test(
        name,
        test_info.get("args", []),
        test_info.get("stdin", None),
        test_info.get("stdout", ""),
        test_info.get("stderr", ""),
        test_info.get("retcode", 0),
    )


##
## La segunda parte (no completa todavía) corre los tests y reporta diferencias.
##


def run_test(test, program):
    """Corre un test y reporta las diferencias encontradas.

    Returns:
      una tupla (result, report_dict).
    """
    proc = subprocess.run(
        [program] + test.args,
        text=True,
        input=test.stdin,
        stdin=None if test.stdin is not None else subprocess.DEVNULL,
        capture_output=True,
        errors="backslashreplace",
    )
    report = {}

    if proc.returncode != test.retcode:
        report["retcode"] = f"retcode={proc.returncode}, se esperaba {test.retcode}"

    # TODO: diff de stderr
    # TODO: diff línea a línea, como en csvdiff.py

    if proc.stdout != test.stdout:
        report["stdout"] = f"stdout={proc.stdout}, se esperaba {test.stdout}"

    return (Result.FAIL if report else Result.OK, report)


def run_tests(tests, program):
    """
    """
    print("TAP version 13")
    print(f"1..{len(tests)}")

    for num, test in enumerate(tests, 1):
        test = make_test(test)
        result, report = run_test(test, program)
        if result == Result.OK:
            print(f"ok {num} {test.name}")
        elif result == Result.FAIL:
            message = f"not ok {num} {test.name}\n"
            if report:
                message += textwrap.indent(
                    yaml.dump(report, explicit_start=True, explicit_end=True), "  "
                )
            print(message, end="")


if __name__ == "__main__":
    sys.exit(main())
