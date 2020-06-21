import logging
import os
import pathlib

from abc import ABC, abstractmethod
from typing import List

from ..common.typ import RepoFile


class TestsRepo(ABC):
    @abstractmethod
    def get_tests(self) -> List[RepoFile]:
        """
        """
        ...


class FilesystemTestsRepo(TestsRepo):
    """
    """

    def __init__(self, tests_dir: pathlib.Path):
        self.logger = logging.getLogger(__name__)
        self.tests_dir = pathlib.Path(tests_dir)

    def get_tests(self) -> List[RepoFile]:
        """
        """
        toplevel = self.tests_dir
        repo_files: List[RepoFile] = []

        def make_file(full_path):
            rel_path = full_path.relative_to(toplevel).as_posix()
            try:
                with open(full_path, "rb") as fileobj:
                    return RepoFile(path=rel_path, contents=fileobj.read())
            except IOError as ex:
                self.logger.warn(f"could not read {full_path}: {ex}")

        for dirname, _dirs, files in os.walk(toplevel, followlinks=True):
            dirpath = pathlib.PurePath(dirname)
            repo_files.extend(
                repo_file
                for filename in files
                if (repo_file := make_file(dirpath / filename)) is not None
            )

        return repo_files
