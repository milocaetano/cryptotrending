import pandas as pd
import numpy as np
import argparse
import sys
import ccxt
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import criptoservice as cripto
import telegrambot
import asyncio

def binance_future_exchange():
    binance = ccxt.binanceusdm({
        'rateLimit': 50,
        'enableRateLimit': True,
    })

    return binance       


async def market_trend(data, lookback=20):
    data['prev_high'] = data['high'].shift(1)
    data['prev_low'] = data['low'].shift(1)

    data['higher_high'] = data['high'] > data['prev_high']
    data['lower_low'] = data['low'] < data['prev_low']

    higher_high_sum = data['higher_high'].rolling(window=lookback).sum()
    lower_low_sum = data['lower_low'].rolling(window=lookback).sum()

    data['uptrend'] = higher_high_sum > lookback * 0.6
    data['downtrend'] = lower_low_sum > lookback * 0.6

    data['doji'] = abs(data['open'] - data['close']) / (data['high'] - data['low']) < 0.1
    data['doji_count'] = data['doji'].rolling(window=lookback).sum()

    data['congested'] = data['doji_count'] > lookback * 0.4

    data['trend'] = 'Congestionado'
    data.loc[data['uptrend'], 'trend'] = 'Tendencia Alta'
    data.loc[data['downtrend'], 'trend'] = 'Tendencia Baixa'

    return data['trend'].iloc[-1]

async def market_continuetrending(data):
    data['prev_close'] = data['close'].shift(1)

    data['bullish'] = data['close'] > data['prev_close']
    data['bearish'] = data['close'] < data['prev_close']

    data['uptrend'] = False
    data['downtrend'] = False

    for i in range(len(data)-1, len(data)-11, -1): # Loop reverso começando do último candle
        # Verifica se há pelo menos 7 a 10 candles bullish ou bearish consecutivos
        if data['bullish'].iloc[i-10:i].all(): 
            data.at[i, 'uptrend'] = True
            break
        elif data['bearish'].iloc[i-10:i].all(): 
            data.at[i, 'downtrend'] = True
            break

    data['trend'] = 'Congestionado'
    data.loc[data['uptrend'], 'trend'] = 'Tendencia de Alta'
    data.loc[data['downtrend'], 'trend'] = 'Tendencia de Baixa'

    return data['trend'].iloc[-1]

async def market_continuetrending2(data):
    data['prev_close'] = data['close'].shift(1)

    data['bullish'] = data['close'] > data['prev_close']
    data['bearish'] = data['close'] < data['prev_close']

    data['uptrend'] = False
    data['downtrend'] = False

    for i in range(6, 7):  # Verificar de 6 a 12
        bullish_sum = data['bullish'].rolling(window=i).sum()
        bearish_sum = data['bearish'].rolling(window=i).sum()

        data['uptrend'] = data['uptrend'] | (bullish_sum == i)
        data['downtrend'] = data['downtrend'] | (bearish_sum == i)

    data['trend'] = 'Congestionado'
    data.loc[data['uptrend'], 'trend'] = 'Tendencia de Alta'
    data.loc[data['downtrend'], 'trend'] = 'Tendencia de Baixa'

    return data['trend'].iloc[-1]

async def market_continuetrending_smart(data):
    data['prev_close'] = data['close'].shift(1)

    data['bullish'] = data['close'] > data['prev_close']
    data['bearish'] = data['close'] < data['prev_close']
    data['doji'] = (abs(data['open'] - data['close']) / (data['high'] - data['low'])) < 0.1 # this assumes that a doji candle has a body less than 10% of the total candle range

    data['uptrend'] = False
    data['downtrend'] = False

    for i in range(len(data)-1, len(data)-11, -1): # Reverse loop starting from the last candle
        # Check for 5 to 10 consecutive bullish or bearish candles, excluding dojis
        bullish_candles = data['bullish'].iloc[i-10:i] & ~data['doji'].iloc[i-10:i]
        bearish_candles = data['bearish'].iloc[i-10:i] & ~data['doji'].iloc[i-10:i]

        # Exclude bearish candles if they are smaller than 60% of the average bullish body
        bearish_candles_size = data[data['bearish']]['close'] - data[data['bearish']]['open']
        bullish_candles_size = data[data['bullish']]['close'] - data[data['bullish']]['open']
        bearish_candles = bearish_candles & (bearish_candles_size < 0.6 * bullish_candles_size.mean())

        # Now we just need to count the sequences and exclude if there are more than one bearish candle
        bullish_count = bullish_candles.rolling(10).sum()
        bearish_count = bearish_candles.rolling(10).sum()

        if ((bullish_count >= 5) & (bullish_count <= 10) & (bearish_count <= 1)).any(): 
            data.at[i, 'uptrend'] = True
            break
        elif ((bearish_count >= 5) & (bearish_count <= 8) & (bullish_count <= 1)).any(): 
            data.at[i, 'downtrend'] = True
            break

    data['trend'] = 'Congestionado'
    data.loc[data['uptrend'], 'trend'] = 'Tendencia de Alta'
    data.loc[data['downtrend'], 'trend'] = 'Tendencia de Baixa'

    return data['trend'].iloc[-1]


async def main():
    parser = argparse.ArgumentParser(description="Trend Tracker")
    parser.add_argument("--timeframe", type=str, help="Timeframe em minutos (por exemplo, 5m 1h)", required=True)
    args = parser.parse_args()
    timeframe = f'{args.timeframe}'
    binancefuture  = binance_future_exchange()
    symbols = cripto.fetch_symbols(binancefuture)
    last_trend = {}  # Dicionário para armazenar a última tendência para cada símbolo   

    try:
        symbol = 'AMB/USDT'          
        print(f"Carregando dados para {symbol}...")
        ohlcv_data = binancefuture.fetch_ohlcv(symbol, timeframe, limit=20)
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        current_trend = await market_continuetrending_smart(df)
        print(f"A tendência atual {symbol} é: {current_trend}")

        if symbol in last_trend:  # Se já temos uma tendência registrada para este símbolo     
            if last_trend[symbol] != current_trend:  # E a tendência mudou
                coin =  symbol.replace("/", "").replace(":USDT", "")
                if(current_trend == 'Congestionado'):
                    print(f"TimeFrame: {timeframe}; {symbol} mudou de {last_trend[symbol]} para {current_trend}")                            
                else:                        
                    print(f"TimeFrame: {timeframe}; {symbol} mudou de {last_trend[symbol]} para {current_trend}")
                    await telegrambot.send_msg(f"TimeFrame: {timeframe}; https://www.binance.com/en/futures/{coin} mudou de {last_trend[symbol]} para {current_trend}")
        else:  # Se ainda não temos uma tendência registrada para este símbolo
            last_trend[symbol] = current_trend  # Registre a tendência atual
            coin =  symbol.replace("/", "").replace(":USDT", "")
            if current_trend != 'Congestionado':
                await telegrambot.send_msg(f"TimeFrame: {timeframe}; https://www.binance.com/en/futures/{coin} Tendencia de {current_trend}")

        last_trend[symbol] = current_trend  # Atualize a última tendência para este símbolo
            #await asyncio.sleep(1)  # Opcional: pause para evitar sobrecarregar a API
    except KeyboardInterrupt:
        print("Interrompido pelo usuário. Saindo...")
       
    except Exception as e:
        print(f"Erro: {e}")
      

if __name__ == '__main__':
    asyncio.run(main())

