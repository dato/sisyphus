import re
import subprocess
import sys

import github
import github3  # type: ignore

from ..common import github_tap, github_utils
from ..common.typ import CorregirJob
from .alu_repo import GithubAluRepo
from .base import CorrectorBase
from .tests_repo import FilesystemTestsRepo


def ensure_checkrun(job: CorregirJob):
    """Marca el checkrun como 'in_progress', creándolo si es necesario."""
    # We use github3.py here, because PyGithub has no Checks API yet:
    # https://github.com/PyGithub/PyGithub/issues/1063
    session = github3.session.GitHubSession()
    session.app_installation_token_auth(job.installation_auth.as_dict())
    github_utils.configure_retries(session)

    gh3 = github3.GitHub(session=session)
    repo = gh3.repository(job.repo.owner, job.repo.name)

    if job.checkrun_id is not None:
        checkrun = repo.check_run(job.checkrun_id)
        checkrun.update(status="in_progress")
    else:
        checkrun = repo.create_check_run(
            head_sha=job.head_sha, name=job.check.name, status="in_progress"
        )
    return checkrun


def corregir_entrega(job: CorregirJob):
    """
    """
    auth = job.installation_auth
    check = job.check
    entrega = job.entrega
    corr_info = job.corrector
    checkrun = ensure_checkrun(job)

    # FIXME: support these.
    assert not check.alu_files
    assert not check.test_files
    assert corr_info.formatter in ("github_tap", "v2_original")  # TODO: use enum

    alu_subdir = entrega.alu_dir or entrega.name
    tests_subdir = entrega.alu_dir or entrega.name

    gh = github.Github(login_or_token=auth.token.get_secret_value())
    alu_repo = GithubAluRepo(gh.get_repo(job.repo.full_name))
    tests_loc = FilesystemTestsRepo(corr_info.tests_path / tests_subdir)

    corr = CorrectorBase(alu_repo, tests_loc)
    try:
        output = corr.corregir_entrega(alu_subdir, job.head_sha).decode(
            "utf-8", errors="backslashreplace"
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
    elif corr_info.formatter == "github_tap":
        output = re.sub(r"^(Todo OK|ERROR)\n\n", "", output, re.M)
        conclusion, checkrun_output = github_tap.checkrun_output(output)
    elif corr_info.formatter == "v2_original":
        conclusion = "success" if m.group(1) == "Todo OK" else "failure"
        checkrun_output = dict(
            title=m.group(1),
            summary="Pruebas del corrector automático",
            text=f"```\n{output}\n```",
        )

    # We set details_url to have a direct link available in Reviewable.
    checkrun.update(
        conclusion=conclusion, output=checkrun_output, details_url=checkrun.html_url,
    )

    return checkrun
