import yfinance as yf
import pandas as pd

MAJOR_INDICES = {
    "S&P 500": "^GSPC",
    "Nasdaq": "^IXIC",
    "Dow Jones": "^DJI"
}

# A sample list of stocks to find top movers from
MOVER_TICKERS = [
    'AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 'AMZN', 'META', 'JPM', 
    'V', 'PG', 'JNJ', 'UNH', 'HD', 'MA', 'BAC', 'DIS'
]

def get_major_indices_data():
    indices_data = []
    for name, ticker in MAJOR_INDICES.items():
        try:
            data = yf.Ticker(ticker).history(period="2d")
            if not data.empty:
                price = data['Close'].iloc[-1]
                change = price - data['Close'].iloc[-2]
                percent_change = (change / data['Close'].iloc[-2]) * 100
                indices_data.append({
                    "name": name,
                    "price": price,
                    "change": change,
                    "percent_change": percent_change
                })
        except Exception as e:
            print(f"Could not fetch data for index {name}: {e}")
    return indices_data

def get_top_movers():
    try:
        data = yf.download(MOVER_TICKERS, period="2d", progress=False)
        if data.empty:
            return {"gainers": [], "losers": []}

        close_prices = data['Close']
        price_change_percent = ((close_prices.iloc[-1] - close_prices.iloc[-2]) / close_prices.iloc[-2]) * 100

        movers_df = pd.DataFrame({
            'price': close_prices.iloc[-1],
            'percent_change': price_change_percent
        }).dropna()

        gainers = movers_df.sort_values(by='percent_change', ascending=False).head(5)
        losers = movers_df.sort_values(by='percent_change', ascending=True).head(5)

        return {
            "gainers": gainers.reset_index().rename(columns={'Ticker': 'ticker'}).to_dict('records'),
            "losers": losers.reset_index().rename(columns={'Ticker': 'ticker'}).to_dict('records')
        }
    except Exception as e:
        print(f"Could not fetch top movers: {e}")
        return {"gainers": [], "losers": []}

def get_market_overview():
    indices = get_major_indices_data()
    movers = get_top_movers()
    return {"indices": indices, "movers": movers}