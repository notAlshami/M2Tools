import typer

from m2tools.commands.delete import delete

app = typer.Typer(help="CLI tools for managing a local Maven repository.")


@app.callback()
def callback() -> None:
    """CLI tools for managing a local Maven repository."""


app.command("delete")(delete)


def main():
    app()


if __name__ == "__main__":
    main()
