import logging
import pathlib

from typing import List, Set

import github
import github3  # type: ignore

from github3.session import GitHubSession  # type: ignore
from github.ContentFile import ContentFile
from github.GithubException import GithubException
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .typ import PyGithubRepo, Repo, RepoFile


def exception_codes(gh_exception: GithubException) -> Set[str]:
    """Devuelve todos los error codes de una excepción de PyGitHub.
    """
    errors = gh_exception.data.get("errors", [])  # type: ignore
    return {code for e in errors if (code := e.get("code"))}  # type: ignore


def configure_retries(session: GitHubSession):
    """Configure retries for a github3 client.
    """
    # https://cumulusci.readthedocs.io/en/latest/_modules/cumulusci/core/github.html
    retries = Retry(status_forcelist=(401, 502, 503, 504), backoff_factor=0.3)
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)


def repo_files(gh_repo: PyGithubRepo, sha: str, subdir: str = None) -> List[RepoFile]:
    """
    """
    # TODO: añadir soporte para directorios.
    # TODO: añadir soporte para permisos.
    # TODO: verificar que get_contents() es recursivo.
    logger = logging.getLogger(__name__)
    subdir = subdir.rstrip("/") if subdir else ""
    contents = gh_repo.get_contents(subdir, sha)
    repo_files = []

    if isinstance(contents, ContentFile):
        contents = [contents]

    for entry in contents:
        if entry.type != "file":
            logger.warn(f"ignoring entry {entry.path!r} of type {entry.type}")
            continue
        rel_path = pathlib.PurePath(entry.path).relative_to(subdir)
        try:
            repo_file = RepoFile(
                path=rel_path.as_posix(), contents=entry.decoded_content
            )
        except GithubException as ex:
            if "too_large" in exception_codes(ex):
                # FIXME: usar la Git Data API para descargar el archivo?
                logger.warn(f"por su tamaño no se pudo descargar {entry.path!r}")
            else:
                raise ex from ex
        else:
            repo_files.append(repo_file)

    return repo_files


def github3_installation_auth(repo: Repo, app_id: int, private_key: bytes):
    """
    """
    gh3 = github3.GitHub()
    gh3.login_as_app(private_key, app_id)

    installation = gh3.app_installation_for_repository(repo.owner, repo.name)
    gh3.login_as_app_installation(private_key, app_id, installation.id)

    return gh3


def app_auth(repo_name: str, app_id: int, private_key: str):
    gh = github.GithubIntegration(app_id, private_key)

    owner, repo = repo_name.split("/")
    inst = gh.get_installation(owner, repo)
    inst_auth = gh.get_access_token(inst.id.value)  # type: ignore
    # error: "_ValuedAttribute" has no attribute "value"

    return github.Github(login_or_token=inst_auth.token)
