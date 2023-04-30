import ccxt

def binance_future_exchange():
    binance = ccxt.binanceusdm({
        'rateLimit': 1200,
        'enableRateLimit': True,
    })

    return binance
        

def binance_exchange():
    binance = ccxt.binance({
        'rateLimit': 1200,
        'enableRateLimit': True,
    })    
    return binance
        