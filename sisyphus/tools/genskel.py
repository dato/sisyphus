#!/usr/bin/env python3

"""Genera un repositorio con el esqueleto configurado en skelbot.yaml.

Se debe correr en el directorio top-level del repositorio origen. El
esqueleto se genera/actualiza en una rama (por omisión ‘pubskel’), lo
cual evita tener que ir copiando blobs de un repositorio a otro.
"""

import argparse
import sys

from pathlib import Path
from typing import Dict, Union

import git  # type: ignore
import yaml

from ..skelbot.typ import Settings, Skeldir


def parse_args():
    """Parser para los argumentos del programa.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-b", "--branch", default="pubskel", help="branch para el esqueleto"
    )
    return parser.parse_args()


def main():
    """Función principal del script.
    """
    args = parse_args()
    config = load_config()

    repo = git.Repo(".")
    try:
        branch = repo.refs[args.branch]
    except IndexError:
        print(f"the target branch {args.branch!r} must exist", file=sys.stderr)
        return 1

    for skeldir in config.skeldirs:
        update_skel(repo, skeldir, target_ref=branch)


def update_skel(repo: git.Repo, skeldir: Skeldir, *, target_ref: git.Head):
    """Lala.
    """
    srcdir = Path(skeldir.srcdir or ".")
    filemap: Dict[str, Path] = {}

    # Expand the patterns their target routes. "files" are globs, possibly
    # relative to a source directory, and preserve directory structure. On
    # the other hand, "extra_files" are always absolute, and just keep the
    # name.
    for pattern in skeldir.files:
        for path in srcdir.glob(pattern):
            rel_path: Union[Path, str] = path.relative_to(
                srcdir
            ) if skeldir.srcdir else path.name
            filemap[path.as_posix()] = skeldir.target / rel_path

    for path in skeldir.extra_files:
        filemap[path.as_posix()] = skeldir.target / path.name

    # Create a new commit in a temporary index.
    orig_tree = repo.tree()
    skel_tree = target_ref.commit.tree
    new_index = git.IndexFile.new(repo, skel_tree)

    # Using blobs preserves symlinks, which is probably not what we want. But, at the
    # same time, it makes it possible to be precise about which revision to export.
    target_blobs = [orig_tree[path] for path in filemap]

    new_index.add(target_blobs, path_rewriter=lambda e: filemap[e.path].as_posix())
    print(new_index.commit("lala2", parent_commits=[target_ref.commit], head=False))


def load_config() -> Settings:
    """Carga la configuración de .skelbot.yaml.

    Returns:
       un objeto de tipo Settings, validado.
    """
    with open(".skelbot.yaml") as yml:
        conf = yaml.safe_load(yml)
        return Settings(**conf)
