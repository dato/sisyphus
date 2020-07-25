import pathlib
import re
import subprocess
import sys

import github
import github3  # type: ignore

from ..common.typ import CorregirJob
from .alu_repo import GithubAluRepo
from .base import CorrectorBase
from .tests_repo import FilesystemTestsRepo


TEST_PATHS = {
    "algo2": pathlib.Path("/srv/algo2/corrector/data/skel"),
}


def post_checkrun(job, checkrun_attrs):
    """Crea o actualiza un check_run en el repositorio."""
    # We use github3.py here, because PyGithub has no Checks API yet:
    # https://github.com/PyGithub/PyGithub/issues/1063
    session = github3.session.GitHubSession()
    session.app_installation_token_auth(job.installation_auth.as_dict())

    gh3 = github3.GitHub(session=session)
    repo = gh3.repository(job.repo.owner, job.repo.name)
    checkrun = repo.check_run(job.checkrun_id) if job.checkrun_id else None

    if not checkrun:
        checkrun = repo.create_check_run(**checkrun_attrs)
    else:
        checkrun.update(**checkrun_attrs)

    return checkrun


def corregir_entrega(job: CorregirJob):
    """
    """
    auth = job.installation_auth

    gh = github.Github(login_or_token=auth.token.get_secret_value())
    alu_repo = GithubAluRepo(gh.get_repo(job.repo.full_name))
    tests_loc = FilesystemTestsRepo(TEST_PATHS[job.materia] / job.head_branch)

    branch = job.head_branch
    corr = CorrectorBase(alu_repo, tests_loc)
    try:
        output = corr.corregir_entrega(branch, job.head_sha).decode(
            "utf-8", errors="replace"
        )
    except subprocess.CalledProcessError as ex:
        print(f"ERROR: {ex.output}", file=sys.stderr)
        raise ex from ex

    if not (m := re.search(r"^(Todo OK|ERROR)$", output, re.M)):
        conclusion = "cancelled"
        checkrun_output = dict(
            title="ERROR EN ENTREGA",
            summary="Ocurrió un error durante la corrección",
            text=f"```\n{output}\n```",
        )
    else:
        conclusion = "success" if m.group(1) == "Todo OK" else "failure"
        checkrun_output = dict(
            title=m.group(1),
            summary="Pruebas del corrector automático",
            text=f"```\n{output}\n```",
        )

    checkrun = post_checkrun(
        job,
        dict(
            name=f"Pruebas {branch}",
            head_sha=job.head_sha,
            conclusion=conclusion,
            output=checkrun_output,
        ),
    )

    # We set details_url to have a direct link available in Reviewable.
    checkrun.update(details_url=checkrun.html_url, output=checkrun_output)

    return checkrun
