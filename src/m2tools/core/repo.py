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


def read_pom_parent_artifact_id(pom_file: Path):
    """Read the `<parent><artifactId>` a submodule's own .pom declares, if any."""
    try:
        root = ET.parse(pom_file).getroot()
    except (ET.ParseError, OSError):
        return None
    ns = root.tag[: root.tag.index("}") + 1] if root.tag.startswith("{") else ""
    parent_el = root.find(f"{ns}parent")
    if parent_el is None:
        return None
    artifact_id_el = parent_el.find(f"{ns}artifactId")
    if artifact_id_el is None or not artifact_id_el.text:
        return None
    return artifact_id_el.text.strip()


def artifact_parent_id(artifact_dir: Path):
    """Return the `<parent><artifactId>` declared by any installed version of `artifact_dir`.

    A submodule's declared parent artifactId is stable across releases, so
    reading it from *any* version this artifact still has on disk is
    enough -- it doesn't require the specific version being deleted to
    still be installed here. That matters for chains of orphans: if an
    intermediate ancestor's matching version was already cleaned up (by an
    earlier `delete`, or manually), its parent pointer -- and thus the
    link connecting a deeper orphan back to the artifact actually being
    deleted -- would otherwise be lost along with it.
    """
    for candidate_dir in artifact_dir.iterdir():
        if not candidate_dir.is_dir():
            continue
        pom_file = next(candidate_dir.glob("*.pom"), None)
        if pom_file is None:
            continue
        parent_artifact_id = read_pom_parent_artifact_id(pom_file)
        if parent_artifact_id:
            return parent_artifact_id
    return None


def find_version_dirs(repo: Path, app_name: str, version: str):
    """Resolve every version directory to delete for `app_name`.

    A multi-module parent's submodules are separate artifactIds that a
    plain by-name delete would leave behind. This follows both links
    between a parent and its submodules to build the whole family (every
    artifactId descending from `app_name`, at any depth), then deletes
    whichever family members actually have a directory matching `version`:

    - forward, via the parent's `<modules>` list at the version being
      deleted, and
    - backward, via each sibling artifact's declared `<parent><artifactId>`
      (see `artifact_parent_id`) -- which also catches an orphan: a
      submodule dropped from its parent's `<modules>` list (renamed,
      replaced, ...) in a later build but never uninstalled, so it still
      declares this ancestry even though nothing forward-links to it
      anymore. Because this is read from any version of the artifact, an
      orphan several levels deep is still found even when the *specific*
      version being deleted was already cleaned up higher up the chain --
      e.g. deleting a parent whose top few levels have no matching
      version installed at all, but a long-orphaned leaf several levels
      down still does.

    Submodules are looked up as siblings of their parent's own directory
    (`<parent's groupId dir>/<module>`) rather than another repo-wide
    search: Maven's repo layout is flat under each groupId regardless of
    source-tree nesting, so every submodule at any depth already lives
    there, and a repo-wide `rglob` per module -- run recursively down
    every level of a multi-module tree -- is both slow (one full walk of
    a repo with tens of thousands of directories per module) and wrong if
    some unrelated artifact elsewhere happens to share a module's bare
    directory name.
    """
    children_by_parent_cache = {}

    def children_by_parent(group_dir):
        """{parent artifactId -> [sibling dirs]} for one groupId dir, built once."""
        mapping = children_by_parent_cache.get(group_dir)
        if mapping is None:
            mapping = {}
            for sibling_dir in group_dir.iterdir():
                if not sibling_dir.is_dir():
                    continue
                parent_artifact_id = artifact_parent_id(sibling_dir)
                if parent_artifact_id:
                    mapping.setdefault(parent_artifact_id, []).append(sibling_dir)
            children_by_parent_cache[group_dir] = mapping
        return mapping

    app_dirs = find_artifact_dirs(repo, app_name)
    family = {}
    to_visit = [(app_name, app_dir) for app_dir in app_dirs]
    while to_visit:
        name, app_dir = to_visit.pop()
        if name in family:
            continue
        family[name] = app_dir
        group_dir = app_dir.parent
        for version_dir in matching_version_dirs(app_dir, version):
            for module in read_pom_modules(version_dir):
                module_dir = group_dir / module
                if module_dir.is_dir() and module not in family:
                    to_visit.append((module, module_dir))
        for child_dir in children_by_parent(group_dir).get(name, []):
            if child_dir.name not in family:
                to_visit.append((child_dir.name, child_dir))

    version_dirs = []
    for app_dir in family.values():
        version_dirs.extend(matching_version_dirs(app_dir, version))
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
