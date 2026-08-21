from m2tools.core.repo import (
    find_artifact_dirs,
    matching_version_dirs,
    scan_versions_by_artifact,
)


def _make_repo(tmp_path):
    app_dir = tmp_path / "com" / "example" / "my-app"
    (app_dir / "1.0-SNAPSHOT").mkdir(parents=True)
    (app_dir / "2.3.0").mkdir(parents=True)
    (app_dir / "1.0-SNAPSHOT" / "my-app-1.0-SNAPSHOT.pom").touch()
    (app_dir / "1.0-SNAPSHOT" / "my-app-1.0-SNAPSHOT.jar").touch()
    (app_dir / "2.3.0" / "my-app-2.3.0.pom").touch()
    return tmp_path


def test_find_artifact_dirs(tmp_path):
    repo = _make_repo(tmp_path)
    dirs = find_artifact_dirs(repo, "my-app")
    assert [d.name for d in dirs] == ["my-app"]


def test_matching_version_dirs(tmp_path):
    repo = _make_repo(tmp_path)
    app_dir = repo / "com" / "example" / "my-app"
    versions = matching_version_dirs(app_dir, "1.0-SNAPSHOT")
    assert [v.name for v in versions] == ["1.0-SNAPSHOT"]


def test_scan_versions_by_artifact(tmp_path):
    repo = _make_repo(tmp_path)
    assert scan_versions_by_artifact(repo) == {"my-app": ["1.0-SNAPSHOT", "2.3.0"]}


def test_scan_versions_by_artifact_ignores_dirs_without_pom(tmp_path):
    repo = _make_repo(tmp_path)
    decoy = repo / "com" / "example" / "my-app-docs" / "not-a-version"
    decoy.mkdir(parents=True)
    (decoy / "README.txt").touch()

    versions = scan_versions_by_artifact(repo)
    assert "my-app-docs" not in versions
    assert "not-a-version" not in versions
