from pathlib import Path
import subprocess

import typer

from m2tools.core.cleanup import remove_completion_and_cache


def uninstall(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the confirmation prompt"),
):
    """Remove m2tools completion files and cache, then uninstall the CLI via pipx."""
    if not yes:
        typer.confirm(
            "This removes m2tools completion, its cache, and uninstalls the CLI via pipx. Continue?",
            abort=True,
        )

    for item in remove_completion_and_cache(Path.home()):
        typer.echo(f"Removed {item}")

    typer.echo("Uninstalling the m2tools package via pipx...")
    subprocess.run(["pipx", "uninstall", "m2tools"], check=False)
