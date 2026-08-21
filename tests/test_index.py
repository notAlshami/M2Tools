import json
import time

from m2tools.core.index import build_index, find_parent_pom_artifact_ids, load_index


def _write_pom(path, artifact_id):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""<?xml version="1.0"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <artifactId>{artifact_id}</artifactId>
</project>
"""
    )


def test_find_parent_pom_artifact_ids_finds_project_root(tmp_path):
    _write_pom(tmp_path / "acme-widget" / "pom.xml", "acme-widget")
    assert find_parent_pom_artifact_ids([tmp_path]) == ["acme-widget"]


def test_find_parent_pom_artifact_ids_does_not_descend_into_submodules(tmp_path):
    _write_pom(tmp_path / "acme-widget" / "pom.xml", "acme-widget")
    _write_pom(tmp_path / "acme-widget" / "acme-widget-core" / "pom.xml", "acme-widget-core")

    assert find_parent_pom_artifact_ids([tmp_path]) == ["acme-widget"]


def test_find_parent_pom_artifact_ids_skips_excluded_dirs(tmp_path):
    _write_pom(tmp_path / ".m2" / "repository" / "some-cached-artifact" / "pom.xml", "some-cached-artifact")
    _write_pom(tmp_path / "acme-widget" / "target" / "generated" / "pom.xml", "generated-decoy")
    _write_pom(tmp_path / "acme-widget" / "pom.xml", "acme-widget")

    assert find_parent_pom_artifact_ids([tmp_path]) == ["acme-widget"]


def _make_m2_repo(tmp_path, artifact, version):
    vdir = tmp_path / "com" / "example" / artifact / version
    vdir.mkdir(parents=True)
    (vdir / f"{artifact}-{version}.pom").touch()
    return tmp_path


def test_build_index_writes_cache_file_with_artifacts_and_versions(tmp_path, monkeypatch):
    src_root = tmp_path / "src"
    _write_pom(src_root / "acme-widget" / "pom.xml", "acme-widget")
    m2_repo = _make_m2_repo(tmp_path / "m2repo", "acme-widget", "1.0-SNAPSHOT")
    cache_file = tmp_path / "cache" / "index.json"
    monkeypatch.setattr("m2tools.core.index.cache_path", lambda: cache_file)

    data = build_index(roots=[src_root], repo=m2_repo)

    assert data["artifacts"] == ["acme-widget"]
    assert data["versions"] == {"acme-widget": ["1.0-SNAPSHOT"]}
    saved = json.loads(cache_file.read_text())
    assert saved == data


def test_load_index_uses_fresh_cache_without_rescanning(tmp_path, monkeypatch):
    cache_file = tmp_path / "cache" / "index.json"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_text(
        json.dumps(
            {
                "generated_at": time.time(),
                "artifacts": ["cached-artifact"],
                "versions": {"cached-artifact": ["1.0-SNAPSHOT"]},
            }
        )
    )
    monkeypatch.setattr("m2tools.core.index.cache_path", lambda: cache_file)

    data = load_index(ttl=86400)
    assert data["artifacts"] == ["cached-artifact"]
    assert data["versions"] == {"cached-artifact": ["1.0-SNAPSHOT"]}


def test_load_index_rebuilds_when_cache_is_stale(tmp_path, monkeypatch):
    src_root = tmp_path / "src"
    _write_pom(src_root / "acme-widget" / "pom.xml", "acme-widget")
    m2_repo = _make_m2_repo(tmp_path / "m2repo", "acme-widget", "2.0.0")
    cache_file = tmp_path / "cache" / "index.json"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_text(
        json.dumps({"generated_at": time.time() - 999999, "artifacts": ["stale-artifact"], "versions": {}})
    )
    monkeypatch.setattr("m2tools.core.index.cache_path", lambda: cache_file)
    monkeypatch.setattr("m2tools.core.index.default_src_roots", lambda: [src_root])
    monkeypatch.setattr("m2tools.core.index.default_repo", lambda: m2_repo)

    data = load_index(ttl=86400)
    assert data["artifacts"] == ["acme-widget"]
    assert data["versions"] == {"acme-widget": ["2.0.0"]}


def test_load_index_force_rebuilds_even_if_fresh(tmp_path, monkeypatch):
    src_root = tmp_path / "src"
    _write_pom(src_root / "acme-widget" / "pom.xml", "acme-widget")
    m2_repo = _make_m2_repo(tmp_path / "m2repo", "acme-widget", "2.0.0")
    cache_file = tmp_path / "cache" / "index.json"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_text(
        json.dumps({"generated_at": time.time(), "artifacts": ["old-artifact"], "versions": {}})
    )
    monkeypatch.setattr("m2tools.core.index.cache_path", lambda: cache_file)
    monkeypatch.setattr("m2tools.core.index.default_src_roots", lambda: [src_root])
    monkeypatch.setattr("m2tools.core.index.default_repo", lambda: m2_repo)

    data = load_index(ttl=86400, force=True)
    assert data["artifacts"] == ["acme-widget"]
