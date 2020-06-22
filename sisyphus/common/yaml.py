# Soporte para !include en YAML. Versión modificada de:
# https://gist.github.com/joshbode/569627ced3076931b02f

import json
import pathlib

from typing import IO, Any

import yaml


class IncludeLoader(yaml.SafeLoader):
    """YAML Loader with support for `!include`."""

    def __init__(self, stream: IO):
        try:
            source = stream.name
        except AttributeError:
            self._root = pathlib.Path.cwd()
        else:
            self._root = pathlib.Path(source).resolve().parent

        super().__init__(stream)


def yaml_include(loader: IncludeLoader, node: yaml.Node) -> Any:
    filename = loader._root / loader.construct_scalar(node)
    extension = filename.suffix[1:]

    with open(filename) as f:
        if extension in {"yaml", "yml"}:
            return yaml.load(f, IncludeLoader)
        elif extension in {"json"}:
            return json.load(f)
        else:
            return f.read()


yaml.add_constructor("!include", yaml_include, IncludeLoader)
