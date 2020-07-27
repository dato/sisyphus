import functools
import os

from typing import Dict

import yaml

from pydantic import BaseSettings, Field, SecretStr, root_validator, validator

from ..common.yaml import IncludeLoader
from ..corrector.typ import Check, Entrega


class ReposApp(BaseSettings):
    app_id: int
    key_path: str
    endpoint: str
    sheets_auth: str
    spreadsheet_id: str
    webhook_secret: SecretStr
    job_queue: str = "default"

    class Config:
        env_prefix = "REPOS_"

    def flask_config(self):
        return dict(
            GITHUBAPP_ID=self.app_id,
            GITHUBAPP_ROUTE=self.endpoint,
            GITHUBAPP_SECRET=self.webhook_secret.get_secret_value(),
            GITHUBAPP_KEY=open(self.key_path, "rb").read(),
        )


class Settings(BaseSettings):
    entregas: Dict[str, Entrega]
    repos_app: ReposApp

    checks: Dict[str, Check] = Field(default_factory=dict)

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

    @root_validator
    def default_checkruns(cls, fields):
        """Rellena checks faltantes con un check default.
        """
        entregas = fields.get("entregas")
        checks = fields.setdefault("checks", {})
        for entrega in entregas.values():
            for check in entrega.checks:
                if check not in checks:
                    checks[check] = Check(name=f"Pruebas {check}")
        return fields


@functools.lru_cache
def load_config():
    """Carga la configuración de un archivo YAML.

    Returns:
       un objeto de tipo Settings, validado.
    """
    conffile = os.environ.get("SISYPHUS_CONF", "sisyphus.yaml")
    with open(conffile) as yml:
        conf = yaml.load(yml, IncludeLoader)
        return Settings(**conf)
