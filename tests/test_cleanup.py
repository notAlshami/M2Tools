from m2tools.core.cleanup import BASH_SOURCE_LINE, ZSH_BOOTSTRAP_LINE, remove_completion_and_cache


def test_removes_cache_dir(tmp_path):
    cache_dir = tmp_path / ".cache" / "m2tools"
    cache_dir.mkdir(parents=True)
    (cache_dir / "index.json").touch()

    removed = remove_completion_and_cache(tmp_path)

    assert not cache_dir.exists()
    assert str(cache_dir) in removed


def test_removes_zfunc_file_and_dir_and_rc_line_when_dir_becomes_empty(tmp_path):
    zfunc_dir = tmp_path / ".zfunc"
    zfunc_dir.mkdir()
    (zfunc_dir / "_m2tools").touch()
    (tmp_path / ".zshrc").write_text(f"some other line\n{ZSH_BOOTSTRAP_LINE}\nanother line\n")

    remove_completion_and_cache(tmp_path)

    assert not zfunc_dir.exists()
    zshrc_content = (tmp_path / ".zshrc").read_text()
    assert ZSH_BOOTSTRAP_LINE not in zshrc_content
    assert "some other line" in zshrc_content
    assert "another line" in zshrc_content


def test_keeps_zfunc_dir_and_rc_line_when_other_completions_remain(tmp_path):
    zfunc_dir = tmp_path / ".zfunc"
    zfunc_dir.mkdir()
    (zfunc_dir / "_m2tools").touch()
    (zfunc_dir / "_othertool").touch()
    (tmp_path / ".zshrc").write_text(f"{ZSH_BOOTSTRAP_LINE}\n")

    remove_completion_and_cache(tmp_path)

    assert zfunc_dir.is_dir()
    assert not (zfunc_dir / "_m2tools").exists()
    assert (zfunc_dir / "_othertool").exists()
    assert ZSH_BOOTSTRAP_LINE in (tmp_path / ".zshrc").read_text()


def test_removes_bash_completion_file_and_rc_line_and_empty_dir(tmp_path):
    bash_dir = tmp_path / ".bash_completions"
    bash_dir.mkdir()
    (bash_dir / "m2tools.sh").touch()
    (tmp_path / ".bashrc").write_text(f"some line\n{BASH_SOURCE_LINE}\n")

    remove_completion_and_cache(tmp_path)

    assert not bash_dir.exists()
    bashrc_content = (tmp_path / ".bashrc").read_text()
    assert BASH_SOURCE_LINE not in bashrc_content
    assert "some line" in bashrc_content


def test_nothing_present_is_a_no_op(tmp_path):
    assert remove_completion_and_cache(tmp_path) == []
