import ccxt
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
# Criar uma instância do objeto Binance
exchange = ccxt.binance()

# Definir o símbolo e o intervalo de tempo
symbol = 'AMB/USDT'
timeframe = '5m'

# Obter os dados do mercado da Binance
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=20)

# Extrair informações do OHLCV
timestamps = [entry[0] for entry in ohlcv]
opens = [entry[1] for entry in ohlcv]
highs = [entry[2] for entry in ohlcv]
lows = [entry[3] for entry in ohlcv]
closes = [entry[4] for entry in ohlcv]

# Criar um DataFrame com os dados
data = {
    'timestamp': timestamps,
    'open': opens,
    'high': highs,
    'low': lows,
    'close': closes
}
df = pd.DataFrame(data)
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)

# Configurar o estilo do gráfico
mc = mpf.make_marketcolors(up='g', down='r')
s = mpf.make_mpf_style(marketcolors=mc)

# Plotar o gráfico de candlestick
mpf.plot(df, type='candle', style=s)
