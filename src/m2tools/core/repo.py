import os
from pathlib import Path

DEFAULT_VERSION = "1.0-SNAPSHOT"


def default_repo() -> Path:
    return Path(os.environ.get("M2_REPO", str(Path.home() / ".m2" / "repository")))


def find_artifact_dirs(repo: Path, app: str):
    return [p for p in repo.rglob(app) if p.is_dir()]


def matching_version_dirs(app_dir: Path, version: str):
    return sorted(p for p in app_dir.glob(f"{version}*") if p.is_dir())


def scan_versions_by_artifact(repo: Path):
    """Walk `repo` once, mapping each artifactId dir name to its version names.

    `find_artifact_dirs`/`list_version_names` re-walk the whole repo on
    every call (used by `delete` itself, where that's a one-off, correctness
    -critical live lookup). This does it once so the result can be cached
    for fast, repeated completion lookups instead.
    """
    versions_by_artifact = {}
    if not repo.is_dir():
        return versions_by_artifact
    for dirpath, dirnames, filenames in os.walk(repo):
        if any(name.endswith(".pom") for name in filenames):
            version_name = os.path.basename(dirpath)
            parent_name = os.path.basename(os.path.dirname(dirpath))
            versions_by_artifact.setdefault(parent_name, []).append(version_name)
    for versions in versions_by_artifact.values():
        versions.sort()
    return versions_by_artifact
