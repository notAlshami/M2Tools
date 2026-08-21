from typer.testing import CliRunner

from m2tools.cli import app

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
