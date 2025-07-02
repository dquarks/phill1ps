# Basic 0DTE Options Trading Tool (Tech Sector) with Free Options Chain Filtering
# Requirements: yfinance, pandas, ta, schedule

import yfinance as yf
import pandas as pd
import warnings

# Suppress the auto_adjust FutureWarning in case older versions of yfinance
# are installed. We explicitly set auto_adjust below, so the warning is
# redundant.
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message="YF.download() has changed argument auto_adjust default",
)

from datetime import datetime

# Define tech tickers
TECH_TICKERS = ["NVDA", "AMD", "AMZN", "META", "TSLA"]

# Parameters for signal detection
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
BREAKOUT_THRESHOLD = 0.5  # % change in price to consider breakout

# Options filtering thresholds
MIN_VOLUME = 100           # minimum options volume
MIN_OPEN_INTEREST = 100    # minimum open interest
MAX_MONEYNESS = 0.1        # max moneyness (10%) for OTM selection
MIN_IV = 0.5               # minimum implied volatility (50%)

# Fetch 5-minute intraday data
def fetch_intraday_data(ticker):
    # Explicitly set auto_adjust to False to avoid FutureWarning in newer
    # yfinance versions where the default has changed to True.
    data = yf.download(
        ticker,
        period="1d",
        interval="5m",
        progress=False,
        auto_adjust=False,
    )
    return data

# Fetch options chain for expirations within 0-1 DTE
def fetch_options_chain(ticker):
    tk = yf.Ticker(ticker)
    exps = tk.options
    today = datetime.now().date()
    valid_exps = [exp for exp in exps if abs((pd.to_datetime(exp).date() - today).days) <= 1]
    chains = []
    for exp in valid_exps:
        opt = tk.option_chain(exp)
        calls = opt.calls.copy(); calls["type"] = "call"
        puts  = opt.puts.copy();  puts["type"]  = "put"
        df = pd.concat([calls, puts], ignore_index=True)
        df["expirationDate"] = pd.to_datetime(exp)
        chains.append(df)
    if chains:
        return pd.concat(chains, ignore_index=True)
    return pd.DataFrame()

# Filter for liquid, OTM options near ATM price
def filter_options(chain_df, price):
    if chain_df.empty:
        return chain_df
    chain_df = chain_df.copy()
    # Moneyness as absolute difference from spot
    chain_df["moneyness"] = abs(chain_df.strike - price) / price
    filtered = chain_df[
        (chain_df.volume       >= MIN_VOLUME) &
        (chain_df.openInterest >= MIN_OPEN_INTEREST) &
        (chain_df.impliedVolatility >= MIN_IV) &
        (chain_df.moneyness    <= MAX_MONEYNESS)
    ]
    return filtered

# Detect RSI & breakout signals
def detect_signals(df):
    import ta
    close = df['Close']
    # `ta` expects a Series. If `Close` comes back as a single-column DataFrame
    # squeeze it to 1D before passing to the indicator
    if isinstance(close, pd.DataFrame):
        close = close.squeeze()

    rsi_series = ta.momentum.RSIIndicator(close, window=RSI_PERIOD).rsi()
    returns_series = close.pct_change() * 100

    df['rsi'] = rsi_series
    df['returns'] = returns_series

    # Grab scalar values to avoid evaluating pandas objects in a boolean context
    rsi_value = float(rsi_series.iloc[-1])
    return_percent = float(returns_series.iloc[-1])
    price = float(close.iloc[-1])

    rsi_signal = (
        'buy' if rsi_value < RSI_OVERSOLD
        else 'sell' if rsi_value > RSI_OVERBOUGHT
        else 'neutral'
    )
    breakout_signal = (
        'breakout' if abs(return_percent) > BREAKOUT_THRESHOLD else 'none'
    )

    # `ta` expects a 1D Series; squeeze in case we have a single-column DataFrame
    if isinstance(close, pd.DataFrame):
        close = close.squeeze()
    df['rsi']     = ta.momentum.RSIIndicator(close, window=RSI_PERIOD).rsi()
    df['returns'] = close.pct_change() * 100
    latest = df.iloc[-1]
    return {
        'price': price,
        'rsi_value': rsi_value,
        'return_percent': return_percent,
        'rsi_signal': rsi_signal,
        'breakout_signal': breakout_signal,
    }

# Print alerts
def alert_user(ticker, signals, opts_df):
    print(f"[{datetime.now()}] {ticker}: Price={signals['price']:.2f}, RSI={signals['rsi_value']:.2f}, Return={signals['return_percent']:.2f}%")
    print(f"    Signals: {signals['rsi_signal']}, Breakout: {signals['breakout_signal']}")
    if not opts_df.empty:
        print("    Filtered 0-1 DTE Options:")
        cols = ['contractSymbol','type','strike','expirationDate','lastPrice','bid','ask','volume','openInterest','impliedVolatility']
        print(opts_df[cols].to_string(index=False))
    else:
        print("    No options match filter criteria.")

# Full analysis per ticker
def analyze_ticker(ticker):
    try:
        df = fetch_intraday_data(ticker)
        if df.empty:
            print(f"No data for {ticker}")
            return
        signals = detect_signals(df)
        opts    = fetch_options_chain(ticker)
        filtered_opts = filter_options(opts, signals['price'])
        alert_user(ticker, signals, filtered_opts)
    except Exception as e:
        print(f"Error processing {ticker}: {e}")

# Scheduler job
def run_trading_scan():
    print(f"\n=== Running 0-1 DTE scan at {datetime.now()} ===")
    for ticker in TECH_TICKERS:
        analyze_ticker(ticker)

if __name__ == "__main__":
    print("Starting 0-1 DTE Options Signal Tool...")
    run_trading_scan()
