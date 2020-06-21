"""Endpoints de los repositorios para el corrector automático."""

import logging
import re

from flask_githubapp import GitHubApp  # type: ignore

from ..common.typ import CorregirJob
from .queue import task_queue
from .settings import load_config
from .tasks import corregir_algo2


__all__ = [
    "repos_hook",
]

repos_hook = GitHubApp()


@repos_hook.on("check_suite.requested")
def on_checksuite():
    config = load_config()
    logger = logging.getLogger(__name__)

    repo = repos_hook.payload["repository"]
    suite = repos_hook.payload["check_suite"]
    branch = suite["head_branch"]
    repo_full = repo["full_name"]

    if not re.match(r"(algorw-alu|fiubatps)/algo2_2020a_", repo_full):  # XXX
        logger.debug(f"ignoring check_suite request from {repo_full}")
        return

    if branch not in config.materias["algo2"].branches:
        logging.warn(f"ignoring check_suite for branch {branch!r} in {repo_full}")
    else:
        logger.info(f"enqueuing check-run job for {repo_full}@{branch}")
        job = CorregirJob(
            repo_name=repo_full,
            materia="algo2",  # XXX
            head_sha=suite["head_sha"],
            head_branch=branch,
            checkrun_id=None,  # TODO: create check run to pass it along.
        )
        task_queue.enqueue(corregir_algo2, job)
