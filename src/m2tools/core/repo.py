import os
from pathlib import Path

DEFAULT_VERSION = "1.0-SNAPSHOT"


def default_repo() -> Path:
    return Path(os.environ.get("M2_REPO", str(Path.home() / ".m2" / "repository")))


def find_artifact_dirs(repo: Path, app: str):
    return [p for p in repo.rglob(app) if p.is_dir()]


def matching_version_dirs(app_dir: Path, version: str):
    return sorted(p for p in app_dir.glob(f"{version}*") if p.is_dir())


def list_app_names(repo: Path, prefix: str = ""):
    if not repo.is_dir():
        return []
    names = set()
    for d in repo.rglob(f"{prefix}*"):
        if d.is_dir() and any(c.is_dir() for c in d.iterdir()):
            names.add(d.name)
    return sorted(names)


def list_version_names(repo: Path, app: str, prefix: str = ""):
    if not app or not repo.is_dir():
        return []
    names = set()
    for app_dir in find_artifact_dirs(repo, app):
        for v in app_dir.glob(f"{prefix}*"):
            if v.is_dir():
                names.add(v.name)
    return sorted(names)
