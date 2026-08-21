import typer

from m2tools.core.index import build_index


def reindex():
    """Rebuild the project and version index used for `delete`'s completion."""
    data = build_index()
    version_count = sum(len(v) for v in data["versions"].values())
    typer.echo(f"Indexed {len(data['artifacts'])} project(s), {version_count} version(s).")
