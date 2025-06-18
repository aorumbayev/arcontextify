<div align="center">
<a href="https://ibb.co/Q3xMZjN2"><img src="https://i.ibb.co/nNKjT8cH/logo.png" alt="logo" border="0" width="60%"></a>
</div>

---

Convert ARC-56 smart contracts to MCP servers for AI agent integration.

## Features

- 🔄 Converts ARC-56 specs to MCP servers
- 🛡️ Secure environment-based configuration  
- 🎯 Call type filtering (readonly/write-only/both)
- 🧪 Simulation mode for safe testing
- ⚡ AlgoKit Utils integration
- 📦 UV-based project generation

## Installation

```bash
git clone <repo-url>
cd arcontextify
uv sync
```

## Usage

```bash
# Generate MCP server
arcontextify contract.arc56.json

# Readonly calls only (no private key needed)
arcontextify contract.arc56.json --call-types readonly

# Write calls only 
arcontextify contract.arc56.json --call-types write-only

# Custom output directory
arcontextify contract.arc56.json --output-dir ./servers
```

## Generated Server

Each server includes:

### Environment Variables
```bash
export ALGORAND_ALGOD_TOKEN="your-token"
export ALGORAND_ALGOD_SERVER="https://testnet-api.algonode.cloud"  
export ALGORAND_APP_ID="123456"
export ALGORAND_DELEGATED_PRIVATE_KEY="your-key"  # Not needed for readonly
```

### Claude Desktop Config
```json
{
  "mcpServers": {
    "contract_mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.contract_mcp"],
      "cwd": "/path/to/contract_mcp",
      "env": {
        "ALGORAND_ALGOD_TOKEN": "your-token",
        "ALGORAND_ALGOD_SERVER": "https://testnet-api.algonode.cloud",
        "ALGORAND_APP_ID": "123456"
      }
    }
  }
}
```

### Available Tools
- `verify_environment_setup()` - Check configuration
- `get_connection_info()` - Connection status  
- `get_application_state()` - Global state
- `get_account_local_state(address)` - Local state
- Contract methods with simulation support

## Security

- Environment-based secrets (no hardcoded keys)
- Dummy accounts for readonly operations
- Transaction simulation for safe testing
- Address validation and input sanitization

## Requirements

- Python 3.10+
- UV package manager
- AlgoKit Utils 2.0+

## License

MIT
