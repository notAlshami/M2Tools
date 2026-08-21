from m2tools.core.repo import (
    find_artifact_dirs,
    list_app_names,
    list_version_names,
    matching_version_dirs,
)


def _make_repo(tmp_path):
    app_dir = tmp_path / "com" / "example" / "my-app"
    (app_dir / "1.0-SNAPSHOT").mkdir(parents=True)
    (app_dir / "2.3.0").mkdir(parents=True)
    (app_dir / "1.0-SNAPSHOT" / "marker.jar").touch()
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


def test_list_app_names(tmp_path):
    repo = _make_repo(tmp_path)
    assert "my-app" in list_app_names(repo, "my")


def test_list_version_names(tmp_path):
    repo = _make_repo(tmp_path)
    assert list_version_names(repo, "my-app", "2") == ["2.3.0"]
