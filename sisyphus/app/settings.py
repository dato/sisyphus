import functools
import os

from typing import Dict, List

import yaml

from pydantic import BaseModel, BaseSettings, SecretStr

from ..common.yaml import IncludeLoader


class Materia(BaseModel):
    branches: List[str]


class ReposApp(BaseSettings):
    app_id: int
    key_path: str
    endpoint: str
    webhook_secret: SecretStr

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
    materias: Dict[str, Materia]
    repos_app: ReposApp


@functools.lru_cache
def load_config():
    """Carga la configuración de un archivo YAML.

    Returns:
       un objeto de tipo Settings, validado.
    """
    conffile = os.environ.get("SISYPHUS_CONF", "sisyphus.yaml")
    with open(conffile) as yml:
        conf_dict = yaml.load(yml, IncludeLoader)
        return Settings(**conf_dict)
