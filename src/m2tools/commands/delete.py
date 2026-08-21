import shutil
from pathlib import Path

import typer

from m2tools.core.index import load_index
from m2tools.core.repo import (
    DEFAULT_VERSION,
    default_repo,
    find_artifact_dirs,
    matching_version_dirs,
)


def complete_app(ctx: typer.Context, incomplete: str):
    return [name for name in load_index()["artifacts"] if name.startswith(incomplete)]


def complete_version(ctx: typer.Context, incomplete: str):
    versions = load_index()["versions"].get(ctx.params.get("app_name"), [])
    matches = [v for v in versions if v.startswith(incomplete)]
    if not matches and DEFAULT_VERSION.startswith(incomplete):
        # Typer/Click fall back to full filesystem completion when a
        # completer returns nothing, which is a confusing result for an
        # app with no locally-built versions. Suggesting the tool's own
        # default is harmless -- `delete` still validates it for real.
        return [DEFAULT_VERSION]
    return matches


def delete(
    app_name: str = typer.Argument(
        ...,
        metavar="APP",
        help="Artifact/application name (the Maven artifactId)",
        autocompletion=complete_app,
    ),
    version: str = typer.Argument(
        DEFAULT_VERSION,
        help=f"Version prefix to delete (default: {DEFAULT_VERSION})",
        autocompletion=complete_version,
    ),
    repo: Path = typer.Option(
        default_repo(),
        "--repo",
        help="Path to the local Maven repository (default: $M2_REPO or ~/.m2/repository)",
    ),
    dry_run: bool = typer.Option(
        False, "-n", "--dry-run", help="Show what would be deleted without deleting anything"
    ),
):
    """Delete a specific version (snapshot) of a Java application from the local Maven repository."""
    repo = repo.expanduser()
    if not repo.is_dir():
        typer.secho(f"Repository path not found: {repo}", err=True, fg=typer.colors.RED)
        raise typer.Exit(1)

    app_dirs = find_artifact_dirs(repo, app_name)
    if not app_dirs:
        typer.secho(
            f"No artifact directory named '{app_name}' found under {repo}",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    deleted_any = False
    for app_dir in app_dirs:
        for version_dir in matching_version_dirs(app_dir, version):
            deleted_any = True
            if dry_run:
                typer.echo(f"Would delete: {version_dir}")
            else:
                typer.echo(f"Deleting: {version_dir}")
                shutil.rmtree(version_dir)

    if not deleted_any:
        typer.secho(
            f"No matching version found for '{app_name}' ({version}*) under {repo}",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
