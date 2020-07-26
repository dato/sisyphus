"""Pseudo-DB con la lista de repositorios conocidos para una materia."""

from google.oauth2.service_account import Credentials  # type: ignore

from ..common.sheets import Config
from ..repos.planilla import RepoDB
from .settings import Materia, load_config


__all__ = [
    "make_repodb",
]


def make_repodb(materia: Materia) -> RepoDB:
    """
    """
    settings = load_config()
    credentials = Credentials.from_service_account_file(
        settings.sheets_auth,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    config = Config(
        spreadsheet_id=materia.spreadsheet_id,
        credentials=credentials,
        sheet_list=["Repos"],
    )
    return RepoDB(config)
