import ccxt
import time
import ccxt

def fetch_symbols(exchange):   

    markets = exchange.load_markets(reload=True)  # Adicione o parâmetro 'reload=True'
    symbols = []
 
    for symbol in markets:
       symbols.append(symbol)   

    return symbols
        
