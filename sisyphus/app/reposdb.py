"""Pseudo-DB con la lista de repositorios conocidos."""

from google.oauth2.service_account import Credentials

from ..common.sheets import Config
from ..repos.planilla import ReposDB, RepoSheet
from .settings import Materia, load_config


__all__ = [
    "make_reposdb",
]


def make_reposdb() -> ReposDB:
    """
    """
    settings = load_config()
    return ReposDB([make_sheet(mat) for mat in settings.materias.values()])


def make_sheet(materia: Materia) -> RepoSheet:
    """
    """
    credentials = Credentials.from_service_account_file(
        materia.service_account_jsonfile,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    config = Config(
        spreadsheet_id=materia.spreadsheet_id,
        credentials=credentials,
        sheet_list=[materia.repos_sheet],
    )
    return RepoSheet(config)
