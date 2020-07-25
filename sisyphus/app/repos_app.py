"""Endpoints de los repositorios para el corrector automático."""

import logging
import re

from flask_githubapp import GitHubApp  # type: ignore

from ..common.typ import AppInstallationTokenAuth, CorregirJob, Repo
from ..corrector.tasks import corregir_entrega
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

    if re.match(r"^0+$", suite["before"]):
        logger.info(f"ignoring check_suite event for just-created {repo_full}@{branch}")
        return
    elif m := re.match(r"(algorw-alu|fiubatps)/(algo2)_2020a_", repo_full):
        materia = m.group(2)
    else:
        logger.debug(f"ignoring check_suite request from {repo_full}")
        return

    if branch not in config.materias[materia].branches:
        logging.warn(f"ignoring check_suite for branch {branch!r} in {repo_full}")
    else:
        logger.info(f"enqueuing check-run job for {repo_full}@{branch}")
        job = CorregirJob(
            repo=Repo(repo_full),
            materia=materia,
            head_sha=suite["head_sha"],
            head_branch=branch,
            installation_auth=app_installation_token_auth(),
        )
        job.checkrun_id = create_checkrun(job)
        task_queue.enqueue(corregir_entrega, job)


def create_checkrun(job):
    """Crea un check_run para pasar al worker. Devuelve el checkrun id."""
    gh3 = repos_hook.installation_client
    repo = gh3.repository(job.repo.owner, job.repo.name)
    checkrun = repo.create_check_run(
        head_sha=job.head_sha, name=f"Pruebas {job.head_branch}"
    )
    return checkrun.id
