"""Este módulo convierte un resultado en formato TAP a un check_run de Github.
"""

import collections
import re
import textwrap

from typing import List

import tap.parser  # type: ignore


Counts = collections.namedtuple("Summary", "ok, fail, warn, skip, expected_ok")
WARN_RE = re.compile(r"^\[warn\]\s*")


def tap_to_markdown(tap_results: str):
    """Convierte de formato TAP a Markdown para Github.

    Returns:
      una tupla (Counts, str) donde el segundo elemento es texto Markdown
      con un resumen de los resultados (a colocar en check_run.output.text).
    """
    # Parse TAP results.
    plan = None
    lines = []
    parser = tap.parser.Parser()
    ok_num = 0
    fail_num = 0
    skip_num = 0
    warn_num = 0

    for test in parser.parse_text(tap_results):
        if test.category == "plan":
            plan = test
        if test.category != "test":
            continue
        if WARN_RE.search(test.description):
            suffix = " :warning:"
            warn_num += 1
        elif test.skip:
            suffix = ""
            skip_num += 1
        elif test.ok:
            suffix = " :heavy_check_mark:"
            ok_num += 1
        else:
            suffix = " :x:"
            fail_num += 1

        description = WARN_RE.sub("", test.description)
        lines.append(f"- {description}{suffix}")

        yaml_lines = []
        yaml_block = test.yaml_block or {}

        for item, data in yaml_block.items():
            if data.count("\n") > 1:
                if item.startswith("_"):
                    yaml_lines.append(f"```\n{data}\n```")
                else:
                    yaml_lines.append(f"- {item}")
                    yaml_lines.append(indent2(f"```\n{data}\n```\n"))
            else:
                yaml_lines.append(f"- {item}: {data}" if item[0] != "_" else f"{data}")

        lines.append(indentjoin((yaml_lines)))
        lines.append("")

    if plan:
        expected_ok = plan.expected_tests - skip_num
    else:
        expected_ok = ok_num + fail_num

    counts = Counts(ok_num, fail_num, warn_num, skip_num, expected_ok)

    return (counts, "\n".join(lines))


def checkrun_output(tap_results):
    """Convierte de formato TAP a CheckRun de Github.

    Returns:
      una tupla (conclusion, dict) donde el segundo elemento se puede serializar
      en JSON para enviar a como check_run.output (con títulos y summary elegidos).
    """
    counts, text = tap_to_markdown(tap_results)
    summary = ""

    if counts.ok == 0:
        title = "No compila"
        conclusion = "failure"
    elif counts.fail > 0:
        title = f"ERROR (failing: {counts.fail})"
        conclusion = "failure"
    elif counts.warn > 0:
        title = f"Pruebas OK (warnings: {counts.warn})"
        conclusion = "neutral"
    elif counts.skip > 0:
        title = f"Pruebas OK ({counts.skip} skipped)"
        conclusion = "success"
    else:
        title = "Pruebas OK"
        conclusion = "success"

    return conclusion, dict(title=title, summary=summary, text=text)


def indent2(s: str) -> str:
    """Indents a string by two spaces."""
    return textwrap.indent(s, "  ")


def indentjoin(lines: List[str], level="  ") -> str:
    """Indents a list of strings, joining them first."""
    return textwrap.indent("\n".join(lines), level)
