import yfinance as yf
from datetime import datetime

def test_yf():
    ticker = "AAPL"
    print(f"Testing yfinance for {ticker}...")
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1wk", interval="1h")
        print(f"Dataframe size: {len(df)}")
        if not df.empty:
            print("Columns:", df.columns.tolist())
            print("First few rows:")
            print(df.head())
    except Exception as e:
        print(f"Error calling yfinance: {e}")

if __name__ == "__main__":
    test_yf()
