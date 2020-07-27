"""Pseudo-DB con la lista de repositorios conocidos."""

from google.oauth2.service_account import Credentials  # type: ignore

from ..common.sheets import Config
from ..repos.planilla import ReposDB
from .settings import load_config


__all__ = [
    "make_reposdb",
]


def make_reposdb() -> ReposDB:
    """
    """
    settings = load_config()
    repos_app = settings.repos_app
    credentials = Credentials.from_service_account_file(
        repos_app.sheets_auth,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    config = Config(
        spreadsheet_id=repos_app.spreadsheet_id,
        credentials=credentials,
        sheet_list=["Repos"],
    )
    return ReposDB(config)
