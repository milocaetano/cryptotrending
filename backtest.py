import ccxt
import numpy as np
import pandas as pd
import datetime

def calculate_sma(prices, period):
    return np.convolve(prices, np.ones(period) / period, mode='valid')

symbol = 'BTC/USDT'
timeframe = '1h'
exchange = ccxt.binance()

# Calculate the timestamp for a month ago
now = exchange.milliseconds()
month_ago = now - 30 * 24 * 60 * 60 * 1000  # 30 days in milliseconds

# Fetch historical data for the past month
bars = exchange.fetch_ohlcv(symbol, timeframe, since=month_ago)

# Convert to pandas DataFrame
df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# Calculate the 21-period simple moving average using the provided function
close_prices = df['close'].values
sma21 = calculate_sma(close_prices, 21)
df = df.iloc[20:]  # Remove the first 20 rows, as they don't have SMA values
df['sma21'] = sma21

initial_balance = 10000
balance = initial_balance
position = None

for i, row in df.iterrows():
    if position is None:
        # Check for entry signal (Price Action Al Brooks strategy)
        if row['high'] > row['sma21'] and row['low'] < row['sma21']:
            position = row['close']
            signal_candle_size = row['high'] - row['low']
            profit_target = 0.8 * signal_candle_size
            stop_loss = row['low'] * 0.001
            print(f"{row['timestamp']} - Entered position at {position}")

    elif position is not None:
        # Check for exit signal (stop loss or profit target)
        if row['low'] < position - stop_loss:
            balance -= stop_loss
            print(f"{row['timestamp']} - Exited position at stop loss: {position - stop_loss}")
            position = None
        elif row['high'] > position + profit_target:
            balance += profit_target
            print(f"{row['timestamp']} - Exited position at profit target: {position + profit_target}")
            position = None

print(f"Initial balance: {initial_balance}")
print(f"Final balance: {balance}")
print(f"Profit: {balance - initial_balance}")
