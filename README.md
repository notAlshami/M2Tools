# m2tools

A small, growing collection of CLI tools for managing a local Maven
repository (`~/.m2/repository`). No more `cd`-ing into `~/.m2/repository`
and hand-crafting an `rm -rf */1.0*` to clear out a stale snapshot.

Ships `delete`, `reindex`, and `uninstall`, with room to grow into more.

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

`delete`'s app-name and version completion is powered by a cached index
(`~/.cache/m2tools/index.json`, refreshed daily), not by walking
`~/.m2/repository` live on every keystroke — that repo can hold thousands
of entries, which makes a live walk on every TAB press too slow to be
usable.

The index has two parts:
- **Project names**: found by scanning `$HOME` for `pom.xml` files and
  reading each project's own (parent) `artifactId`, stopping at the first
  `pom.xml` per directory tree so submodules of a multi-module project
  don't explode the list into hundreds of entries.
- **Versions**: an artifactId → version-list map, built by one walk of
  `~/.m2/repository`.

One-time setup:

```sh
m2tools --install-completion
```

Reload your shell, then `m2tools delete <TAB>` lists indexed project
names, and `m2tools delete my-app <TAB>` lists that project's available
versions.

If you've just cloned or created a new project and don't want to wait for
the daily refresh:

```sh
m2tools reindex
```

## Uninstall

```sh
m2tools uninstall
```

Removes the completion cache and shell completion files/rc lines, then
uninstalls the CLI itself via `pipx`. Plain `pipx uninstall m2tools` also
works, but leaves the cache and completion files behind — there's no such
thing as a pip/pipx "on-uninstall" hook, so cleaning those up requires
going through this command instead.

## Project layout

```
src/m2tools/
├── __main__.py            # `python -m m2tools` entry point
├── cli.py                  # root Typer app, registers commands
├── completion_support.py   # OptionSuggestingCommand (see below)
├── commands/                # one module per subcommand (thin routers)
│   ├── delete.py
│   ├── reindex.py
│   └── uninstall.py
└── core/                     # business logic, independent of the CLI framework
    ├── repo.py                 # reads the actual ~/.m2/repository (live)
    ├── index.py                 # cached project/version index (for completion)
    └── cleanup.py                 # removes completion files/cache/rc lines
tests/                          # mirrors src/m2tools/
```

`completion_support.OptionSuggestingCommand` works around a Click default:
option flags (`--repo`, `--dry-run`, ...) are normally only suggested once
you've typed a leading `-`. Once both of `delete`'s positional arguments
are already filled, a bare TAB then has nothing left to complete under
that rule and falls through to the shell's native file completion — a
confusing directory dump. This suggests the remaining options instead in
that specific case.

## Development

```sh
pip install -e ".[dev]"
pytest
```
