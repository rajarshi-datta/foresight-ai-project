import pandas as pd
import yfinance as yf
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from prophet import Prophet
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import numpy as np
from sklearn.metrics import mean_squared_error
import warnings

warnings.filterwarnings("ignore")

# --- Model Implementations (Real-Time Training) ---

def run_arima(series, horizon):
    try:
        if len(series) < horizon * 2:
            raise ValueError("Not enough data for ARIMA model.")
        train_data, test_data = series[:-horizon], series[-horizon:]
        model = ARIMA(train_data, order=(5, 1, 0))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=horizon)
        rmse = np.sqrt(mean_squared_error(test_data, forecast))
        return {
            "status": "success", "rmse": rmse, "last_pred": forecast.iloc[-1],
            "predictions": forecast.tolist()
        }
    except Exception as e:
        return {"status": "failed", "error_message": str(e)}

def run_sarima(series, horizon):
    try:
        if len(series) < horizon * 2:
            raise ValueError("Not enough data for SARIMA model.")
        train_data, test_data = series[:-horizon], series[-horizon:]
        model = SARIMAX(train_data, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
        model_fit = model.fit(disp=False)
        forecast = model_fit.forecast(steps=horizon)
        rmse = np.sqrt(mean_squared_error(test_data, forecast))
        return {
            "status": "success", "rmse": rmse, "last_pred": forecast.iloc[-1],
            "predictions": forecast.tolist()
        }
    except Exception as e:
        return {"status": "failed", "error_message": str(e)}

def run_prophet(series, horizon):
    try:
        if len(series) < 30:
            raise ValueError("Not enough data for Prophet model.")
        df = series.reset_index(); df.columns = ['ds', 'y']
        model = Prophet(); model.fit(df)
        future = model.make_future_dataframe(periods=horizon)
        forecast = model.predict(future)
        y_pred, y_true = forecast['yhat'][-horizon:].values, series[-horizon:].values
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        return {
            "status": "success", "rmse": rmse, "last_pred": forecast['yhat'].iloc[-1],
            "predictions": forecast['yhat'][-horizon:].tolist()
        }
    except Exception as e:
        return {"status": "failed", "error_message": str(e)}

def run_lstm(series, horizon):
    try:
        if len(series) < 60:
            raise ValueError("Not enough data for LSTM model.")
        data = series.values.reshape(-1, 1)
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(data)
        look_back = 60
        X, y = [], []
        for i in range(look_back, len(scaled_data)):
            X.append(scaled_data[i-look_back:i, 0]); y.append(scaled_data[i, 0])
        X, y = np.array(X), np.array(y)
        X = np.reshape(X, (X.shape[0], X.shape[1], 1))
        test_size, train_size = horizon, len(X) - horizon
        X_train, X_test = X[0:train_size], X[train_size:len(X)]
        y_train, y_test = y[0:train_size], y[train_size:len(y)]
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(X.shape[1], 1)),
            LSTM(50, return_sequences=False), Dense(25), Dense(1)
        ])
        model.compile(optimizer='adam', loss='mean_squared_error')
        model.fit(X_train, y_train, batch_size=1, epochs=1, verbose=0)
        predictions = scaler.inverse_transform(model.predict(X_test, verbose=0))
        y_test_inv = scaler.inverse_transform(y_test.reshape(-1, 1))
        rmse = np.sqrt(mean_squared_error(y_test_inv, predictions))
        return {
            "status": "success", "rmse": rmse, "last_pred": predictions[-1][0],
            "predictions": predictions.flatten().tolist()
        }
    except Exception as e:
        return {"status": "failed", "error_message": str(e)}

def run_all_forecasts_realtime(ticker: str, horizon: int):
    """
    This is the main orchestrator for on-demand training.
    """
    try:
        data = yf.download(ticker, period="3y", interval="1d", progress=False)
        if data.empty:
            raise ValueError(f"No data found for ticker {ticker}")

        series = data['Close']
        current_price = series.iloc[-1] # --- 1. GET THE CURRENT PRICE ---

        results = {
            'arima': run_arima(series, horizon),
            'sarima': run_sarima(series, horizon),
            'prophet': run_prophet(series, horizon),
            'lstm': run_lstm(series, horizon)
        }

        best_model, min_rmse = None, float('inf')
        for model_name, result in results.items():
            if result.get('status') == 'success' and result.get('rmse', float('inf')) < min_rmse:
                min_rmse, best_model = result['rmse'], model_name

        # --- 2. ADD THE CURRENT PRICE TO THE RESPONSE ---
        return {
            "ticker": ticker, 
            "horizon": horizon, 
            "results": results,
            "best_model": best_model,
            "current_price": current_price 
        }
    except Exception as e:
        return {"error": str(e)}