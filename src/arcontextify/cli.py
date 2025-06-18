"""CLI interface for ARContextify - ARC-56 to MCP converter."""

import click
from pathlib import Path
from .code_generator import generate_mcp_server


def _print_setup_instructions(project_dir: Path, project_name: str) -> None:
    """Print setup and installation instructions."""
    instructions = [
        "🔧 Setup & Installation:",
        "   # Install the MCP server as a tool",
        f"   uv tool install {project_dir}",
        "",
        "🧪 Local Testing:",
        "   # Test the installed server directly",
        f"   {project_name}_mcp",
        "",
        "   # Test with MCP inspector (install if needed)",
        f"   npx @modelcontextprotocol/inspector {project_name}",
        "",
    ]
    click.echo("\n".join(instructions))


def _print_environment_variables(call_types: str) -> None:
    """Print required environment variables section."""
    if call_types == "readonly":
        env_vars_required = [
            "ALGORAND_ALGOD_TOKEN",
            "ALGORAND_ALGOD_SERVER",
            "ALGORAND_APP_ID",
        ]
        env_note = " (readonly mode - no private key needed)"
    else:
        env_vars_required = [
            "ALGORAND_ALGOD_TOKEN",
            "ALGORAND_ALGOD_SERVER",
            "ALGORAND_APP_ID",
            "ALGORAND_DELEGATED_PRIVATE_KEY",
        ]
        env_note = ""

    env_examples = {
        "ALGORAND_ALGOD_TOKEN": "your-algod-token",
        "ALGORAND_ALGOD_SERVER": "http://localhost",
        "ALGORAND_ALGOD_PORT": "1005",
        "ALGORAND_APP_ID": "your-app-id",
        "ALGORAND_DELEGATED_PRIVATE_KEY": "your-agents-wallet-key-or-mnemonic",
    }

    lines = [f"🔑 Required Environment Variables{env_note}:"]
    for var in env_vars_required:
        lines.append(f'   export {var}="{env_examples[var]}"')
    lines.append("")

    click.echo("\n".join(lines))


def _print_claude_config(project_dir: Path, project_name: str, call_types: str) -> None:
    """Print Claude Desktop configuration."""

    if call_types == "readonly":
        env_vars_required = [
            "ALGORAND_ALGOD_TOKEN",
            "ALGORAND_ALGOD_SERVER",
            "ALGORAND_ALGOD_PORT",
            "ALGORAND_APP_ID",
        ]
    else:
        env_vars_required = [
            "ALGORAND_ALGOD_TOKEN",
            "ALGORAND_ALGOD_SERVER",
            "ALGORAND_ALGOD_PORT",
            "ALGORAND_APP_ID",
            "ALGORAND_DELEGATED_PRIVATE_KEY",
        ]

    env_examples = {
        "ALGORAND_ALGOD_TOKEN": "your-algod-token",
        "ALGORAND_ALGOD_SERVER": "https://testnet-api.algonode.cloud",
        "ALGORAND_ALGOD_PORT": "443",
        "ALGORAND_APP_ID": "123456",
        "ALGORAND_DELEGATED_PRIVATE_KEY": "your-private-key-or-mnemonic",
    }

    env_lines = []
    for i, var in enumerate(env_vars_required):
        comma = "," if i < len(env_vars_required) - 1 else ""
        env_lines.append(f'        "{var}": "{env_examples[var]}"{comma}')

    config_lines = [
        "🤖 Claude Desktop Configuration:",
        "   Add this to your claude_desktop_config.json:",
        "",
        "   {",
        '     "mcpServers": {',
        f'       "{project_name}": {{',
        f'         "command": "{project_name}", // Note that you might need full path to uv tool executable on some systems',
        '         "env": {',
        *[f"   {line}" for line in env_lines],
        "         }",
        "       }",
        "     }",
        "   }",
        "",
    ]

    click.echo("\n".join(config_lines))


def _print_tips() -> None:
    """Print helpful tips."""
    tips = [
        "💡 Tips:",
        "   • Use testnet for development: https://testnet-api.algonode.cloud",
        "   • Test readonly methods without real private keys",
        "   • Use MCP Inspector to debug server responses",
        "   • After uv tool install, restart Claude Desktop to detect the new server",
    ]
    click.echo("\n".join(tips))


def _print_project_structure(project_dir: Path) -> None:
    """Print project structure if verbose mode is enabled."""
    lines = ["\n📁 Project structure:"]
    for path in sorted(project_dir.rglob("*")):
        if path.is_file():
            lines.append(f"  {path.relative_to(project_dir)}")
    click.echo("\n".join(lines))


@click.command()
@click.argument("arc56_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=".",
    help="Output directory",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option(
    "--call-types",
    "-t",
    type=click.Choice(["readonly", "write-only", "both"], case_sensitive=False),
    default="both",
    help="Include only readonly calls, write-only calls, or both (default: both)",
)
def main(arc56_path: Path, output_dir: Path, verbose: bool, call_types: str) -> None:
    """Convert ARC-56 smart contract specification to MCP server."""
    if verbose:
        click.echo(f"Converting: {arc56_path}\nOutput: {output_dir}")

    try:
        project_dir = generate_mcp_server(str(arc56_path), str(output_dir), call_types)
        project_name = project_dir.name

        click.echo(f"✅ Generated MCP server: {project_dir}\n")

        # Print all sections using helper functions
        _print_setup_instructions(project_dir, project_name)
        _print_environment_variables(call_types)
        _print_claude_config(project_dir, project_name, call_types)
        _print_tips()

        if verbose:
            _print_project_structure(project_dir)

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
