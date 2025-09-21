import yfinance as yf
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet
from prophet.serialize import model_to_json
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import numpy as np
import pickle
import joblib
import warnings

warnings.filterwarnings("ignore")

# The list of stocks you want to pre-train models for
TICKER_UNIVERSE = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 'AMZN', 'META']

def train_and_save_models_for_ticker(ticker):
    print(f"--- Training models for {ticker} ---")
    try:
        # 1. Fetch data
        data = yf.download(ticker, period="5y", interval="1d")
        if data.empty:
            print(f"No data for {ticker}, skipping.")
            return
        series = data['Close']

        # 2. Train and save ARIMA
        print(f"Training ARIMA for {ticker}...")
        arima_model = ARIMA(series, order=(5, 1, 0)).fit()
        with open(f"{ticker}_arima.pkl", "wb") as f:
            pickle.dump(arima_model, f)
        print(f"Saved {ticker}_arima.pkl")

        # 3. Train and save Prophet
        print(f"Training Prophet for {ticker}...")
        df = series.reset_index(); df.columns = ['ds', 'y']
        prophet_model = Prophet().fit(df)
        with open(f"{ticker}_prophet.json", "w") as f:
            f.write(model_to_json(prophet_model))
        print(f"Saved {ticker}_prophet.json")

        # 4. Train and save LSTM
        print(f"Training LSTM for {ticker}...")
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(series.values.reshape(-1, 1))

        look_back = 60
        X, y = [], []
        for i in range(look_back, len(scaled_data)):
            X.append(scaled_data[i-look_back:i, 0]); y.append(scaled_data[i, 0])
        X, y = np.array(X), np.array(y)
        X = np.reshape(X, (X.shape[0], X.shape[1], 1))

        lstm_model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(X.shape[1], 1)),
            LSTM(50), Dense(25), Dense(1)
        ])
        lstm_model.compile(optimizer='adam', loss='mean_squared_error')
        lstm_model.fit(X, y, batch_size=1, epochs=10) # More epochs for better training

        lstm_model.save(f"{ticker}_lstm.h5")
        joblib.dump(scaler, f"{ticker}_scaler.save")
        print(f"Saved {ticker}_lstm.h5 and {ticker}_scaler.save")

    except Exception as e:
        print(f"Failed to train models for {ticker}: {e}")

# Main execution block
if __name__ == "__main__":
    for ticker in TICKER_UNIVERSE:
        train_and_save_models_for_ticker(ticker)
    print("\n--- All models trained and saved! ---")