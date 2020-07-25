import json

from dataclasses import dataclass, field
from typing import Optional

from github.Repository import Repository as PyGithubRepo
from pydantic import BaseModel, SecretStr

from ..corrector.typ import Check, Corrector, Entrega


__all__ = [
    "PyGithubRepo",
    "Repo",
    "RepoFile",
]


@dataclass
class Repo:
    name: str = field(init=False)
    owner: str = field(init=False)
    full_name: str

    def __post_init__(self):
        self.owner, self.name = self.full_name.split("/", 1)


@dataclass
class RepoFile:
    # TODO: add mtime (optional)
    path: str
    contents: bytes
    mode: int = 0o644


class AppInstallationTokenAuth(BaseModel):
    """Authentication data for github3.Session.app_installation_token_auth.
    """

    # Queremos que esta clase use SafeStr para que el token no aparezca
    # en los logs de rq. Pero, a la vez, pydantic no ofrece un método de
    # serialización en que se releve el valor de SafeStr. Una manera hacky
    # pero rápida de hacer un equivalente a obj.dict(decode_secrets=True)
    # es pasar a JSON con un custom encoder, y parsearlo de vuelta. :(

    token: SecretStr
    expires_at: str

    class Config:
        # https://github.com/samuelcolvin/pydantic/issues/596
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None,
        }

    def as_dict(self):
        # Esto es ugly AF.
        return json.loads(self.json())


class CorregirJob(BaseModel):
    repo: Repo
    head_sha: str
    check: Check
    entrega: Entrega
    corrector: Corrector
    installation_auth: AppInstallationTokenAuth
    checkrun_id: Optional[int] = None

    class Config:
        arbitrary_types_allowed = True
