"""Endpoints de los repositorios para el corrector automático."""

import logging
import re

from flask_githubapp import GitHubApp  # type: ignore

from ..common.typ import AppInstallationTokenAuth, CorregirJob, Repo
from ..corrector.tasks import corregir_algo2
from .queue import task_queue
from .settings import load_config


__all__ = [
    "repos_hook",
]

repos_hook = GitHubApp()


def app_installation_token_auth() -> AppInstallationTokenAuth:
    """Obtiene el token de autenticación del objeto GitHubApp.
    """
    client = repos_hook.installation_client
    session_auth = client.session.auth
    # Para poder usar github3.py en el worker, se necesita tanto el token
    # como su fecha de expiración. Para PyGithub haría falta solamente el
    # token.
    return AppInstallationTokenAuth(
        token=session_auth.token, expires_at=session_auth.expires_at_str,
    )


@repos_hook.on("check_suite.requested")
def checksuite_requested():
    create_runs(repos_hook.payload)


@repos_hook.on("check_suite.rerequested")
def checksuite_rerequested():
    create_runs(repos_hook.payload)


def create_runs(payload):
    config = load_config()
    logger = logging.getLogger(__name__)

    repo = payload["repository"]
    suite = payload["check_suite"]
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
            repo=Repo(repo_full),
            materia="algo2",  # XXX
            head_sha=suite["head_sha"],
            head_branch=branch,
            installation_auth=app_installation_token_auth(),
            checkrun_id=None,  # TODO: create check run to pass it along.
        )
        task_queue.enqueue(corregir_algo2, job)
