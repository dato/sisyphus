"""Clase base para correcciones desde Github."""

import datetime
import io
import pathlib
import subprocess
import tarfile

from typing import Type

from .alu_repo import AluRepo
from .tests_repo import TestsRepo


__all__ = [
    "CorrectorBase",
]

CORRECTOR_BIN = "/srv/algo2/corrector/bin/worker"


class CorrectorBase:
    """
    """

    def __init__(self, alu_repo: Type[AluRepo], tests_repo: Type[TestsRepo]):
        self.alu_repo = alu_repo
        self.tests_repo = tests_repo

    def corregir_entrega(self, entrega_id: str, /, *, sha: str):
        tarbytes = io.BytesIO()
        now = datetime.datetime.now()
        tarobj = tarfile.open(fileobj=tarbytes, mode="w|", dereference=True)

        test_files = self.tests_repo.get_tests()
        entrega_files = self.alu_repo.get_entrega(entrega_id, sha)

        def add_file(repo_file, prefix):
            info = tarfile.TarInfo((prefix / repo_file.path).as_posix())
            info.size = len(repo_file.contents)
            info.mtime = now.timestamp()
            info.type, info.mode = tarfile.REGTYPE, repo_file.mode
            tarobj.addfile(info, io.BytesIO(repo_file.contents))

        for subdir, files in ("skel", test_files), ("orig", entrega_files):
            # FIXME: El worker actual hace el merge entre orig/ y
            # skel/, pero estaría quizás mejor hacerlo aquí.
            prefix = pathlib.PurePath(subdir)
            for repo_file in files:
                add_file(repo_file, prefix)

        tarobj.close()

        # TODO: timeout here for "timed_out" conclusion.
        return subprocess.check_output(
            [CORRECTOR_BIN], input=tarbytes.getvalue(), stderr=subprocess.STDOUT
        )
