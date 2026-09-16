import os
import xml.etree.ElementTree as ET
from pathlib import Path

DEFAULT_VERSION = "1.0-SNAPSHOT"


def default_repo() -> Path:
    return Path(os.environ.get("M2_REPO", str(Path.home() / ".m2" / "repository")))


def find_artifact_dirs(repo: Path, app: str):
    return [p for p in repo.rglob(app) if p.is_dir()]


def matching_version_dirs(app_dir: Path, version: str):
    return sorted(p for p in app_dir.glob(f"{version}*") if p.is_dir())


def read_pom_modules(version_dir: Path):
    """Read the `<modules>` list from the .pom file installed in `version_dir`.

    A multi-module (aggregator) parent POM lists its submodules here, by
    directory name -- which is conventionally also the submodule's own
    artifactId. Returns [] for a regular (non-aggregator) artifact.
    """
    for pom_file in version_dir.glob("*.pom"):
        try:
            root = ET.parse(pom_file).getroot()
        except (ET.ParseError, OSError):
            continue
        ns = root.tag[: root.tag.index("}") + 1] if root.tag.startswith("{") else ""
        modules_el = root.find(f"{ns}modules")
        if modules_el is None:
            continue
        return [m.text.strip() for m in modules_el.findall(f"{ns}module") if m.text]
    return []


def find_version_dirs(repo: Path, app_name: str, version: str):
    """Resolve every version directory to delete for `app_name`.

    Follows `<modules>` of any aggregator POM found at the matching
    version, so deleting a multi-module parent also sweeps up its
    already-installed submodules (which are separate artifactIds, and
    otherwise left behind by a plain by-name delete).
    """
    seen_names = set()
    to_visit = [app_name]
    version_dirs = []
    while to_visit:
        name = to_visit.pop()
        if name in seen_names:
            continue
        seen_names.add(name)
        for app_dir in find_artifact_dirs(repo, name):
            for version_dir in matching_version_dirs(app_dir, version):
                version_dirs.append(version_dir)
                to_visit.extend(read_pom_modules(version_dir))
    return version_dirs


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
