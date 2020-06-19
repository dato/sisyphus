"""Endpoints de los repositorios para el corrector automático."""

import logging

from flask_githubapp import GitHubApp


__all__ = [
    "repos_hook",
]

repos_hook = GitHubApp()


@repos_hook.on("check_suite.requested")
def on_checksuite():
    logger = logging.getLogger(__name__)
    repo = repos_hook.payload["repository"]
    repo_full = repo["full_name"]
    logger.info(f"received check_suite request for {repo_full}")
