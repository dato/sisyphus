from typing import ClassVar, List, Optional

from ..common import sheets
from ..common.models import Model, parse_rows


__all__ = [
    "RepoSheet",
    "ReposDB",
]


class RepoRow(Model):
    repo: str
    legajo: str
    grupo: Optional[str]
    github: Optional[str]
    repo_grupal: Optional[str]  # XXX Should be a dict

    COLUMNAS: ClassVar = ("Repo", "Legajo", "Grupo", "Github", "Repo2")

    class Config:
        arbitrary_types_allowed = True


class RepoSheet(sheets.PullDB):
    """Mixin para sheets.PullDB para parsear la hoja de repositorios.
    """

    def parse_sheets(self, sheet_dict):
        """Parsea una hoja de repositorios.

        Pre-condición: se recibe exactamente _una_ hoja.
        Post-condición: self.data es un diccionario {full_name: RepoRow}
        """
        assert len(sheet_dict) == 1
        sheets = set(sheet_dict)

        data = sheet_dict[sheets.pop()]
        repo_rows = parse_rows(data, RepoRow)
        repos = {r.repo: r for r in repo_rows}
        repos.update((r.repo_grupal, r) for r in repo_rows if r.repo_grupal)

        return repos


class ReposDB:
    """Representación unificada de hojas "Repos" de varias planillas.

    Las hojas que se descargan y procesan son las del enum Hojas, arriba.
    """

    def __init__(self, sheets: List[RepoSheet]):
        self.sheets = sheets

    def is_repo_known(self, /, repo_full: str):
        """Devuelve verdadero si el repositorio existe en alguna materia.
        """
        return any(repo_full in sheet.data for sheet in self.sheets)
