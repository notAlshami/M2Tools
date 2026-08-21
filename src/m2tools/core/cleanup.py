from pathlib import Path
import shutil

ZSH_BOOTSTRAP_LINE = "fpath+=~/.zfunc; autoload -Uz compinit; compinit"
BASH_SOURCE_LINE = "source '~/.bash_completions/m2tools.sh'"


def remove_rc_line(rc_path: Path, line: str) -> bool:
    if not rc_path.is_file():
        return False
    lines = rc_path.read_text().splitlines(keepends=True)
    kept = [entry for entry in lines if entry.strip() != line]
    if len(kept) == len(lines):
        return False
    rc_path.write_text("".join(kept))
    return True


def remove_completion_and_cache(home: Path):
    """Remove m2tools' completion files, cache, and the rc lines that load them.

    The zsh bootstrap line (`fpath+=~/.zfunc; ...`) is generic -- other tools
    could rely on it too -- so it's only removed if `~/.zfunc` becomes empty
    once `_m2tools` itself is gone. The bash line is m2tools-specific and
    always safe to remove once its completion script is deleted.

    Returns a list of human-readable strings describing what was removed,
    for the caller to report back to the user.
    """
    removed = []

    cache_dir = home / ".cache" / "m2tools"
    if cache_dir.is_dir():
        shutil.rmtree(cache_dir)
        removed.append(str(cache_dir))

    zfunc_file = home / ".zfunc" / "_m2tools"
    if zfunc_file.is_file():
        zfunc_file.unlink()
        removed.append(str(zfunc_file))
        zfunc_dir = zfunc_file.parent
        if zfunc_dir.is_dir() and not any(zfunc_dir.iterdir()):
            zfunc_dir.rmdir()
            if remove_rc_line(home / ".zshrc", ZSH_BOOTSTRAP_LINE):
                removed.append(f"{ZSH_BOOTSTRAP_LINE!r} from {home / '.zshrc'}")

    bash_completion_file = home / ".bash_completions" / "m2tools.sh"
    if bash_completion_file.is_file():
        bash_completion_file.unlink()
        removed.append(str(bash_completion_file))
        if remove_rc_line(home / ".bashrc", BASH_SOURCE_LINE):
            removed.append(f"{BASH_SOURCE_LINE!r} from {home / '.bashrc'}")
        bash_completions_dir = bash_completion_file.parent
        if bash_completions_dir.is_dir() and not any(bash_completions_dir.iterdir()):
            bash_completions_dir.rmdir()

    return removed
