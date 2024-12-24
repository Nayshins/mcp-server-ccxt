import asyncio
from typing import Any, Dict, List
import ccxt.async_support as ccxt
import mcp.types as types
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# Initialize server
server = Server("crypto-server")

# Define supported exchanges and their instances
SUPPORTED_EXCHANGES = {
    'binance': ccxt.binance,
    'coinbase': ccxt.coinbase,
    'kraken': ccxt.kraken,
    'kucoin': ccxt.kucoin,
    'ftx': ccxt.hyperliquid,
    'huobi': ccxt.huobi,
    'bitfinex': ccxt.bitfinex,
    'bybit': ccxt.bybit,
    'okx': ccxt.okx,
    'mexc': ccxt.mexc
}

# Exchange instances cache
exchange_instances = {}

async def get_exchange(exchange_id: str) -> ccxt.Exchange:
    """Get or create an exchange instance."""
    exchange_id = exchange_id.lower()
    if exchange_id not in SUPPORTED_EXCHANGES:
        raise ValueError(f"Unsupported exchange: {exchange_id}")

    if exchange_id not in exchange_instances:
        exchange_class = SUPPORTED_EXCHANGES[exchange_id]
        exchange_instances[exchange_id] = exchange_class()

    return exchange_instances[exchange_id]

async def format_ticker(ticker: Dict[str, Any], exchange_id: str) -> str:
    """Format ticker data into a readable string."""
    return (
        f"Exchange: {exchange_id.upper()}\n"
        f"Symbol: {ticker.get('symbol')}\n"
        f"Last Price: {ticker.get('last', 'N/A')}\n"
        f"24h High: {ticker.get('high', 'N/A')}\n"
        f"24h Low: {ticker.get('low', 'N/A')}\n"
        f"24h Volume: {ticker.get('baseVolume', 'N/A')}\n"
        f"Bid: {ticker.get('bid', 'N/A')}\n"
        f"Ask: {ticker.get('ask', 'N/A')}\n"
        "---"
    )

def get_exchange_schema() -> Dict[str, Any]:
    """Get the JSON schema for exchange selection."""
    return {
        "type": "string",
        "description": f"Exchange to use (supported: {', '.join(SUPPORTED_EXCHANGES.keys())})",
        "enum": list(SUPPORTED_EXCHANGES.keys()),
        "default": "binance"
    }

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available cryptocurrency tools."""
    return [
        types.Tool(
            name="get-price",
            description="Get current price of a cryptocurrency pair from a specific exchange",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading pair symbol (e.g., BTC/USDT, ETH/USDT)",
                    },
                    "exchange": get_exchange_schema()
                },
                "required": ["symbol"],
            },
        ),
        types.Tool(
            name="get-market-summary",
            description="Get detailed market summary for a cryptocurrency pair from a specific exchange",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading pair symbol (e.g., BTC/USDT, ETH/USDT)",
                    },
                    "exchange": get_exchange_schema()
                },
                "required": ["symbol"],
            },
        ),
        types.Tool(
            name="get-top-volumes",
            description="Get top cryptocurrencies by trading volume from a specific exchange",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Number of pairs to return (default: 5)",
                    },
                    "exchange": get_exchange_schema()
                }
            },
        ),
        types.Tool(
            name="list-exchanges",
            description="List all supported cryptocurrency exchanges",
            inputSchema={
                "type": "object",
                "properties": {}
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any]
) -> List[types.TextContent]:
    """Handle tool execution requests."""
    try:
        if name == "list-exchanges":
            exchange_list = "\n".join([f"- {ex.upper()}" for ex in SUPPORTED_EXCHANGES.keys()])
            return [
                types.TextContent(
                    type="text",
                    text=f"Supported exchanges:\n\n{exchange_list}"
                )
            ]

        # Get exchange from arguments or use default
        exchange_id = arguments.get("exchange", "binance")
        exchange = await get_exchange(exchange_id)

        if name == "get-price":
            symbol = arguments.get("symbol", "").upper()
            ticker = await exchange.fetch_ticker(symbol)

            return [
                types.TextContent(
                    type="text",
                    text=f"Current price of {symbol} on {exchange_id.upper()}: {ticker['last']} {symbol.split('/')[1]}"
                )
            ]

        elif name == "get-market-summary":
            symbol = arguments.get("symbol", "").upper()
            ticker = await exchange.fetch_ticker(symbol)

            formatted_data = await format_ticker(ticker, exchange_id)
            return [
                types.TextContent(
                    type="text",
                    text=f"Market summary for {symbol}:\n\n{formatted_data}"
                )
            ]

        elif name == "get-top-volumes":
            limit = int(arguments.get("limit", 5))
            tickers = await exchange.fetch_tickers()

            # Sort by volume and get top N
            sorted_tickers = sorted(
                tickers.values(),
                key=lambda x: float(x.get('baseVolume', 0) or 0),
                reverse=True
            )[:limit]

            formatted_results = []
            for ticker in sorted_tickers:
                formatted_data = await format_ticker(ticker, exchange_id)
                formatted_results.append(formatted_data)

            return [
                types.TextContent(
                    type="text",
                    text=f"Top {limit} pairs by volume on {exchange_id.upper()}:\n\n" + "\n".join(formatted_results)
                )
            ]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except ccxt.BaseError as e:
        return [
            types.TextContent(
                type="text",
                text=f"Error accessing cryptocurrency data: {str(e)}"
            )
        ]
    finally:
        # Clean up exchange connections
        for instance in exchange_instances.values():
            await instance.close()
        exchange_instances.clear()


def run_server():
    """Wrapper to run the async main function"""
    asyncio.run(main())



async def main():
    """Run the server using stdin/stdout streams."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="crypto-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())