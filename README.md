# Cryptocurrency Market Data MCP Server

A Model Context Protocol (MCP) server that provides real-time and historical cryptocurrency market data through integration with major exchanges. This server enables LLMs like Claude to fetch current prices, analyze market trends, and access detailed trading information.

[![MCP](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org)
[![CCXT](https://img.shields.io/badge/CCXT-Powered-green)](https://github.com/ccxt/ccxt)

## Features

- **Real-time Market Data**
  - Current cryptocurrency prices
  - Market summaries with bid/ask spreads
  - Top trading pairs by volume
  - Multiple exchange support

- **Historical Analysis**
  - OHLCV (candlestick) data
  - Price change statistics
  - Volume history tracking
  - Customizable timeframes

- **Exchange Support**
  - Binance
  - Coinbase
  - Kraken
  - KuCoin
  - HyperLiquid
  - Huobi
  - Bitfinex
  - Bybit
  - OKX
  - MEXC

## Installation

```bash
# Using uv (recommended)
uv pip install mcp ccxt

# Using pip
pip install mcp ccxt
```

## Usage

### Running the Server

```bash
python crypto_server.py
```

### Connecting with Claude Desktop

1. Open your Claude Desktop configuration at:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the server configuration:

```json
{
    "mcpServers": {
        "crypto": {
            "command": "python",
            "args": ["/path/to/crypto_server.py"]
        }
    }
}
```

3. Restart Claude Desktop

### Available Tools

1. **get-price**
   - Get current price for any trading pair
   - Example: "What's the current price of BTC/USDT on Binance?"

2. **get-market-summary**
   - Fetch detailed market information
   - Example: "Show me a market summary for ETH/USDT"

3. **get-top-volumes**
   - List top trading pairs by volume
   - Example: "What are the top 5 trading pairs on Kraken?"

4. **list-exchanges**
   - Show all supported exchanges
   - Example: "Which exchanges are supported?"

5. **get-historical-ohlcv**
   - Get historical candlestick data
   - Example: "Show me the last 7 days of BTC/USDT price data in 1-hour intervals"

6. **get-price-change**
   - Calculate price changes over different timeframes
   - Example: "What's the 24-hour price change for SOL/USDT?"

7. **get-volume-history**
   - Track trading volume over time
   - Example: "Show me the trading volume history for ETH/USDT over the last week"

### Example Queries

Here are some example questions you can ask Claude once the server is connected:

```
- What's the current Bitcoin price on Binance?
- Show me the top 5 trading pairs by volume on Coinbase
- How has ETH/USDT performed over the last 24 hours?
- Give me a detailed market summary for SOL/USDT on Kraken
- What's the trading volume history for BNB/USDT over the last week?
```

## Technical Details

### Dependencies

- `mcp`: Model Context Protocol SDK
- `ccxt`: Cryptocurrency Exchange Trading Library
- Python 3.9 or higher

### Architecture

The server uses:
- CCXT's async support for efficient exchange communication
- MCP's tool system for LLM integration
- Standardized data formatting for consistent outputs
- Connection pooling for optimal performance

### Error Handling

The server implements robust error handling for:
- Invalid trading pairs
- Exchange connectivity issues
- Rate limiting
- Malformed requests
- Network timeouts

## Development

### Running Tests

```bash
# To be implemented
pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### Local Development

```bash
# Clone the repository
git clone [repository-url]
cd crypto-mcp-server

# Install dependencies
uv pip install -e .
```

## Troubleshooting

### Common Issues

1. **Exchange Connection Errors**
   - Check your internet connection
   - Verify the exchange is operational
   - Ensure the trading pair exists on the selected exchange

2. **Rate Limiting**
   - Implement delays between requests
   - Use different exchanges for high-frequency queries
   - Check exchange-specific rate limits

3. **Data Formatting Issues**
   - Verify trading pair format (e.g., BTC/USDT, not BTCUSDT)
   - Check timeframe specifications
   - Ensure numerical parameters are within valid ranges

## License

MIT License - See LICENSE file for details

## Acknowledgments

- [CCXT](https://github.com/ccxt/ccxt) for exchange integrations
- [Model Context Protocol](https://modelcontextprotocol.io) for the MCP specification
- The cryptocurrency exchanges for providing market data APIs
