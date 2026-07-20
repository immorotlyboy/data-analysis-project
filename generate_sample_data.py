import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(OUTPUT_DIR, "stock_market.db")

TICKERS = {
    "AAPL": {"name": "Apple Inc.", "sector": "Technology", "base_price": 150.0, "drift": 0.0008, "volatility": 0.02},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "Technology", "base_price": 100.0, "drift": 0.0006, "volatility": 0.022},
    "MSFT": {"name": "Microsoft Corp.", "sector": "Technology", "base_price": 250.0, "drift": 0.0007, "volatility": 0.018},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "Technology", "base_price": 130.0, "drift": 0.0005, "volatility": 0.025},
    "META": {"name": "Meta Platforms", "sector": "Technology", "base_price": 200.0, "drift": 0.0009, "volatility": 0.028},
    "TSLA": {"name": "Tesla Inc.", "sector": "Automotive", "base_price": 200.0, "drift": 0.001, "volatility": 0.04},
    "NVDA": {"name": "NVIDIA Corp.", "sector": "Technology", "base_price": 300.0, "drift": 0.0012, "volatility": 0.035},
    "NFLX": {"name": "Netflix Inc.", "sector": "Entertainment", "base_price": 350.0, "drift": 0.0004, "volatility": 0.03},
}

ANALYSTS = ["Goldman Sachs", "Morgan Stanley", "JP Morgan", "Bank of America", "Citigroup", "Wells Fargo"]
RATINGS = ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]
RATING_WEIGHTS = [0.15, 0.30, 0.35, 0.15, 0.05]


def generate_trading_dates(start_date, num_days):
    dates = pd.bdate_range(start=start_date, periods=num_days)
    return dates


def generate_ohlcv(ticker_info, dates):
    n = len(dates)
    returns = np.random.normal(ticker_info["drift"], ticker_info["volatility"], n)

    market_shock = np.zeros(n)
    shock_indices = np.random.choice(n, size=int(n * 0.05), replace=False)
    market_shock[shock_indices] = np.random.normal(0, 0.03, len(shock_indices))
    returns += market_shock

    log_prices = np.log(ticker_info["base_price"]) + np.cumsum(returns)
    close_prices = np.exp(log_prices)

    intraday_vol = ticker_info["volatility"] * 0.6
    open_prices = close_prices * (1 + np.random.normal(0, intraday_vol * 0.3, n))
    high_prices = np.maximum(open_prices, close_prices) * (1 + np.abs(np.random.normal(0, intraday_vol * 0.5, n)))
    low_prices = np.minimum(open_prices, close_prices) * (1 - np.abs(np.random.normal(0, intraday_vol * 0.5, n)))

    high_prices = np.maximum(high_prices, np.maximum(open_prices, close_prices))
    low_prices = np.minimum(low_prices, np.minimum(open_prices, close_prices))

    base_volume = np.random.randint(10_000_000, 80_000_000)
    volume = np.abs(np.random.normal(base_volume, base_volume * 0.4, n)).astype(int)
    volume[shock_indices] = (volume[shock_indices] * 3).astype(int)

    df = pd.DataFrame({
        "date": dates,
        "ticker": ticker_info["name"].split()[0].upper()[:5],
        "open": np.round(open_prices, 2),
        "high": np.round(high_prices, 2),
        "low": np.round(low_prices, 2),
        "close": np.round(close_prices, 2),
        "volume": volume,
    })

    missing_idx = np.random.choice(n, size=int(n * 0.02), replace=False)
    for idx in missing_idx:
        col = np.random.choice(["open", "close", "volume"])
        df.loc[idx, col] = np.nan

    duplicate_idx = np.random.choice(n, size=3, replace=False)
    for idx in duplicate_idx:
        df = pd.concat([df, df.iloc[[idx]]], ignore_index=True)

    return df.sort_values("date").reset_index(drop=True)


def generate_financials(tickers, dates):
    records = []
    quarterly_dates = pd.date_range(start=dates[0], end=dates[-1], freq="QS")
    for ticker, info in tickers.items():
        revenue_base = np.random.uniform(50, 300) * 1e9
        for qdate in quarterly_dates:
            growth = np.random.normal(0.02, 0.05)
            revenue_base *= (1 + growth)
            revenue = revenue_base
            cogs = revenue * np.random.uniform(0.4, 0.65)
            gross_profit = revenue - cogs
            opex = revenue * np.random.uniform(0.15, 0.30)
            operating_income = gross_profit - opex
            net_income = operating_income * np.random.uniform(0.6, 0.9)
            total_assets = revenue * np.random.uniform(2.0, 5.0)
            total_liabilities = total_assets * np.random.uniform(0.3, 0.7)
            equity = total_assets - total_liabilities
            records.append({
                "ticker": ticker,
                "report_date": qdate,
                "revenue": round(revenue, 2),
                "cogs": round(cogs, 2),
                "gross_profit": round(gross_profit, 2),
                "operating_expenses": round(opex, 2),
                "operating_income": round(operating_income, 2),
                "net_income": round(net_income, 2),
                "total_assets": round(total_assets, 2),
                "total_liabilities": round(total_liabilities, 2),
                "shareholders_equity": round(equity, 2),
            })
    return pd.DataFrame(records)


def generate_analyst_ratings(tickers, dates):
    records = []
    for ticker in tickers:
        num_ratings = np.random.randint(40, 80)
        rating_dates = np.random.choice(dates, size=num_ratings, replace=True)
        for rdate in rating_dates:
            analyst = np.random.choice(ANALYSTS)
            rating = np.random.choice(RATINGS, p=RATING_WEIGHTS)
            price_target = round(np.random.uniform(80, 500), 2)
            records.append({
                "ticker": ticker,
                "date": rdate,
                "analyst": analyst,
                "rating": rating,
                "price_target": price_target,
            })
    return pd.DataFrame(records)


def main():
    print("Generating stock market data...")
    start_date = datetime(2021, 1, 4)
    num_trading_days = 756
    dates = generate_trading_dates(start_date, num_trading_days)

    all_ohlcv = []
    for ticker, info in TICKERS.items():
        print(f"  Generating OHLCV data for {ticker}...")
        ohlcv = generate_ohlcv(info, dates)
        ohlcv["ticker"] = ticker
        all_ohlcv.append(ohlcv)
    ohlcv_df = pd.concat(all_ohlcv, ignore_index=True)

    print("Generating financial statements...")
    financials_df = generate_financials(TICKERS, dates)

    print("Generating analyst ratings...")
    ratings_df = generate_analyst_ratings(list(TICKERS.keys()), dates)

    ohlcv_path = os.path.join(OUTPUT_DIR, "stock_prices.csv")
    fin_path = os.path.join(OUTPUT_DIR, "financials.csv")
    ratings_path = os.path.join(OUTPUT_DIR, "analyst_ratings.csv")

    ohlcv_df.to_csv(ohlcv_path, index=False)
    financials_df.to_csv(fin_path, index=False)
    ratings_df.to_csv(ratings_path, index=False)

    print(f"\nData generated successfully!")
    print(f"  Stock Prices: {ohlcv_path} ({len(ohlcv_df)} rows)")
    print(f"  Financials:   {fin_path} ({len(financials_df)} rows)")
    print(f"  Ratings:      {ratings_path} ({len(ratings_df)} rows)")

    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        ohlcv_df.to_sql("stock_prices", conn, if_exists="replace", index=False)
        financials_df.to_sql("financials", conn, if_exists="replace", index=False)
        ratings_df.to_sql("analyst_ratings", conn, if_exists="replace", index=False)
        conn.close()
        print(f"\nSQLite database created: {DB_PATH}")
    except Exception as e:
        print(f"\nNote: Could not create SQLite database: {e}")


if __name__ == "__main__":
    main()
