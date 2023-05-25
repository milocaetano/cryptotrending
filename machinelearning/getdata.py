import ccxt
import pandas as pd
from datetime import datetime
import pytz

def convert_input_format(input_str):
    return pd.to_datetime(input_str, format='%Y%m%d%H', exact=False)

def convert_to_utc(local_datetime, local_timezone="America/Sao_Paulo"):
    local_tz = pytz.timezone(local_timezone)
    local_dt = local_tz.localize(local_datetime, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.UTC)
    return utc_dt

def get_data(symbol, label, timeframe, start_date, end_date):
    exchange = ccxt.binance()
    
    start_date = convert_to_utc(convert_input_format(start_date))
    end_date = convert_to_utc(convert_input_format(end_date))
    
    start_timestamp = exchange.parse8601(start_date.isoformat() + 'Z')
    end_timestamp = exchange.parse8601(end_date.isoformat() + 'Z')   
    
    ohlcv_data = exchange.fetch_ohlcv(symbol, timeframe, start_timestamp, end_timestamp)
    
    #print(ohlcv_data)
    
    df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['SMA_14'] = df['Close'].rolling(window=14).mean()
    df['SMA_21'] = df['Close'].rolling(window=21).mean()
    df['SMA_99'] = df['Close'].rolling(window=99).mean()
    df["Label"] = label
    return df

def save_data_to_csv(df, file_name):
    df.to_csv(file_name, index=False)

if __name__ == '__main__':

    # Example usage
    symbol = "BTCUSDT"
    timeframe = "5m"
    start_date = "202304190300"
    end_date = "202304221300"
    label = "downtrend"
    data = get_data(symbol, label, timeframe, start_date, end_date)
    path = f'C:\Machine\DownTrend'
    save_data_to_csv(data, f"{path}\{symbol}{start_date}-{end_date}.csv")



 
