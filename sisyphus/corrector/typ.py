from dataclasses import field
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import validator
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
class Materia:
    """Clase que representa la configuración de una materia.
    """

    name: str
    entregas: Dict[str, Entrega]
    checks: Dict[str, Check] = field(default_factory=dict)

    @validator("checks", pre=True)
    def checkrun_names(cls, checks):
        """Si un check no incluye nombre, se le da uno por omisión.
        """
        for key, check in checks.items():
            check.setdefault("name", f"Pruebas {key}")
        return checks

    @validator("entregas", pre=True)
    def entrega_defaults(cls, entregas):
        """Se usa el nombre de la entrega como default para rama y alu_dir.

        Si no se especifica ningún check, se creará uno default.
        """
        if isinstance(entregas, list):
            # Por conveniencia, permitimos que las entregas sean una lista
            # si todas tienen los atributos default.
            entregas = {e: {} for e in entregas}
        for entrega, attrs in entregas.items():
            attrs["name"] = entrega
            attrs.setdefault("branch", entrega)
            attrs.setdefault("alu_dir", entrega)
            attrs.setdefault("checks", [entrega])
        return entregas

    def __post_init_post_parse__(self):
        """Rellena checks faltantes con un check default.
        """
        for entrega in self.entregas.values():
            for check in entrega.checks:
                if check not in self.checks:
                    self.checks[check] = Check(name=f"Pruebas {check}")
