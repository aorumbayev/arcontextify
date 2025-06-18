"""Code generator for MCP servers from ARC-56 specifications."""

import json
from pathlib import Path
from typing import Any
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .arc56_parser import ARC56Contract, parse_arc56_file


# Type mapping from ABI types to Python types
ABI_TYPE_MAP: dict[str, str] = {
    "uint64": "int",
    "uint32": "int",
    "uint16": "int",
    "uint8": "int",
    "bool": "bool",
    "address": "str",
    "account": "str",
    "string": "str",
    "byte[]": "list[int]",
    "asset": "int",
    "application": "int",
}


def map_abi_type(abi_type: str) -> str:
    """Convert ABI type to Python type annotation."""
    # Handle arrays
    if abi_type.endswith("[]"):
        base_type = abi_type[:-2]
        mapped_type = ABI_TYPE_MAP.get(base_type, "Any")
        return f"list[{mapped_type}]"

    # Handle fixed-size arrays like uint64[5]
    if "[" in abi_type and "]" in abi_type:
        base_type = abi_type.split("[")[0]
        mapped_type = ABI_TYPE_MAP.get(base_type, "Any")
        return f"list[{mapped_type}]"

    return ABI_TYPE_MAP.get(abi_type, "Any")


def python_bool(value: bool) -> str:
    """Convert boolean to proper Python boolean string."""
    return "True" if value else "False"


def serialize_to_python_literal(obj: Any) -> str:
    """Convert Python object to a Python literal representation with proper boolean handling."""
    json_str = json.dumps(obj, indent=None, separators=(",", ":"))
    # Replace JSON literals with Python literals
    python_str = (
        json_str.replace("null", "None")
        .replace("true", "True")
        .replace("false", "False")
    )
    return python_str


def python_identifier(name: str) -> str:
    """Convert a name to a valid Python identifier."""
    # Replace hyphens and other non-alphanumeric characters with underscores
    import re

    # Replace any non-alphanumeric character with underscore
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    # Ensure it doesn't start with a number
    if sanitized and sanitized[0].isdigit():
        sanitized = f"method_{sanitized}"
    # Ensure it's not empty
    if not sanitized:
        sanitized = "method"
    return sanitized


def pretty_serialize_to_python_literal(obj: Any) -> str:
    """Convert Python object to a formatted Python literal representation."""
    json_str = json.dumps(obj, indent=4)
    # Replace JSON literals with Python literals
    python_str = (
        json_str.replace("null", "None")
        .replace("true", "True")
        .replace("false", "False")
    )
    # Indent each line properly for Python code (8 spaces base + 4 more for structure)
    lines = python_str.split("\n")
    indented_lines = []
    for i, line in enumerate(lines):
        if i == 0:
            indented_lines.append(line)  # First line is inline
        else:
            indented_lines.append("        " + line)  # 8 spaces for alignment
    return "\n".join(indented_lines)


def create_mcp_server(
    contract: ARC56Contract,
    output_dir: Path,
    abi_json: dict[str, Any],
    call_types: str = "both",
) -> Path:
    """Generate complete MCP server project structure."""
    project_name = f"{contract.name.lower().replace(' ', '_')}_mcp"
    project_dir = output_dir / project_name

    # Create directory structure
    src_dir = project_dir / "src" / project_name
    src_dir.mkdir(parents=True, exist_ok=True)

    # Setup Jinja2 environment
    template_dir = Path(__file__).parent / "templates"
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["python_type"] = map_abi_type
    env.filters["python_bool"] = python_bool
    env.filters["python_identifier"] = python_identifier
    env.filters["tojson"] = serialize_to_python_literal
    env.filters["to_pretty_json"] = pretty_serialize_to_python_literal

    # Generate server file
    template = env.get_template("mcp_server.py.j2")
    server_content = template.render(
        contract={
            "name": contract.name,
            "description": contract.description,
            "methods": [
                {
                    "name": method.name,
                    "description": method.description,
                    "args": [
                        {
                            "name": arg.name,
                            "type": arg.type,
                            "description": arg.description,
                        }
                        for arg in method.args
                    ],
                    "returns": method.returns,
                    "readonly": method.readonly,
                    "actions": method.actions,
                }
                for method in contract.methods
            ],
        },
        abi_json=abi_json,
        call_types=call_types,
    )

    # Write files
    _write_file(src_dir / "server.py", server_content)
    _write_file(
        src_dir / "__init__.py",
        f'"""MCP Server for {contract.name}."""\n\n__version__ = "0.1.0"\n',
    )
    _write_file(
        project_dir / "pyproject.toml",
        _create_pyproject_toml(project_name, contract.name),
    )
    _write_file(project_dir / "README.md", _create_readme(contract, project_name))

    return project_dir


def _write_file(path: Path, content: str) -> None:
    """Write content to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_pyproject_toml(project_name: str, contract_name: str) -> str:
    """Create pyproject.toml content."""
    return f'''[project]
name = "{project_name}"
version = "0.1.0"
description = "MCP Server for {contract_name}"
authors = [
    {{name = "Generated", email = "generated@example.com"}}
]
license = {{text = "MIT"}}
requires-python = ">=3.10"
dependencies = [
    "mcp[cli]>=1.0.0",
    "algokit-utils>=2.0.0",
]

[project.scripts]
{project_name} = "{project_name}.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
'''


def _create_readme(contract: ARC56Contract, project_name: str) -> str:
    """Create README.md content."""
    readonly_methods = [m for m in contract.methods if m.readonly]
    transaction_methods = [m for m in contract.methods if not m.readonly]

    return f"""# {contract.name} MCP Server

Generated MCP Server for the {contract.name} Algorand smart contract.

## Security Setup

This MCP server uses environment variables for secure configuration. **Never pass private keys or tokens directly in chat.**

### Required Environment Variables

Set these in your MCP client configuration:

```bash
# Algorand node connection
export ALGORAND_ALGOD_TOKEN="your-algod-token"
export ALGORAND_ALGOD_SERVER="https://testnet-api.algonode.cloud"  # or your node URL

# Smart contract details  
export ALGORAND_APP_ID="123456"  # Your application ID

# Account private key (keep secure!)
export ALGORAND_DELEGATED_PRIVATE_KEY="your-private-key-base64"
```

### MCP Client Configuration

For Claude Desktop, add to your `claude_desktop_config.json`:

```json
{{
  "mcpServers": {{
    "{project_name}": {{
      "command": "python",
      "args": ["-m", "{project_name}"],
      "env": {{
        "ALGORAND_ALGOD_TOKEN": "your-algod-token",
        "ALGORAND_ALGOD_SERVER": "https://testnet-api.algonode.cloud",
        "ALGORAND_APP_ID": "123456",
        "ALGORAND_DELEGATED_PRIVATE_KEY": "your-private-key"
      }}
    }}
  }}
}}
```

## Available Tools

### Connection Management
- `verify_environment_setup()` - Check environment variable configuration
- `get_connection_info()` - Get current connection status (no sensitive data)

### State Queries  
- `get_application_state()` - Get global application state
- `get_account_local_state(account_address)` - Get account's local state
- `get_contract_info()` - Get contract metadata

### Contract Methods

{contract.description or ""}

{f"#### Read-Only Methods ({len(readonly_methods)})" if readonly_methods else ""}
{chr(10).join(f"- `{method.name}()` - {method.description or 'No description'}" for method in readonly_methods)}

{f"#### Transaction Methods ({len(transaction_methods)})" if transaction_methods else ""}
{chr(10).join(f"- `{method.name}()` - {method.description or 'No description'}" for method in transaction_methods)}

All methods include a `simulate_only` parameter for safe testing.

## Security Features

✅ **Environment-based configuration** - No secrets in chat  
✅ **Input validation** - Sanitizes and validates all inputs  
✅ **Address validation** - Verifies Algorand address formats  
✅ **Error handling** - Comprehensive error logging  
✅ **Simulation support** - Test transactions safely  
✅ **Type safety** - Strong typing for all parameters  

## Usage Examples

```python
# Check setup
verify_environment_setup()

# Get connection info
get_connection_info()

# Read contract state
get_application_state()

# Simulate a method call (safe)
some_method(param1="value", simulate_only=True)

# Execute a method (requires valid setup)
some_method(param1="value", simulate_only=False)
```

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Format code
uv run black .
uv run ruff check --fix .
```

## License

MIT
"""


def generate_mcp_server(
    arc56_path: str, output_dir: str, call_types: str = "both"
) -> Path:
    """Main function to generate MCP server from ARC-56 specification."""
    contract = parse_arc56_file(arc56_path)

    # Filter methods based on call_types parameter
    if call_types == "readonly":
        contract.methods = [m for m in contract.methods if m.readonly]
    elif call_types == "write-only":
        contract.methods = [m for m in contract.methods if not m.readonly]
    # "both" - no filtering needed

    # Load raw ABI JSON for template
    with open(arc56_path, encoding="utf-8") as f:
        abi_json = json.load(f)

    return create_mcp_server(contract, Path(output_dir), abi_json, call_types)
