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

## Shell completion (zsh)

Tab-completion for `<app-name>` and `[version]` is powered by
[`argcomplete`](https://github.com/kislyuk/argcomplete), searching your local
Maven repository live — so it always reflects what's actually installed.

One-time setup:

```sh
pipx install argcomplete   # or: pip install --user argcomplete
```

Then add to `~/.zshrc`:

```sh
autoload -U bashcompinit && bashcompinit
eval "$(register-python-argcomplete m2delete)"
```

Reload your shell (or `source ~/.zshrc`), then `m2delete <TAB>` lists artifact
names found in the repo, and `m2delete my-app <TAB>` lists that artifact's
available versions.
