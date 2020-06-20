"""Endpoints de los repositorios para el corrector automático."""

import logging

from flask_githubapp import GitHubApp

from .reposdb import make_reposdb


__all__ = [
    "repos_hook",
]

reposdb = make_reposdb()
repos_hook = GitHubApp()


@repos_hook.on("check_suite.requested")
def on_checksuite():
    logger = logging.getLogger(__name__)
    repo = repos_hook.payload["repository"]
    repo_full = repo["full_name"]

    logger.debug(f"received check_suite request for {repo_full}")

    if reposdb.is_repo_known(repo_full):
        # TODO: create check run here.
        logger.info(f"enqueued check run for {repo_full}")
    else:
        logger.info(f"ignoring check_suite request from unknown repo {repo_full}")
