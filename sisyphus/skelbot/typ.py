from dataclasses import field
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel
from pydantic.dataclasses import dataclass


@dataclass
class Skeldir:
    """Clase que representa un directorio en el repositorio esqueleto.

    Args:
      • files: lista de archivos a importar (relativos a srcdir, si se especifica).
               Se interpretan como globs (as in Path.blob, con soporte para ‘**’).
      • target: directorio a crear en el repositorio destino.
      • srcdir: si se especifica, los archivos son relativos a este este directorio.
                Además, de estar presente, los archivos preservan la estructura de
                subdirectorios con respecto a srcdir.
      • extra_files: lista de archivos/globs adicionales desde el directorio raíz (se
                     guardan únicamente bajo el nombre; no preservan estructura).
    """

    # TODO: support specifying revisions.
    files: List[str]
    target: Path
    srcdir: Optional[Path] = None
    extra_files: List[Path] = field(default_factory=list)


class Settings(BaseModel):
    """Configuración para skelbot.
    """

    skeldirs: List[Skeldir]
