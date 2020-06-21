import os
import pathlib
import re
import subprocess

from dotenv import load_dotenv

from ..common.github_utils import app_auth
from ..common.typ import CorregirJob
from ..corrector import *


ALGO2_TESTS = pathlib.Path("/srv/algo2/corrector/data/skel")


def corregir_algo2(job: CorregirJob):
    """
    """
    assert re.match("(algorw-alu|fiubatps)/algo2_", job.repo_name)

    load_dotenv()
    app_id = int(os.environ["REPOS_APP_ID"])
    private_key = open(".repos.pem").read()

    gh = app_auth(job.repo_name, app_id, private_key)
    gh_repo = gh.get_repo(job.repo_name)
    alu_repo = GithubAluRepo(gh_repo)
    tests_loc = FilesystemTestsRepo(ALGO2_TESTS / job.head_branch)

    branch = job.head_branch
    corr = CorrectorBase(alu_repo, tests_loc)
    try:
        output = corr.corregir_entrega(branch, job.head_sha).decode(
            "utf-8", errors="replace"
        )
    except subprocess.CalledProcessError as ex:
        print(f"ERROR: {ex.output}")
        raise ex from ex

    if not (m := re.search(r"^(Todo OK|ERROR)$", output, re.M)):
        conclusion = "cancelled"
        checkrun_output = None  # TODO: say something.
    else:
        conclusion = "success" if m.group(1) == "Todo OK" else "failure"
        checkrun_output = dict(
            title=m.group(1),
            summary="Pruebas del corrector automático",
            text=f"```\n{output}\n```",
        )

    checkrun = dict(
        name=f"Pruebas {branch}",
        head_sha=job.head_sha,
        conclusion=conclusion,
        output=checkrun_output,
    )

    # XXX: Use of private member _requester
    status, header, body = gh_repo._requester.requestJson(
        "POST",
        f"{gh_repo.url}/check-runs",  # TODO: use job.checkrun_id if not None.
        input=checkrun,
        headers={"Accept": "application/vnd.github.antiope-preview+json"},
    )
    return header["status"]
