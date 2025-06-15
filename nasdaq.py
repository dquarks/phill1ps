import yfinance as yf

TOP_10_TICKERS = [
    "AAPL",  # Apple Inc.
    "MSFT",  # Microsoft Corporation
    "AMZN",  # Amazon.com, Inc.
    "NVDA",  # NVIDIA Corporation
    "GOOGL", # Alphabet Inc. (Class A)
    "META",  # Meta Platforms, Inc.
    "TSLA",  # Tesla, Inc.
    "AVGO",  # Broadcom Inc.
    "PEP",   # PepsiCo, Inc.
    "COST"   # Costco Wholesale Corporation
]


def get_latest_prices(tickers):
    """Return a dict of the latest stock prices for the given tickers."""
    prices = {}
    for symbol in tickers:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            price = info.get("last_price")
            prices[symbol] = price
        except Exception:
            prices[symbol] = None
    return prices


def main():
    prices = get_latest_prices(TOP_10_TICKERS)
    for symbol in TOP_10_TICKERS:
        price = prices.get(symbol)
        if price is not None:
            print(f"{symbol}: ${price:.2f}")
        else:
            print(f"{symbol}: price not available")


if __name__ == "__main__":
    main()
