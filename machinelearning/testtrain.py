import ccxt
import pandas as pd
import time
from keras.models import load_model
import numpy as np

folder = "C:\\Machine\\"
symbol = 'ETH/USDT'
timeframe = '5m'

limit = 1000  # O número máximo de velas que podem ser retornadas
exchange = ccxt.binance()
# Obtenha os dados históricos usando a API do cctx
ohlcvs = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)

# Transforme os dados em um DataFrame pandas
header = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
df = pd.DataFrame(ohlcvs, columns=header)

# Converta o carimbo de data/hora UNIX para um objeto pandas DateTimeIndex
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)

# Espere um segundo antes de fazer outra solicitação
time.sleep(1)

# Repita o processo para obter o próximo conjunto de velas
ohlcvs = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit, since=df.index[-1].timestamp() * 1000)


df_next = pd.DataFrame(ohlcvs, columns=header)
df_next['timestamp'] = pd.to_datetime(df_next['timestamp'], unit='ms')
df_next.set_index('timestamp', inplace=True)

# Combine os dois conjuntos de dados
df = pd.concat([df, df_next])

# Carregue o modelo salvo
model = load_model(f"{folder}\\output\\crypto_trend_classifier.h5")

# Remova as colunas 'Label' e 'timestamp'
X = df.drop(columns=['timestamp'])

# Normalize os dados
min_vals = np.min(X, axis=0)
max_vals = np.max(X, axis=0)
X_normalized = (X - min_vals) / (max_vals - min_vals)


# Normalizar os dados usando os mesmos valores mínimos e máximos usados para normalizar os dados de treinamento
X_test_normalized = (df - min_vals) / (max_vals - min_vals)

# Faça previsões em seus dados de teste
predictions = model.predict(X_test_normalized)

# Converta as previsões em rótulos de classe
predicted_labels = np.argmax(predictions, axis=1)

# Converta os rótulos de classe de volta para os rótulos originais
predicted_labels = pd.Series(predicted_labels).replace({0: 'uptrend', 1: 'downtrend', 2: 'congestion'})

# Imprima as previsões
print(predicted_labels)
