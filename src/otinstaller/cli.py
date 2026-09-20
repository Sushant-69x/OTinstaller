"""CLI entry point."""

from __future__ import annotations

import json
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from otinstaller import __version__
from otinstaller.registry import (
    RegistryError,
    default_registry_path,
    find_tool,
    load_registry,
    search_tools,
    suggest_names,
)

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


def _load_registry(verbose: bool) -> list:
    try:
        path = default_registry_path()
        if verbose:
            typer.echo(f"Using registry: {path}", err=True)
        return load_registry(path)
    except RegistryError as e:
        typer.echo(f"error: {e}", err=True)
        raise typer.Exit(code=1) from e


def _make_console(no_color: bool) -> Console:
    return Console(color_system=None if no_color else "auto")


def _print_table(console: Console, tools: list, json_output: bool) -> None:
    if json_output:
        data = [
            {
                "name": t.name,
                "display_name": t.display_name,
                "description": t.description,
                "tier": t.tier,
                "capabilities": list(t.capabilities),
            }
            for t in tools
        ]
        typer.echo(json.dumps(data))
        return

    if not tools:
        typer.echo("no tools in the registry")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Name")
    table.add_column("Tier")
    table.add_column("Description")
    for tool in tools:
        table.add_row(tool.name, tool.tier, tool.description)
    console.print(table)
    typer.echo(f"{len(tools)} tools")


@app.command(name="list")
def list_tools(
    installed: Annotated[
        bool,
        typer.Option("--installed", help="List only installed tools"),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", help="Verbose output")] = False,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colored output")] = False,
):
    """List available tools."""
    if installed:
        typer.echo("not implemented yet")
        raise typer.Exit(code=2)

    tools = _load_registry(verbose)
    console = _make_console(no_color)
    _print_table(console, tools, json_output)


@app.command()
def search(
    query: Annotated[list[str], typer.Argument(help="Search query words")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", help="Verbose output")] = False,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colored output")] = False,
):
    """Search for tools."""
    tools = _load_registry(verbose)
    console = _make_console(no_color)

    query_str = " ".join(query)
    results = search_tools(tools, query_str)

    if json_output:
        data = [
            {
                "name": t.name,
                "display_name": t.display_name,
                "description": t.description,
                "tier": t.tier,
                "capabilities": list(t.capabilities),
            }
            for t in results
        ]
        typer.echo(json.dumps(data))
        return

    if not results:
        typer.echo(f"no tools match '{query_str}'")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Name")
    table.add_column("Tier")
    table.add_column("Description")
    for tool in results:
        table.add_row(tool.name, tool.tier, tool.description)
    console.print(table)
    typer.echo(f"{len(results)} tools")


@app.command()
def info(
    tool_name: Annotated[str, typer.Argument(help="Tool name")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", help="Verbose output")] = False,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colored output")] = False,
):
    """Show tool information."""
    tools = _load_registry(verbose)

    tool = find_tool(tools, tool_name)
    if not tool:
        suggestions = suggest_names(tools, tool_name)
        msg = f"error: unknown tool '{tool_name}'"
        if suggestions:
            msg += f"\ndid you mean: {', '.join(suggestions)}?"
        typer.echo(msg, err=True)
        raise typer.Exit(code=1)

    if json_output:
        from dataclasses import asdict

        typer.echo(json.dumps(asdict(tool), default=str))
        return

    console = _make_console(no_color)

    lines = []
    lines.append(f"{tool.display_name} ({tool.name})")
    lines.append(tool.description)
    lines.append(f"Tier: {tool.tier}")

    if tool.repo:
        lines.append(f"Repo: {tool.repo}")
    if tool.license:
        lines.append(f"License: {tool.license}")

    if tool.install.method == "pip":
        pkg = tool.install.package or ""
        ver = f" ({tool.install.version})" if tool.install.version else ""
        lines.append(f"Install: pip {pkg}{ver}")
    else:
        lines.append(f"Install: git {tool.install.url}")
        if tool.install.ref:
            lines.append(f"Ref: {tool.install.ref}")
        if tool.install.requirements:
            lines.append(f"Requirements: {tool.install.requirements}")
        if tool.install.as_package:
            lines.append("As package: yes")

    if tool.entrypoint.command:
        lines.append(f"Entrypoint: {tool.entrypoint.command}")
    elif tool.entrypoint.script:
        lines.append(f"Entrypoint: {tool.entrypoint.script}")

    if tool.capabilities:
        lines.append(f"Capabilities: {', '.join(tool.capabilities)}")

    api_keys = []
    if tool.api_keys.required:
        api_keys.append(f"required: {', '.join(tool.api_keys.required)}")
    if tool.api_keys.optional:
        api_keys.append(f"optional: {', '.join(tool.api_keys.optional)}")
    if api_keys:
        lines.append(f"API keys: {'; '.join(api_keys)}")
    else:
        lines.append("API keys: none")

    if tool.verified:
        lines.append(
            f"Verified: {tool.verified.date} with version {tool.verified.version} "
            f"on {tool.verified.os}, python {tool.verified.python}"
        )
    else:
        lines.append("Not verified yet")

    if "dual-use" in tool.capabilities:
        lines.append("Dual-use tool. See the responsible use notice in the README.")

    for line in lines:
        console.print(line)


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
