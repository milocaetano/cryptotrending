import criptoservice as cripto
import trendtracker
import exchange
import argparse
import asyncio
import telegrambot as telegram
import time
import keyboard

async def run(symbols, binance, timeframe):
    for symbol in symbols: 
        if keyboard.is_pressed('esc'):
            print("ESC key pressed. Exiting...")
            return False   
        trend, candle = trendtracker.analyze_trend(symbol, binance, timeframe=timeframe)      
        if candle is not None:
            print(f"Tendência para {symbol}: {trend}")
            print("Candle encontrado:", candle)
            await telegram.send_msg(f"Tendência para {symbol}: {trend}")
            await telegram.send_msg(f"Candle encontrado:") 
                
        else:  
            if(trend == 'Alta' or trend == 'Baixa'):
                    await telegram.send_msg(f"Tendência para {symbol}: {trend}")
                    await telegram.send_msg(f"Candle Não encontrado")
     
            print(f"Tendência para {symbol}: {trend}, nenhum candle encontrado") 
    return True  


async def main():
    parser = argparse.ArgumentParser(description="Trend Tracker")
    parser.add_argument("--timeframe", type=int, help="Timeframe em minutos (por exemplo, 5)", required=True)
    args = parser.parse_args()
    timeframe = f'{args.timeframe}m'
    binance  =exchange.binance_future_exchange()
    symbols =cripto.fetch_symbols(binance)
    while True:
     if keyboard.is_pressed('esc'):
            print("ESC key pressed. Exiting...")
            break
     result = await run(symbols, binance, timeframe)
     if(result == False):
         break
     time.sleep(60)  

if __name__ == '__main__':
    asyncio.run(main())
