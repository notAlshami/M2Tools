from types import SimpleNamespace

from typer.testing import CliRunner

from m2tools.cli import app
from m2tools.commands.delete import complete_version

runner = CliRunner()


def _make_repo(tmp_path):
    app_dir = tmp_path / "com" / "example" / "my-app"
    (app_dir / "1.0-SNAPSHOT").mkdir(parents=True)
    (app_dir / "2.3.0").mkdir(parents=True)
    (app_dir / "1.0-SNAPSHOT" / "marker.jar").touch()
    return tmp_path


def test_delete_dry_run_keeps_files(tmp_path):
    repo = _make_repo(tmp_path)
    result = runner.invoke(app, ["delete", "my-app", "--repo", str(repo), "--dry-run"])
    assert result.exit_code == 0
    assert "Would delete" in result.stdout
    assert (repo / "com" / "example" / "my-app" / "1.0-SNAPSHOT").exists()


def test_delete_removes_matching_version_only(tmp_path):
    repo = _make_repo(tmp_path)
    result = runner.invoke(app, ["delete", "my-app", "--repo", str(repo)])
    assert result.exit_code == 0
    assert not (repo / "com" / "example" / "my-app" / "1.0-SNAPSHOT").exists()
    assert (repo / "com" / "example" / "my-app" / "2.3.0").exists()


def test_delete_unknown_app_errors(tmp_path):
    repo = _make_repo(tmp_path)
    result = runner.invoke(app, ["delete", "unknown-app", "--repo", str(repo)])
    assert result.exit_code != 0


def test_reindex_reports_project_and_version_count(tmp_path, monkeypatch):
    src_root = tmp_path / "src"
    project_dir = src_root / "acme-widget"
    project_dir.mkdir(parents=True)
    (project_dir / "pom.xml").write_text(
        '<project xmlns="http://maven.apache.org/POM/4.0.0">'
        "<artifactId>acme-widget</artifactId></project>"
    )
    m2_repo = tmp_path / "m2repo"
    vdir = m2_repo / "com" / "example" / "acme-widget" / "1.0-SNAPSHOT"
    vdir.mkdir(parents=True)
    (vdir / "acme-widget-1.0-SNAPSHOT.pom").touch()

    monkeypatch.setattr("m2tools.core.index.cache_path", lambda: tmp_path / "cache" / "index.json")
    monkeypatch.setattr("m2tools.core.index.default_src_roots", lambda: [src_root])
    monkeypatch.setattr("m2tools.core.index.default_repo", lambda: m2_repo)

    result = runner.invoke(app, ["reindex"])

    assert result.exit_code == 0
    assert "Indexed 1 project(s), 1 version(s)." in result.stdout


def test_complete_version_suggests_default_when_app_has_none_indexed(monkeypatch):
    monkeypatch.setattr(
        "m2tools.commands.delete.load_index",
        lambda: {"artifacts": ["empty-app"], "versions": {}},
    )
    ctx = SimpleNamespace(params={"app_name": "empty-app"})

    assert complete_version(ctx, "") == ["1.0-SNAPSHOT"]


def test_complete_version_returns_real_matches_when_present(monkeypatch):
    monkeypatch.setattr(
        "m2tools.commands.delete.load_index",
        lambda: {"artifacts": ["my-app"], "versions": {"my-app": ["1.0-SNAPSHOT", "2.3.0"]}},
    )
    ctx = SimpleNamespace(params={"app_name": "my-app"})

    assert complete_version(ctx, "2") == ["2.3.0"]


def test_uninstall_cleans_up_and_calls_pipx(tmp_path, monkeypatch):
    zfunc_dir = tmp_path / ".zfunc"
    zfunc_dir.mkdir()
    (zfunc_dir / "_m2tools").touch()
    cache_dir = tmp_path / ".cache" / "m2tools"
    cache_dir.mkdir(parents=True)

    monkeypatch.setattr("m2tools.commands.uninstall.Path.home", lambda: tmp_path)
    calls = []
    monkeypatch.setattr(
        "m2tools.commands.uninstall.subprocess.run", lambda *a, **k: calls.append((a, k))
    )

    result = runner.invoke(app, ["uninstall", "--yes"])

    assert result.exit_code == 0
    assert not cache_dir.exists()
    assert not zfunc_dir.exists()
    assert calls == [((["pipx", "uninstall", "m2tools"],), {"check": False})]


def test_uninstall_aborts_without_confirmation(tmp_path, monkeypatch):
    monkeypatch.setattr("m2tools.commands.uninstall.Path.home", lambda: tmp_path)
    calls = []
    monkeypatch.setattr(
        "m2tools.commands.uninstall.subprocess.run", lambda *a, **k: calls.append((a, k))
    )

    result = runner.invoke(app, ["uninstall"], input="n\n")

    assert result.exit_code != 0
    assert calls == []
