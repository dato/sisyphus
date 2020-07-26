"""Pseudo-DB con la lista de repositorios conocidos para una materia."""

from google.oauth2.service_account import Credentials

from ..common.sheets import Config
from ..repos.planilla import RepoDB
from .settings import Materia


__all__ = [
    "make_repodb",
]


def make_repodb(materia: Materia) -> RepoDB:
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
    return RepoDB(config)
