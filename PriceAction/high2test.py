import ccxt
import pandas as pd
import numpy as np
import pytz
# Inicializando a API
exchange = ccxt.binance({
    'rateLimit': 1200,
    'enableRateLimit': True,
})

# Configurando parâmetros
symbol = 'BNB/USDT'
timeframe = '5m'
since = exchange.parse8601('2023-05-02T00:00:00Z')
now = exchange.milliseconds()

# Buscando dados históricos
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit=None)
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

# Adicionando colunas auxiliares
df['h1'] = df['high'].shift(1)
df['l1'] = df['low'].shift(1)
df['uptrend'] = df['close'] > df['close'].rolling(window=20).mean()
df['downtrend'] = df['close'] < df['close'].rolling(window=20).mean()
df['atr'] = df['high'] - df['low']
df['timestamp_formatted'] = pd.to_datetime(df['timestamp'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')
br_zone = pytz.timezone('America/Sao_Paulo')
df['timestamp_formatted_br'] = pd.to_datetime(df['timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert(br_zone).dt.strftime('%Y-%m-%d %H:%M:%S')



openPosition =False


def strategy(row):
    position = None
    global previous_high, previous_low

    if row['uptrend']:
        if row['high'] > previous_high and previous_high <= row['h1']:
            position = 'long'
    elif row['downtrend']:
        if row['low'] < previous_low and previous_low >= row['l1']:
            position = 'short'

    previous_high = row['high']
    previous_low = row['low']
    return position

previous_high = df.iloc[0]['high']
previous_low = df.iloc[0]['low']
df['position'] = df.apply(strategy, axis=1)

# Avaliando a estratégia
initial_balance = 500
balance = initial_balance
leverage = 10
positions = 0
entry_price = 0
stop_loss = 0
stop_gain = 0
risk_per_trade = 10
trailing_stop = 0
half_exit = False

for index, row in df.iterrows():
    if row['position'] == 'long':
        if positions <= 0:  # Adicionado condição para fechar a posição short, se houver
            if positions < 0:
                balance += positions * (row['high'] - entry_price)
                positions = 0
                print(f"Fechando posição short: {row['high']:.2f}, Saldo: {balance:.2f} TimeStamp: {row['timestamp_formatted_br']}")   
        if positions == 0:
            entry_price = row['high'] + 1
            stop_loss = row['low'] - row['atr'] - 1
            stop_gain = entry_price + (row['atr'] / 2)
            position_size = (risk_per_trade / (entry_price - stop_loss)) * leverage
            positions = (balance * leverage) / entry_price
            half_exit = False
            print(f"Entrada long: {entry_price:.2f}, Posições: {positions:.4f}, Stop Loss: {stop_loss:.2f}, Stop Gain: {stop_gain:.2f} TimeStamp: {row['timestamp_formatted_br']}")
    elif row['position'] == 'short':
        if positions >= 0:  # Adicionado condição para fechar a posição long, se houver
            if positions > 0:
                balance += positions * (entry_price - row['low'])
                positions = 0
                print(f"Fechando posição long: {row['low']:.2f}, Saldo: {balance:.2f} TimeStamp: {row['timestamp_formatted_br']}")

        if positions > 0:
            exit_price = row['low'] - 1
            stop_loss = row['high'] + row['atr'] + 1
            stop_gain = entry_price - (row['atr'] / 2)
            position_size = (risk_per_trade / (stop_loss - entry_price)) * leverage
            positions = (balance * leverage) / entry_price
            half_exit = False
            print(f"Entrada short: {exit_price:.2f}, Posições: {positions:.4f}, Stop Loss: {stop_loss:.2f}, Stop Gain: {stop_gain:.2f} TimeStamp: {row['timestamp_formatted_br']}")

    # Verificar stop loss e stop gain
    if positions > 0:
        if row['low'] <= stop_loss and row['position'] == 'long':
            balance -= risk_per_trade
            positions = 0
            half_exit = False
            print(f"Stop loss atingido (long): {stop_loss:.2f}, Saldo: {balance:.2f} TimeStamp: {row['timestamp_formatted_br']}")
        elif row['high'] >= stop_loss and row['position'] == 'short':
            balance -= risk_per_trade
            positions = 0
            half_exit = False
            print(f"Stop loss atingido (short): {stop_loss:.2f}, Saldo: {balance:.2f} TimeStamp: {row['timestamp_formatted_br']}")
        elif row['high'] >= stop_gain and row['position'] == 'long' and not half_exit:
            balance += risk_per_trade / 2
            positions /= 2
            half_exit = True
            trailing_stop = row['high'] - row['atr']
            print(f"Stop gain atingido (long): {stop_gain:.2f}, Saldo: {balance:.2f}, Trailing stop: {trailing_stop:.2f}   TimeStamp: {row['timestamp_formatted_br']} ")
        elif row['low'] <= stop_gain and row['position'] == 'short' and not half_exit:
            balance += risk_per_trade / 2
            positions /= 2
            half_exit = True
            trailing_stop = row['low'] + row['atr']
            print(f"Stop gain atingido (short): {stop_gain:.2f}, Saldo: {balance:.2f}, Trailing stop: {trailing_stop:.2f}")

        # Trailing stop
        if half_exit:
            if row['position'] == 'long':
                new_trailing_stop = row['high'] - row['atr']
                if new_trailing_stop > trailing_stop:
                    trailing_stop = new_trailing_stop
                if row['low'] <= trailing_stop:
                    balance += positions * (row['low'] - entry_price)
                    positions = 0
                    half_exit = False
                    print(f"Trailing stop atingido (long): {trailing_stop:.2f}, Saldo: {balance:.2f} TimeStamp: {row['timestamp_formatted_br']}")
            elif row['position'] == 'short':
                new_trailing_stop = row['low'] + row['atr']
                if new_trailing_stop < trailing_stop:
                    trailing_stop = new_trailing_stop
                if row['high'] >= trailing_stop:
                    balance += positions * (entry_price - row['high'])
                    positions = 0
                    half_exit = False
                    print(f"Trailing stop atingido (short): {trailing_stop:.2f}, Saldo: {balance:.2f} TimeStamp: {row['timestamp_formatted_br']}")

if positions > 0:
    balance = positions * df.iloc[-1]['close']

print(f"Saldo final: {balance:.2f}")

