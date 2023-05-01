import ccxt
import pandas as pd
import numpy as np
import random

symbol = 'BTC/USD'
timeframe = '15m'

exchange = ccxt.binance({
    'rateLimit': 1200,
    'enableRateLimit': True,
})

ohlcv = exchange.fetch_ohlcv(symbol, timeframe)
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

# Calculate ATR
df['tr0'] = abs(df['high'] - df['low'])
df['tr1'] = abs(df['high'] - df['close'].shift())
df['tr2'] = abs(df['low'] - df['close'].shift())
df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
df['atr'] = df['tr'].rolling(14).mean()

# Define initial capital
initial_capital = 10000
capital = initial_capital
position = None
capital_history = []
profit_history = []

# Perform backtest
for i, row in df.iterrows():
    if i < 14:
        capital_history.append(capital)
        continue

    if not position:
        signal = random.choice(['buy', 'sell'])
        price = row['close']
        position = (signal, price, capital)
        print(f"Entrada ({signal.upper()}): {price:.2f} USD")
    else:
        action, entry_price, entry_capital = position
        current_price = row['close']
        atr = row['atr']
        gain = 0.01 * entry_capital + atr
        stop_loss = 0.01 * entry_capital

        if action == 'buy':
            if current_price >= entry_price + gain:
                capital = entry_capital + (current_price - entry_price) * (entry_capital / entry_price)
                position = None
                profit = capital - entry_capital
                profit_history.append(profit)
                print(f"Saída ({action.upper()}): {current_price:.2f} USD, Profit: {profit:.2f} USD")
            elif current_price <= entry_price - stop_loss:
                capital = entry_capital - stop_loss
                position = None
                profit = capital - entry_capital
                profit_history.append(profit)
                print(f"Saída ({action.upper()}): {current_price:.2f} USD, Profit: {profit:.2f} USD")
        else:
            if current_price <= entry_price - gain:
                capital = entry_capital + (entry_price - current_price) * (entry_capital / entry_price)
                position = None
                profit = capital - entry_capital
                profit_history.append(profit)
                print(f"Saída ({action.upper()}): {current_price:.2f} USD, Profit: {profit:.2f} USD")
            elif current_price >= entry_price + stop_loss:
                capital = entry_capital - stop_loss
                position = None
                profit = capital - entry_capital
                profit_history.append(profit)
                print(f"Saída ({action.upper()}): {current_price:.2f} USD, Profit: {profit:.2f} USD")

    capital_history.append(capital)

final_capital = capital_history[-1]
total_profit = final_capital - initial_capital

print("\n")
print(f"Capital inicial: {initial_capital:.2f} USD")

print(f"Lucro: {profit:.2f} USD")
