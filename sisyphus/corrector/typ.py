from pathlib import Path
from typing import List, Optional

from pydantic.dataclasses import dataclass


@dataclass
class Check:
    """Clase que representa una corrección (un check run).

    Args:
      • name: nombre visible en Github, por ejemplo "Pruebas datalab"
      • alu_files: lista de archivos a corregir, por ejemplo ["bits.c"]. (Si
            no se especifica, se usan todos los archivos en Entrega.alu_dir.)
      • test_files: ídem, con los archivos que componen los tests.
    """

    name: str
    alu_files: Optional[List[Path]] = None
    test_files: Optional[List[Path]] = None


@dataclass
class Entrega:
    """Clase que representa una entrega (rama y subdirectorio).

    Args:
      • branch: rama en la que estará la entrega.
      • alu_dir: subdirectorio en donde se encuentran los archivos de la entrega.
      • checks: lista de correcciones a realizar (normalmente solo uan).
      • modalidad: si la entrega es grupal, o individual.
    """

    name: str
    branch: str
    alu_dir: str
    checks: List[str]


@dataclass
class Corrector:
    """
    """

    formatter: str
    tests_path: Path
    worker_path: Path
