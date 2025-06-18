# Contextify

A Python CLI tool that automatically converts ARC-56 smart contract specifications into Model Context Protocol (MCP) servers, enabling AI agents to interact with Algorand smart contracts.

## Features

- ✅ Parses ARC-56 JSON specifications
- ✅ Generates fully functional MCP servers with FastMCP
- ✅ Supports delegated logic signature accounts for transaction signing
- ✅ Includes both read-only and write operations
- ✅ Provides state inspection tools (global and local state)
- ✅ Ready-to-use UV-based project structure
- ✅ Type-safe Python code generation with proper ABI handling

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd contextify

# Install with uv
uv sync
```

## Usage

### Basic Usage

```bash
# Convert an ARC-56 specification to MCP server
contextify path/to/contract.arc56.json

# Specify output directory
contextify path/to/contract.arc56.json --output-dir ./generated-servers

# Verbose output
contextify path/to/contract.arc56.json --verbose
```

### Example Workflow

1. **Generate MCP Server:**
```bash
contextify ZeroCouponBond.arc56.json --output-dir ./servers
```

2. **Navigate to generated project:**
```bash
cd servers/zerocouponbond_mcp
uv sync
```

3. **Use the MCP server in your AI application:**
```python
# The generated server includes tools like:
# - initialize_connection()
# - get_contract_info()
# - get_application_state()
# - All contract methods as individual tools
```

## Generated MCP Server Features

Each generated MCP server includes:

### Core Tools
- `initialize_connection()`: Set up Algorand network connection with delegated account
- `get_contract_info()`: Retrieve contract metadata and available methods
- `get_application_state()`: Read global state of the smart contract
- `get_account_local_state()`: Read account-specific local state

### Contract-Specific Tools
- One tool per contract method (e.g., `asset_transfer()`, `pay_principal()`)
- Automatic type conversion from ABI types to Python types
- Support for both simulation and execution modes
- Proper error handling and transaction result reporting

### Example Generated Tool
```python
@mcp.tool()
def asset_transfer(
    asset_id: int,
    receiver: str,
    amount: int,
    simulate_only: bool = False
) -> Dict[str, Any]:
    """Transfer assets to specified receiver
    
    Args:
        asset_id (uint64): The asset to transfer
        receiver (address): Recipient address
        amount (uint64): Amount to transfer
    """
    # Implementation handles ABI encoding, transaction composition, and execution
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   ARC-56 JSON   │───▶│  Parser & CodeGen │───▶│   MCP Server    │
│  Specification  │    │                  │    │   (FastMCP)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  Jinja2 Template │    │  AI Agent Tools │
                       │    Generation    │    │ (Contract Calls) │
                       └──────────────────┘    └─────────────────┘
```

## Project Structure

```
contextify/
├── src/contextify/
│   ├── __init__.py
│   ├── cli.py                 # Click-based CLI interface
│   ├── arc56_parser.py        # ARC-56 JSON parser with Pydantic models
│   ├── code_generator.py      # MCP server code generator
│   └── templates/
│       └── mcp_server.py.j2   # Jinja2 template for MCP server
├── pyproject.toml             # UV project configuration
└── README.md
```

## Generated Project Structure

```
{contract_name}_mcp/
├── src/{contract_name}_mcp/
│   ├── __init__.py
│   └── server.py              # Generated MCP server
├── pyproject.toml             # Project dependencies
└── README.md                  # Usage instructions
```

## Configuration

The generated MCP server requires initialization with:

```python
initialize_connection(
    algod_token="your_algod_token",           # Algorand node API token
    algod_server="https://testnet-api.algonode.cloud",  # Node URL
    delegated_private_key="your_private_key", # Delegated account private key
    app_id=123456789                          # Smart contract application ID
)
```

## Security Considerations

- **Delegated Accounts**: The tool uses delegated logic signature accounts for transaction signing
- **Private Key Handling**: Private keys are handled securely and never logged
- **Network Isolation**: Supports different Algorand networks (MainNet, TestNet, BetaNet)
- **Transaction Simulation**: All methods support simulation mode for safe testing

## Supported ABI Types

| ABI Type | Python Type | Description |
|----------|-------------|-------------|
| `uint64`, `uint32`, `uint16`, `uint8` | `int` | Unsigned integers |
| `bool` | `bool` | Boolean values |
| `address`, `account` | `str` | Algorand addresses |
| `string` | `str` | UTF-8 strings |
| `byte[]` | `bytes` | Byte arrays |
| `asset` | `int` | Asset IDs |
| `application` | `int` | Application IDs |
| `type[]` | `List[type]` | Dynamic arrays |
| `type[N]` | `List[type]` | Fixed-size arrays |

## Requirements

- Python 3.8+
- UV package manager
- Algorand Python SDK
- MCP Python SDK
- Click for CLI interface
- Jinja2 for code generation
- Pydantic for data validation

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Related Projects

- [ARC-56 Specification](https://arc.algorand.foundation/ARCs/arc-0056)
- [Model Context Protocol](https://github.com/modelcontextprotocol/python-sdk)
- [Algorand Python SDK](https://github.com/algorand/py-algorand-sdk)
- [MakerX AI Agents](https://github.com/Algorand-Developer-Retreat/makerx-ai-agents)
- [Algorand MCP](https://github.com/GoPlausible/algorand-mcp)
