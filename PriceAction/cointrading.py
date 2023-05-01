import ccxt
import pandas as pd
import numpy as np
import time

# Inicializando a API
exchange = ccxt.binance({
    'rateLimit': 1200,
    'enableRateLimit': True,
})

# Configurando parâmetros
symbol = 'BNB/USDT'
timeframe = '5m'
since = exchange.parse8601('2022-01-01T00:00:00Z')
now = exchange.milliseconds()


def fetch_new_candle():
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=1)
    return pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

def update_dataframe(df):
    new_candle = fetch_new_candle()
    return pd.concat([df, new_candle], ignore_index=True)


# Buscando dados históricos
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit=None)
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

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
previous_high = None
previous_low = None


def strategy(row):
    position = None
    global previous_high, previous_low

    if row['uptrend']:
        if previous_high is not None and row['high'] > previous_high and previous_high <= row['h1']:
            position = 'long'
    elif row['downtrend']:
        if previous_low is not None and row['low'] < previous_low and previous_low >= row['l1']:
            position = 'short'

    previous_high = row['high']
    previous_low = row['low']
    return position



while True:
    print(f"Saldo: {balance:.2f}, Posições: {positions:.4f}, Preço: {df.iloc[-1]['close']:.2f}", end='\r')

    # Adiciona um novo candle ao DataFrame
    df = update_dataframe(df)
    
    # Atualiza as colunas auxiliares
    df['h1'] = df['high'].shift(1)
    df['l1'] = df['low'].shift(1)
    df['uptrend'] = df['close'] > df['close'].rolling(window=20).mean()
    df['downtrend'] = df['close'] < df['close'].rolling(window=20).mean()
    df['atr'] = df['high'] - df['low']
    
    # Aplica a estratégia no último candle
    last_candle = df.iloc[-1]
    position = strategy(last_candle)
    
    # Executa as ações de acordo com a posição
    if position == 'long':
        if positions <= 0:
            if positions < 0:
                balance += positions * (last_candle['high'] - entry_price)
                positions = 0
                print(f"Fechando posição short: {last_candle['high']:.2f}, Saldo: {balance:.2f}")   
            if positions == 0:
                entry_price = last_candle['high'] + 1
                stop_loss = last_candle['low'] - last_candle['atr'] - 1
                stop_gain = entry_price + (last_candle['atr'] / 2)
                position_size = (risk_per_trade / (entry_price - stop_loss)) * leverage
                positions = (balance * leverage) / entry_price
                half_exit = False
                print(f"Entrada long: {entry_price:.2f}, Posições: {positions:.4f}, Stop Loss: {stop_loss:.2f}, Stop Gain: {stop_gain:.2f}")
    elif position == 'short':
        if positions >= 0:
            if positions > 0:
                balance += positions * (entry_price - last_candle['low'])
                positions = 0
                print(f"Fechando posição long: {last_candle['low']:.2f}, Saldo:{balance:.2f}")
        if positions == 0:
            entry_price = last_candle['low'] - 1
            stop_loss = last_candle['high'] + last_candle['atr'] + 1
            stop_gain = entry_price - (last_candle['atr'] / 2)
            position_size = (risk_per_trade / (stop_loss - entry_price)) * leverage
            positions = (balance * leverage) / entry_price
            half_exit = False
            print(f"Entrada short: {entry_price:.2f}, Posições: {positions:.4f}, Stop Loss: {stop_loss:.2f}, Stop Gain: {stop_gain:.2f}")
    # Verificar stop loss e stop gain
    if positions > 0:
        if last_candle['low'] <= stop_loss and position == 'long':
            balance -= risk_per_trade
            positions = 0
            half_exit = False
            print(f"Stop loss atingido (long): {stop_loss:.2f}, Saldo: {balance:.2f}")
        elif last_candle['high'] >= stop_loss and position == 'short':
            balance -= risk_per_trade
            positions = 0
            half_exit = False
            print(f"Stop loss atingido (short): {stop_loss:.2f}, Saldo: {balance:.2f}")
        elif last_candle['high'] >= stop_gain and position == 'long' and not half_exit:
            balance += risk_per_trade / 2
            positions /= 2
            half_exit = True
            trailing_stop = last_candle['high'] - last_candle['atr']
            print(f"Stop gain atingido (long): {stop_gain:.2f}, Saldo: {balance:.2f}, Trailing stop: {trailing_stop:.2f}")
        elif last_candle['low'] <= stop_gain and position == 'short' and not half_exit:
            balance += risk_per_trade / 2
            positions /= 2
            half_exit = True
            trailing_stop = last_candle['low'] + last_candle['atr']
            print(f"Stop gain atingido (short): {stop_gain:.2f}, Saldo: {balance:.2f}, Trailing stop: {trailing_stop:.2f}")

        # Trailing stop
        if half_exit:
            if position == 'long':
                new_trailing_stop = last_candle['high'] - last_candle['atr']
                if new_trailing_stop > trailing_stop:
                    trailing_stop = new_trailing_stop
                if last_candle['low'] <= trailing_stop:
                    balance += positions * (last_candle['low'] - entry_price)
                    positions = 0
                    half_exit = False
                    print(f"Trailing stop atingido (long): {trailing_stop:.2f}, Saldo: {balance:.2f}")
            elif position == 'short':
                new_trailing_stop = last_candle['low'] + last_candle['atr']
                if new_trailing_stop < trailing_stop:
                    trailing_stop = new_trailing_stop
                if last_candle['high'] >= trailing_stop:
                    balance += positions * (entry_price - last_candle['high'])
                    positions = 0
                    half_exit = False
                    print(f"Trailing stop atingido (short): {trailing_stop:.2f}, Saldo: {balance:.2f}")

    # Aguarda até o próximo candle
    time.sleep(300)