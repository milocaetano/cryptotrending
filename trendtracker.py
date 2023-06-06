import numpy as np
import ccxt

def find_candle(close_prices, sma99, trend, lookback=5):
    if trend == 'Neutro':
        return None

    for i in range(-lookback, 0):
        sma99_trending_up = sma99[i - 1] < sma99[i]
        sma99_trending_down = sma99[i - 1] > sma99[i]

        if trend == 'Alta' and sma99_trending_up and close_prices[i][3] < sma99[i] and close_prices[i][4] > sma99[i]:
            return close_prices[i]
        elif trend == 'Baixa' and sma99_trending_down and close_prices[i][3] > sma99[i] and close_prices[i][4] < sma99[i]:
            return close_prices[i]

    return None

def calculate_congestion(ohlcv, lookback=14, threshold=0.01):
    close_prices = [x[4] for x in ohlcv]

    pct_changes = [(close_prices[i + 1] - close_prices[i]) / close_prices[i] for i in range(len(close_prices) - 1)]
    pct_changes_abs = np.abs(pct_changes)

    # Calcular a variação percentual média nos últimos 'lookback' períodos
    avg_pct_change = np.mean(pct_changes_abs[-lookback:])

    if avg_pct_change < threshold:
        return True  # 
    else:
        return False  # 

def analyze_trend(symbol, binance, timeframe='5m'):
    ohlcv = binance.fetch_ohlcv(symbol, timeframe)
    close_prices = [x[4] for x in ohlcv]

    sma14 = calculate_sma(close_prices, 14)
    sma21 = calculate_sma(close_prices, 21)
    sma99 = calculate_sma(close_prices, 99)

    if len(sma14) < 1 or len(sma21) < 1 or len(sma99) < 1:
        return "Neutro"

    sma99_trending_up = sma99[-1] > sma99[-2]
    sma99_trending_down = sma99[-1] < sma99[-2]
    
 
   

    if (sma14[-1] > sma21[-1]) and (sma99[-1] < sma21[-1] and sma99[-1] < sma14[-1]) and sma99_trending_up:
        trend = 'Alta'
    elif (sma14[-1] < sma21[-1]) and (sma99[-1] > sma21[-1] and sma99[-1] > sma14[-1]) and sma99_trending_down:
        trend = 'Baixa'
    else:
        trend = 'Neutro'

    candle = find_candle(ohlcv, sma99, trend)    
    congestion_chance = calculate_congestion(ohlcv)

    return trend, candle, congestion_chance


def do_order(symbol, binance, timeframe='5m'):
    (trend, candle, congestion_chance)   =analyze_trend(symbol, binance, timeframe='5m')
    if congestion_chance is not None:

        if trend == 'Alta' and congestion_chance is not True:
        
            print('Buy')
        if trend == 'Baixa' and congestion_chance is not True:
            print('Sell')


def calculate_sma(prices, period):
    return np.convolve(prices, np.ones(period) / period, mode='valid')