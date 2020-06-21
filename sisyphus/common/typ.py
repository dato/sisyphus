from dataclasses import dataclass, field
from typing import Optional

from github.Repository import Repository as PyGithubRepo


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


@dataclass
class CorregirJob:
    repo_name: str
    materia: str
    head_sha: str
    head_branch: str
    checkrun_id: Optional[int] = None
