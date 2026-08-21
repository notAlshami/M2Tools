# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

`m2tools` is a multi-command CLI (Typer-based) for managing a local Maven
repository (`~/.m2/repository`). It's a personal tool, not a company
project — treat it that way (small scope, no enterprise abstractions).

Currently ships one real command, `delete`, plus `reindex` which
maintains the cache `delete`'s shell completion depends on.

## Project layout

```
src/m2tools/
├── __main__.py       # `python -m m2tools` entry point
├── cli.py            # root Typer app, registers commands
├── commands/         # one module per subcommand (thin routers)
│   ├── delete.py
│   └── reindex.py
└── core/             # business logic, independent of the CLI framework
    ├── repo.py        # reads the actual ~/.m2/repository (live, authoritative)
    └── index.py       # cached project/version index (fast, for completion only)
tests/                 # mirrors src/m2tools/
```

Adding a new subcommand: add `commands/<name>.py` (thin, Typer-decorated)
+ any needed logic in `core/`, then register it in `cli.py` with
`app.command("<name>")(<function>)`. Follow `delete`'s pattern.

## The two-tier data model (important)

There are two distinct data sources, used for two distinct purposes —
don't blur them:

- **`core/repo.py`** walks the real `~/.m2/repository` live, on demand.
  This is what `delete` actually uses to decide what exists and what to
  delete. It must always reflect current on-disk truth, never a cache.
- **`core/index.py`** builds a cached index (`~/.cache/m2tools/index.json`,
  1-day TTL, see `DEFAULT_TTL_SECONDS`) used *only* to make shell
  completion fast. It has two parts:
  - `artifacts`: project names found by scanning `$HOME` for `pom.xml`
    files and reading each project's own (parent) `artifactId` — stopping
    at the first `pom.xml` per directory tree, so submodules of a
    multi-module project don't explode the list into hundreds of entries.
  - `versions`: an artifactId → version-list map, built by one `os.walk`
    of `~/.m2/repository` (via `scan_versions_by_artifact`), instead of
    the naive approach of re-`rglob`-ing the whole repo on every keystroke.

**Why this split exists**: early versions matched completion candidates by
walking `~/.m2/repository` directly. That repo can contain tens of
thousands of directories (groupId segments, every module, every version),
so `rglob()` on every TAB press was slow enough that short prefixes like
`pps` would hang for seconds. Switching completion to a cached index
fixed it; `delete` itself still resolves paths live, because deletion is a
one-off action where staleness is a correctness risk, not a per-keystroke
one where staleness is a UX/-non-issue.

If you're asked to speed up or change completion again, extend
`core/index.py`'s cache — don't reintroduce a live repo walk in the
completion path. If you're asked to change what `delete` actually
deletes, that's `core/repo.py` — don't route it through the cache.

## Conventions

- **Never use real project, company, or internal system names** in code,
  tests, docs, or commit messages in this repo — it's public on GitHub.
  Use fictional names (`acme-widget`, `acme-gadget`, `my-app`, etc.) in
  tests and examples, even when reproducing a real bug found against a
  real (excluded) local repository during development.
- Business logic in `core/` should stay independent of Typer/Click —
  `commands/*.py` should stay thin: argument parsing, calling into `core/`,
  formatting output.
- `tests/` mirrors `src/m2tools/` file-for-file.

## Commands

```sh
pip install -e ".[dev]"   # install with dev deps (pytest)
pytest                     # run the full suite (PYTHONPATH=src pytest also works without installing)
pipx install -e . --force  # reinstall the globally-available `m2tools` binary after changes
m2tools reindex             # force-rebuild the completion cache (also happens automatically, daily)
```

## Git workflow

Always confirm with the user before running `git commit` or `git push` —
do not commit or push automatically, even after a series of changes they
seem happy with. This was explicitly requested; standing auto-push
permission was granted once by mistake and immediately revoked.
