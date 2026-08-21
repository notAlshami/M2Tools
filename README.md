# m2tools

CLI tool to delete versioned artifacts from your local Maven repository — no more manually hunting through `~/.m2/repository`.

## Install

```sh
git clone git@github.com:notAlshami/M2Delete.git
pipx install -e ./M2Delete
```

(or `pip install -e .` from this directory, ideally inside a virtualenv)

## Usage

```sh
m2delete <app-name> [version=1.0-SNAPSHOT] [--repo PATH] [--dry-run]
```

Finds `<app-name>` under `~/.m2/repository` (or `$M2_REPO`, or `--repo`) and
deletes any version directory whose name starts with `<version>` (default
`1.0-SNAPSHOT`).

Examples:

```sh
m2delete my-app                  # deletes .../my-app/1.0-SNAPSHOT*
m2delete my-app 2.3              # deletes .../my-app/2.3*
m2delete my-app 1.0-SNAPSHOT -n  # dry run, just prints what would be deleted
```
