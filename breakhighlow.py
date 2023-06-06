import ccxt
import asyncio
import argparse
import time
import telegrambot

alerted_price = False  # Variável de controle para saber se um alerta de preço já foi enviado
alerted_candle = False  # Variável de controle para saber se um alerta de candle já foi enviado
alert_time_price = None  # Tempo em que o alerta de preço foi disparado
alert_time_candle = None  # Tempo em que o alerta de candle foi disparado

def timeframe_to_seconds(timeframe_str):
    multiplier = int(timeframe_str[:-1])  # get numeric part
    if timeframe_str.endswith('m'):
        return multiplier * 60
    elif timeframe_str.endswith('h'):
        return multiplier * 60 * 60
    elif timeframe_str.endswith('d'):
        return multiplier * 60 * 60 * 24

async def check_price_and_candle(exchange, symbol, parameter, timeframe):
    global alerted_price, alerted_candle, alert_time_price, alert_time_candle  # Acessa as variáveis globais
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=2)
    last_candle = ohlcv[-1]
    previous_candle = ohlcv[-2]

    # Reseta 'alerted' para False se um novo candle foi formado ou tempo do alerta já passou o timeframe
    if last_candle[0] != previous_candle[0] or (alert_time_price and (time.time() - alert_time_price > timeframe_to_seconds(timeframe))):
        alerted_price = False
        alert_time_price = None
    if last_candle[0] != previous_candle[0] or (alert_time_candle and (time.time() - alert_time_candle > timeframe_to_seconds(timeframe))):
        alerted_candle = False
        alert_time_candle = None

    # Verifica o preço
    if not alerted_price:
        if parameter == "high" and last_candle[2] > previous_candle[2]:  # Comparando as máximas dos dois últimos candles
            print(f"O preço de {symbol} ultrapassou a máxima do candle anterior!")
            await telegrambot.send_msg(f"ATENÇÃOO!!!!! O preço de {symbol} ultrapassou a máxima do candle anterior!  TimeFrame: {timeframe}; https://www.binance.com/en/futures/{symbol}")
            alerted_price = True  # Define 'alerted_price' como True após enviar um alerta
            alert_time_price = time.time()  # Grava o tempo atual como tempo do alerta
                 
        elif parameter == "low" and last_candle[3] < previous_candle[3]:  # Comparando as mínimas dos dois últimos candles
            print(f"O preço de {symbol} ultrapassou a mínima do candle anterior!")
            await telegrambot.send_msg(f"ATENÇÃOO!!!!! O preço de {symbol} ultrapassou a Mínima do candle anterior!  TimeFrame: {timeframe}; https://www.binance.com/en/futures/{symbol}")
            alerted_price = True  # Define 'alerted_price' como True após enviar um alerta
            alert_time_price = time.time()  # Grava o tempo atual como tempo do alerta

         # Verifica se o último candle fechou como bearish ou bullish
        if not alerted_candle:
            if parameter == "high" and last_candle[4] > last_candle[1]:  # Verificando se o último candle fechou bullish
                print(f"O último candle de {symbol} fechou bullish!")
                await telegrambot.send_msg(f"O último candle de {symbol} fechou bullish! TimeFrame: {timeframe}; https://www.binance.com/en/futures/{symbol}")
                alerted_candle = True  # Define 'alerted_candle' como True após enviar um alerta
                alert_time_candle = time.time()  # Grava o tempo atual como tempo do alerta

            elif parameter == "low" and last_candle[4] < last_candle[1]:  # Verificando se o último candle fechou bearish
                print(f"O último candle de {symbol} fechou bearish!")
                await telegrambot.send_msg(f"O último candle de {symbol} fechou bearish! TimeFrame: {timeframe}; https://www.binance.com/en/futures/{symbol}")
                alerted_candle = True  # Define 'alerted_candle' como True após enviar um alerta
                alert_time_candle = time.time()  # Grava o tempo atual como tempo do alerta

async def main():
    parser = argparse.ArgumentParser(description="Price Checker")
    parser.add_argument("--symbol", type=str, help="Symbol to check (e.g. 'BTC/USDT')", required=True)
    parser.add_argument("--parameter", type=str, help="Parameter to check ('high' or 'low')", required=True)
    parser.add_argument("--timeframe", type=str, help="Timeframe (default '15m')", required=False, default='15m')
    args = parser.parse_args()
    symbol = args.symbol
    parameter = args.parameter
    timeframe = args.timeframe

    exchange = ccxt.binance()  # Conectando com a Binance

    while True:  # Loop infinito
        print(f"Checking... {symbol}")            
        await check_price_and_candle(exchange, symbol, parameter, timeframe)
        await asyncio.sleep(30)  # Pausa de 30 segundos

if __name__ == "__main__":
    asyncio.run(main())

