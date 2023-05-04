import ccxt
import pandas as pd
import pandas_ta as ta

# Configuração da Binance sem chaves de API
binance = ccxt.binance()

# Obter dados históricos (último mês)
symbol = "BNB/USDT"
timeframe = "5m"
since = binance.parse8601("2023-04-01T00:00:00Z")
ohlcv = binance.fetch_ohlcv(symbol, timeframe, since)

# Converter para um DataFrame
df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

# Calcular Pivot Points com Pandas_TA
pivot_points = ta.pivotpoints(df["high"], df["low"], df["close"], method="standard", timeperiod=200)
df = pd.concat([df, pivot_points], axis=1)

print(df.tail())
