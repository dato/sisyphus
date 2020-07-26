from abc import ABC, abstractmethod
from typing import List

from ..common.github_utils import repo_files
from ..common.typ import PyGithubRepo, RepoFile


class AluRepo(ABC):
    @abstractmethod
    def get_entrega(self, entrega_id: str, /, sha: str) -> List[RepoFile]:
        """
        """
        ...


class GithubAluRepo(AluRepo):
    """AluRepo en que que el id de entrega dobla como subdirectorio."""

    def __init__(self, alu_repo: PyGithubRepo):
        self.gh_repo = alu_repo

    def get_entrega(self, entrega_id: str, /, sha: str) -> List[RepoFile]:
        return repo_files(self.gh_repo, sha, subdir=entrega_id)
