"""CLI entry point."""

from typing import Annotated

import typer

from otinstaller import __version__

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)


def version_callback(value: bool):
    if value:
        typer.echo(f"otinstaller {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version", callback=version_callback, is_eager=True, help="Show version and exit"
        ),
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", help="Verbose output")] = False,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colored output")] = False,
):
    pass


@app.command()
def install(names: Annotated[list[str], typer.Argument(help="Tool names to install")]):
    """Install tools by name."""
    typer.echo("not implemented yet")
    raise typer.Exit(code=2)


@app.command()
def remove(
    names: Annotated[list[str] | None, typer.Argument(help="Tool names to remove")] = None,
    all_tools: Annotated[bool, typer.Option("--all", help="Remove all installed tools")] = False,
):
    """Remove installed tools."""
    if names is None:
        names = []
    typer.echo("not implemented yet")
    raise typer.Exit(code=2)


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def run(
    tool: Annotated[str, typer.Argument(help="Tool name to run")],
    extra_args: Annotated[list[str] | None, typer.Argument()] = None,
):
    """Run a tool with arguments passed through after --."""
    if extra_args is None:
        extra_args = []
    typer.echo("not implemented yet")
    raise typer.Exit(code=2)


@app.command()
def update(
    names: Annotated[list[str] | None, typer.Argument(help="Tool names to update")] = None,
    all_tools: Annotated[bool, typer.Option("--all", help="Update all installed tools")] = False,
):
    """Update installed tools."""
    if names is None:
        names = []
    typer.echo("not implemented yet")
    raise typer.Exit(code=2)


@app.command()
def list(
    installed: Annotated[
        bool,
        typer.Option("--installed", help="List only installed tools"),
    ] = False,
):
    """List available tools."""
    typer.echo("not implemented yet")
    raise typer.Exit(code=2)


@app.command()
def search(query: Annotated[str, typer.Argument(help="Search query")]):
    """Search for tools."""
    typer.echo("not implemented yet")
    raise typer.Exit(code=2)


@app.command()
def info(tool: Annotated[str, typer.Argument(help="Tool name")]):
    """Show tool information."""
    typer.echo("not implemented yet")
    raise typer.Exit(code=2)


@app.command()
def example(tool: Annotated[str, typer.Argument(help="Tool name")]):
    """Show usage examples for a tool."""
    typer.echo("not implemented yet")
    raise typer.Exit(code=2)


@app.command()
def init():
    """Initialize configuration and directories."""
    typer.echo("not implemented yet")
    raise typer.Exit(code=2)


keys_app = typer.Typer(no_args_is_help=True, help="Manage API keys.")
app.add_typer(keys_app, name="keys")


@keys_app.command("check")
def keys_check():
    """Check API keys configuration."""
    typer.echo("not implemented yet")
    raise typer.Exit(code=2)


@app.command()
def resume():
    """Resume interrupted jobs."""
    typer.echo("not implemented yet")
    raise typer.Exit(code=2)


@app.command()
def doctor():
    """Run diagnostics."""
    typer.echo("not implemented yet")
    raise typer.Exit(code=2)
