import logging
import pathlib

from typing import List

from .typ import PyGithubRepo, RepoFile


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

    for entry in contents:
        if entry.type != "file":
            logger.warn(f"ignoring entry {entry.path!r} of type {entry.type}")
            continue
        rel_path = pathlib.PurePath(entry.path).relative_to(subdir)
        repo_files.append(
            RepoFile(path=rel_path.as_posix(), contents=entry.decoded_content)
        )

    return repo_files
