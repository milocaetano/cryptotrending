import pandas as pd
import numpy as np
import argparse
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import exchange 
import criptoservice as cripto
import telegrambot
import asyncio

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


async def main():
    parser = argparse.ArgumentParser(description="Trend Tracker")
    parser.add_argument("--timeframe", type=str, help="Timeframe em minutos (por exemplo, 5m 1h)", required=True)
    args = parser.parse_args()
    timeframe = f'{args.timeframe}'
    binancefuture  =exchange.binance_future_exchange()
    symbols =cripto.fetch_symbols(binancefuture)
    for symbol in symbols:
        #first_part_symbol_name = symbol.split(':')[0]
        
        print(f"Carregando dados para {symbol}...")
        ohlcv_data = binancefuture.fetch_ohlcv(symbol, timeframe)
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        current_trend = await market_trend(df)
        print(f"A tendência atual {symbol} é: {current_trend}")
        if('Tendencia Alta' in current_trend):
            await telegrambot.send_msg(f"TimeFrame: {timeframe}; A tendência atual {symbol} é: {current_trend}")
        if('Tendencia Baixa' in current_trend):
            await telegrambot.send_msg(f"TimeFrame: {timeframe}; A tendência atual {symbol} é: {current_trend}")    
      

if __name__ == '__main__':
    
    asyncio.run(main())


