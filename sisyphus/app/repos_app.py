"""Endpoints de los repositorios para el corrector automático."""

import logging
import re

from flask_githubapp import GitHubApp  # type: ignore

from ..common import github_utils
from ..common.typ import AppInstallationTokenAuth, CorregirJob, Repo
from ..corrector.tasks import corregir_entrega
from .queue import task_queue
from .reposdb import make_reposdb
from .settings import load_config


__all__ = [
    "repos_hook",
]

reposdb = make_reposdb()
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


@repos_hook.on("check_run.rerequested")
def checkrun_rerequested():
    create_runs(repos_hook.payload)


def create_runs(payload):
    config = load_config()
    logger = logging.getLogger(__name__)

    # We are normally called from check_suite.(re)requested, but this could also be
    # a check_run.rerequested; in that case the check_suite is inside the check_run
    # object, and we limit ourselves to retrying that one check, only.
    if "check_run" not in payload:
        suite = payload["check_suite"]
        check_rerequested = None
    else:
        suite = payload["check_run"]["check_suite"]
        check_rerequested = payload["check_run"]["name"]

    repo = payload["repository"]
    branch = suite["head_branch"]
    repo_full = repo["full_name"]

    if not reposdb.is_repo_known(repo_full):
        logger.debug(f"ignoring check_suite request from unknown repo {repo_full}")
        return
    elif re.match(r"^0+$", suite["before"]):
        logger.info(f"ignoring check_suite event for just-created {repo_full}@{branch}")
        return

    try:
        # TODO: cambiar esto por un wildcard de paths.
        entrega = next(e for e in config.entregas.values() if e.branch == branch)
    except StopIteration:
        logging.warn(f"ignoring check_suite for branch {branch!r} in {repo_full}")
        return

    for check in entrega.checks:
        check = config.checks[check]
        if not check_rerequested or check.name == check_rerequested:
            logger.info(f"enqueuing {check.name} for {repo_full}@{branch}")
        else:
            logger.debug(f"skipping {check.name}, which was not rerequested")
            continue
        job = CorregirJob(
            repo=Repo(repo_full),
            head_sha=suite["head_sha"],
            check=check,
            entrega=entrega,
            corrector=config.corrector,
            installation_auth=app_installation_token_auth(),
        )
        job.checkrun_id = create_checkrun(job)
        task_queue.enqueue(corregir_entrega, job)


def create_checkrun(job):
    """Crea un check_run para pasar al worker. Devuelve el checkrun id."""
    gh3 = repos_hook.installation_client
    github_utils.configure_retries(gh3.session)
    repo = gh3.repository(job.repo.owner, job.repo.name)
    checkrun = repo.create_check_run(head_sha=job.head_sha, name=job.check.name)
    return checkrun.id
