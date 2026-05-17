import json
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen


TOP_COMPANIES = [
    {"symbol": "NVDA", "name": "NVIDIA"},
    {"symbol": "MSFT", "name": "Microsoft"},
    {"symbol": "AAPL", "name": "Apple"},
    {"symbol": "AMZN", "name": "Amazon"},
    {"symbol": "META", "name": "Meta Platforms"},
    {"symbol": "GOOGL", "name": "Alphabet"},
]

USER_AGENT = "RiskAI/1.0"
REQUEST_TIMEOUT = 8


def get_stock_history(symbol, range_value="1mo", interval="1d"):
    clean_symbol = symbol.strip().upper()

    if not clean_symbol:
        raise ValueError("Enter a stock symbol.")

    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{quote(clean_symbol)}?range={quote(range_value)}&interval={quote(interval)}"
    )

    try:
        request = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise ValueError("Market data is temporarily unavailable.") from exc

    chart = payload.get("chart", {})
    results = chart.get("result") or []

    if chart.get("error") or not results:
        raise ValueError("No market data found for that symbol.")

    result = results[0]
    meta = result.get("meta", {})
    timestamps = result.get("timestamp") or []
    quote_data = (result.get("indicators", {}).get("quote") or [{}])[0]
    closes = quote_data.get("close") or []

    points = []

    for timestamp, close in zip(timestamps, closes):
        if close is None:
            continue

        points.append({
            "date": datetime.fromtimestamp(
                timestamp,
                tz=timezone.utc
            ).strftime("%b %d"),
            "price": round(float(close), 2),
        })

    if not points:
        raise ValueError("No price history found for that symbol.")

    current_price = meta.get("regularMarketPrice") or points[-1]["price"]
    previous_close = meta.get("chartPreviousClose") or points[0]["price"]
    change = float(current_price) - float(previous_close)
    change_percent = (
        (change / float(previous_close)) * 100
        if previous_close else 0
    )

    return {
        "symbol": meta.get("symbol", clean_symbol),
        "name": meta.get("shortName") or clean_symbol,
        "currency": meta.get("currency", "USD"),
        "price": round(float(current_price), 2),
        "change": round(change, 2),
        "change_percent": round(change_percent, 2),
        "points": points,
    }


def get_top_company_snapshots():
    snapshots = []

    for company in TOP_COMPANIES:
        try:
            data = get_stock_history(company["symbol"], "5d", "1d")
            data["name"] = company["name"]
            snapshots.append(data)
        except ValueError:
            continue

    if not snapshots:
        raise ValueError("Top company data is temporarily unavailable.")

    return sorted(
        snapshots,
        key=lambda item: item["change_percent"],
        reverse=True
    )
