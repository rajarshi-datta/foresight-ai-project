from . import forecasting
import yfinance as yf
import time
from sqlalchemy.orm import Session
from .. import crud

# In-memory cache
suggestions_cache = {
    "timestamp": 0,
    "data": []
}
CACHE_DURATION_SECONDS = 4 * 60 * 60  # Cache for 4 hours

TICKER_UNIVERSE = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 'AMZN', 'META']

def generate_suggestions(db: Session, horizon: int = 5):
    current_time = time.time()

    # Check if the cache is still valid
    if current_time - suggestions_cache["timestamp"] < CACHE_DURATION_SECONDS and suggestions_cache["data"]:
        print("--- Serving suggestions from cache ---")
        return suggestions_cache["data"]

    print("--- Cache expired or empty. Generating new suggestions... ---")
    suggestions = []

    # ... (The loop to generate suggestions remains exactly the same) ...
    for ticker in TICKER_UNIVERSE:
        try:
            stock_data = yf.Ticker(ticker)
            current_price = stock_data.history(period="1d")['Close'].iloc[-1]
            if current_price is None: continue

            forecast_data = forecasting.run_all_forecasts(ticker, horizon)
            if "error" in forecast_data: continue

            predicted_price = forecast_data["results"]["lstm"]["last_pred"]
            if predicted_price is None: continue

            growth_percent = ((predicted_price - current_price) / current_price) * 100

            suggestions.append({
                "ticker": ticker,
                "current_price": current_price,
                "forecast_details": {
                    "predicted_price": predicted_price,
                    "horizon_days": horizon,
                    "best_model": forecast_data.get("best_model", "N/A"),
                },
                "suggestion_metrics": {
                    "predicted_growth_percent": growth_percent,
                    "suggestion_score": growth_percent
                }
            })
        except Exception as e:
            print(f"Could not analyze {ticker}: {e}")
            continue

    suggestions.sort(key=lambda x: x['suggestion_metrics']['suggestion_score'], reverse=True)

    ranked_suggestions = []
    for i, suggestion in enumerate(suggestions[:3]):
        suggestion['rank'] = i + 1
        ranked_suggestions.append(suggestion)

    # --- CORRECTED LOGIC ---
    # 1. Save the newly generated suggestions to the database
    print("--- Saving new suggestions to database history... ---")
    for suggestion in ranked_suggestions:
        crud.create_suggestion_history(db=db, suggestion=suggestion)

    # 2. THEN, update the cache with the new data
    suggestions_cache["timestamp"] = current_time
    suggestions_cache["data"] = ranked_suggestions

    return ranked_suggestions