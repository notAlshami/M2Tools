# m2tools

A small, growing collection of CLI tools for managing a local Maven
repository (`~/.m2/repository`). No more `cd`-ing into `~/.m2/repository`
and hand-crafting an `rm -rf */1.0*` to clear out a stale snapshot.

Currently ships one command, `delete`, with room to grow into more.

## Install

```sh
git clone git@github.com:notAlshami/M2Tools.git
pipx install -e ./M2Tools
```

(or `pip install -e .` from this directory, ideally inside a virtualenv)

## Usage

```sh
m2tools delete <app-name> [version=1.0-SNAPSHOT] [--repo PATH] [--dry-run]
```

Finds `<app-name>` under `~/.m2/repository` (or `$M2_REPO`, or `--repo`) and
deletes any version directory whose name starts with `<version>` (default
`1.0-SNAPSHOT`).

Examples:

```sh
m2tools delete my-app                  # deletes .../my-app/1.0-SNAPSHOT*
m2tools delete my-app 2.3              # deletes .../my-app/2.3*
m2tools delete my-app 1.0-SNAPSHOT -n  # dry run, just prints what would be deleted
```

## Shell completion

Tab-completion for `<app-name>` and `[version]` searches your local Maven
repository live, so it always reflects what's actually installed.

One-time setup:

```sh
m2tools --install-completion
```

Reload your shell, then `m2tools delete <TAB>` lists artifact names found in
the repo, and `m2tools delete my-app <TAB>` lists that artifact's available
versions.

## Project layout

```
src/m2tools/
├── __main__.py     # `python -m m2tools` entry point
├── cli.py           # root Typer app, registers commands
├── commands/        # one module per subcommand
│   └── delete.py
└── core/             # business logic, independent of the CLI framework
    └── repo.py
tests/                # mirrors src/m2tools/
```

## Development

```sh
pip install -e ".[dev]"
pytest
```
