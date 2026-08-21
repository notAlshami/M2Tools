import json
import os
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from m2tools.core.repo import default_repo, scan_versions_by_artifact

DEFAULT_TTL_SECONDS = 86400  # 1 day

# Directories that never hold a project's own pom.xml but are expensive or
# noisy to walk into: build output, dependency caches, and the local Maven
# repository itself (which is exactly what this index replaces as a data
# source for completion).
EXCLUDE_DIR_NAMES = {"node_modules", "target", "build", "dist", "out", "Android", "snap"}


def default_src_roots():
    env = os.environ.get("M2TOOLS_SRC_ROOTS")
    if env:
        return [Path(p).expanduser() for p in env.split(":") if p]
    return [Path.home()]


def cache_path() -> Path:
    cache_home = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
    return cache_home / "m2tools" / "index.json"


def _pom_artifact_id(pom_file: Path):
    try:
        root = ET.parse(pom_file).getroot()
    except (ET.ParseError, OSError):
        return None
    ns = root.tag[: root.tag.index("}") + 1] if root.tag.startswith("{") else ""
    element = root.find(f"{ns}artifactId")
    return element.text.strip() if element is not None and element.text else None


def find_parent_pom_artifact_ids(roots):
    """Find each project's own (parent) pom.xml artifactId under `roots`.

    Stops descending as soon as a pom.xml is found in a directory, so
    submodules of a multi-module project aren't indexed individually --
    only the top-level project name is. This mirrors how the actual
    projects are organized on disk, instead of the flattened, much
    noisier module list found under ~/.m2/repository.
    """
    artifact_ids = []
    for root in roots:
        if not root.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in EXCLUDE_DIR_NAMES]
            if "pom.xml" in filenames:
                artifact_id = _pom_artifact_id(Path(dirpath) / "pom.xml")
                if artifact_id:
                    artifact_ids.append(artifact_id)
                dirnames[:] = []
    return artifact_ids


def build_index(roots=None, repo=None):
    artifact_ids = sorted(set(find_parent_pom_artifact_ids(roots or default_src_roots())))
    versions_by_artifact = scan_versions_by_artifact(repo or default_repo())
    data = {
        "generated_at": time.time(),
        "artifacts": artifact_ids,
        "versions": versions_by_artifact,
    }
    path = cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return data


def load_index(ttl: float = DEFAULT_TTL_SECONDS, force: bool = False):
    path = cache_path()
    if not force and path.is_file():
        try:
            data = json.loads(path.read_text())
            if time.time() - data.get("generated_at", 0) < ttl:
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return build_index()
