import os
import pandas as pd
import yfinance as yf
import pickle
import joblib
from prophet.serialize import model_from_json
from tensorflow.keras.models import load_model
import numpy as np

# --- Import the real-time training functions ---
from .realtime_forecasting import run_all_forecasts_realtime

def predict_from_saved_models(ticker: str, horizon: int = 5):
    """
    Attempts to load pre-trained models and make a forecast.
    Returns None if files are not found.
    """
    model_path = f"{ticker}_arima.pkl"
    if not os.path.exists(model_path):
        print(f"--- No pre-trained model found for {ticker}. Switching to real-time training. ---")
        return None # Signal that we need to train in real-time

    print(f"--- Loading pre-trained models for {ticker} ---")
    results = {}
    try:
        # Load and predict with ARIMA
        with open(f"{ticker}_arima.pkl", "rb") as f:
            arima_model = pickle.load(f)
        arima_pred = arima_model.forecast(steps=horizon)
        results['arima'] = {"status": "success", "last_pred": arima_pred.iloc[-1]}

        # Load and predict with Prophet
        with open(f"{ticker}_prophet.json", "r") as f:
            prophet_model = model_from_json(f.read())
        future = prophet_model.make_future_dataframe(periods=horizon)
        forecast = prophet_model.predict(future)
        results['prophet'] = {"status": "success", "last_pred": forecast['yhat'].iloc[-1]}

        # Load and predict with LSTM
        lstm_model = load_model(f"{ticker}_lstm.h5")
        scaler = joblib.load(f"{ticker}_scaler.save")
        data = yf.download(ticker, period="90d", interval="1d", progress=False)
        series = data['Close']
        last_60_days = series[-60:].values.reshape(-1, 1)
        last_60_days_scaled = scaler.transform(last_60_days)
        X_test = np.array([last_60_days_scaled])
        pred_scaled = lstm_model.predict(X_test, verbose=0)
        pred = scaler.inverse_transform(pred_scaled)
        results['lstm'] = {"status": "success", "last_pred": pred[0][0]}

        return {
            "ticker": ticker, "horizon": horizon, "results": results,
            "best_model": "lstm" # Default for pre-trained
        }
    except Exception as e:
        print(f"Error loading pre-trained models for {ticker}: {e}")
        return None # Fallback to real-time if there's an error

def run_all_forecasts(ticker: str, horizon: int):
    """
    Main function that first tries to use saved models, then falls back
    to real-time training if necessary.
    """
    # First, try the fast, pre-trained model approach
    result = predict_from_saved_models(ticker, horizon)

    # If it returns a result, we're done
    if result:
        return result

    # Otherwise, run the slower, real-time training
    return run_all_forecasts_realtime(ticker, horizon)
def predict_from_saved_models(ticker: str, horizon: int = 5):
    """
    Attempts to load pre-trained models and make a forecast.
    Returns None if files are not found.
    """
    model_path = f"{ticker}_arima.pkl"
    if not os.path.exists(model_path):
        print(f"--- No pre-trained model found for {ticker}. Switching to real-time training. ---")
        return None # Signal that we need to train in real-time

    print(f"--- Loading pre-trained models for {ticker} ---")
    results = {}
    try:
        # 1. Load and predict with ARIMA
        with open(f"{ticker}_arima.pkl", "rb") as f:
            arima_model = pickle.load(f)
        arima_pred = arima_model.forecast(steps=horizon)
        results['arima'] = {"status": "success", "last_pred": arima_pred.iloc[-1]}

        # 2. Load and predict with Prophet
        with open(f"{ticker}_prophet.json", "r") as f:
            prophet_model = model_from_json(f.read())
        future = prophet_model.make_future_dataframe(periods=horizon)
        forecast = prophet_model.predict(future)
        results['prophet'] = {"status": "success", "last_pred": forecast['yhat'].iloc[-1]}

        # 3. Load and predict with LSTM
        lstm_model = load_model(f"{ticker}_lstm.h5")
        scaler = joblib.load(f"{ticker}_scaler.save")
        
        # Fetch recent data for LSTM input AND to get the current price
        data = yf.download(ticker, period="90d", interval="1d", progress=False)
        series = data['Close']
        current_price = series.iloc[-1] # GET THE CURRENT PRICE
        
        look_back = 60
        last_60_days = series[-look_back:].values.reshape(-1, 1)
        last_60_days_scaled = scaler.transform(last_60_days)
        X_test = np.array([last_60_days_scaled])
        
        pred_scaled = lstm_model.predict(X_test, verbose=0)
        pred = scaler.inverse_transform(pred_scaled)
        results['lstm'] = {"status": "success", "last_pred": pred[0][0]}

        return {
            "ticker": ticker, 
            "horizon": horizon, 
            "results": results,
            "best_model": "lstm", # Default for pre-trained
            "current_price": current_price # ADDED CURRENT PRICE
        }
    except Exception as e:
        print(f"Error loading pre-trained models for {ticker}: {e}")
        return None