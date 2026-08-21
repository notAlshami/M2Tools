import typer

from m2tools.commands.delete import delete
from m2tools.commands.reindex import reindex
from m2tools.commands.uninstall import uninstall
from m2tools.completion_support import OptionSuggestingCommand

app = typer.Typer(help="CLI tools for managing a local Maven repository.")


@app.callback()
def callback() -> None:
    """CLI tools for managing a local Maven repository."""


app.command("delete", cls=OptionSuggestingCommand)(delete)
app.command("reindex")(reindex)
app.command("uninstall")(uninstall)


def main():
    app()


if __name__ == "__main__":
    main()
