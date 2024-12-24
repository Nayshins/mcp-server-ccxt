import asyncio
from typing import Any, Dict, List
import ccxt.async_support as ccxt
import mcp.types as types
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
from datetime import datetime, timedelta

# Initialize server
server = Server("crypto-server")

# Define supported exchanges and their instances
SUPPORTED_EXCHANGES = {
    'binance': ccxt.binance,
    'coinbase': ccxt.coinbase,
    'kraken': ccxt.kraken,
    'kucoin': ccxt.kucoin,
    'hyperliquid': ccxt.hyperliquid,
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


def format_ohlcv_data(ohlcv_data: List[List], timeframe: str) -> str:
    """Format OHLCV data into a readable string with price changes."""
    formatted_data = []

    for i, candle in enumerate(ohlcv_data):
        timestamp, open_price, high, low, close, volume = candle

        # Calculate price change from previous close if available
        price_change = ""
        if i > 0:
            prev_close = ohlcv_data[i-1][4]
            change_pct = ((close - prev_close) / prev_close) * 100
            price_change = f"Change: {change_pct:+.2f}%"

        # Format the candle data
        dt = datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')
        candle_str = (
            f"Time: {dt}\n"
            f"Open: {open_price:.8f}\n"
            f"High: {high:.8f}\n"
            f"Low: {low:.8f}\n"
            f"Close: {close:.8f}\n"
            f"Volume: {volume:.2f}\n"
            f"{price_change}\n"
            "---"
        )
        formatted_data.append(candle_str)

    return "\n".join(formatted_data)


@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available cryptocurrency tools."""
    return [
        # Market Data Tools
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
        ),
        # Historical Data Tools
        types.Tool(
            name="get-historical-ohlcv",
            description="Get historical OHLCV (candlestick) data for a trading pair",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading pair symbol (e.g., BTC/USDT, ETH/USDT)",
                    },
                    "timeframe": {
                        "type": "string",
                        "description": "Timeframe for candlesticks (e.g., 1m, 5m, 15m, 1h, 4h, 1d)",
                        "enum": ["1m", "5m", "15m", "1h", "4h", "1d"],
                        "default": "1h"
                    },
                    "days_back": {
                        "type": "number",
                        "description": "Number of days of historical data to fetch (default: 7, max: 30)",
                        "default": 7,
                        "maximum": 30
                    },
                    "exchange": get_exchange_schema()
                },
                "required": ["symbol"],
            },
        ),
        types.Tool(
            name="get-price-change",
            description="Get price change statistics over different time periods",
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
            name="get-volume-history",
            description="Get trading volume history over time",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading pair symbol (e.g., BTC/USDT, ETH/USDT)",
                    },
                    "days": {
                        "type": "number",
                        "description": "Number of days of volume history (default: 7, max: 30)",
                        "default": 7,
                        "maximum": 30
                    },
                    "exchange": get_exchange_schema()
                },
                "required": ["symbol"],
            },
        ),
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

        elif name == "get-historical-ohlcv":
            symbol = arguments.get("symbol", "").upper()
            timeframe = arguments.get("timeframe", "1h")
            days_back = min(int(arguments.get("days_back", 7)), 30)

            # Calculate timestamps
            since = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)

            # Fetch historical data
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, since=since)

            formatted_data = format_ohlcv_data(ohlcv, timeframe)
            return [
                types.TextContent(
                    type="text",
                    text=f"Historical OHLCV data for {symbol} ({timeframe}) on {exchange_id.upper()}:\n\n{formatted_data}"
                )
            ]

        elif name == "get-price-change":
            symbol = arguments.get("symbol", "").upper()

            # Get current price
            ticker = await exchange.fetch_ticker(symbol)
            current_price = ticker['last']

            # Get historical prices
            timeframes = {
                "1h": (1, "1h"),
                "24h": (1, "1d"),
                "7d": (7, "1d"),
                "30d": (30, "1d")
            }

            changes = []
            for label, (days, timeframe) in timeframes.items():
                since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
                ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1)
                if ohlcv:
                    start_price = ohlcv[0][1]  # Open price
                    change_pct = ((current_price - start_price) / start_price) * 100
                    changes.append(f"{label} change: {change_pct:+.2f}%")

            return [
                types.TextContent(
                    type="text",
                    text=f"Price changes for {symbol} on {exchange_id.upper()}:\n\n" + "\n".join(changes)
                )
            ]

        elif name == "get-volume-history":
            symbol = arguments.get("symbol", "").upper()
            days = min(int(arguments.get("days", 7)), 30)

            # Get daily volume data
            since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            ohlcv = await exchange.fetch_ohlcv(symbol, "1d", since=since)

            volume_data = []
            for candle in ohlcv:
                timestamp, _, _, _, _, volume = candle
                dt = datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d')
                volume_data.append(f"{dt}: {volume:,.2f}")

            return [
                types.TextContent(
                    type="text",
                    text=f"Daily trading volume history for {symbol} on {exchange_id.upper()}:\n\n" +
                         "\n".join(volume_data)
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


def run_server():
    """Wrapper to run the async main function"""
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
