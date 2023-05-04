import ccxt
import backtrader as bt
import datetime
import pandas as pd
import sys
import time


class MarketTrend(bt.Indicator):
    lines = ('trend',)
    params = (('lookback', 20),)

    def __init__(self):
        self.addminperiod(self.params.lookback)

    def next(self):
        lookback = self.params.lookback

        ohlc = {
            'open': self.data.open.get(size=lookback + 1),
            'high': self.data.high.get(size=lookback + 1),
            'low': self.data.low.get(size=lookback + 1),
            'close': self.data.close.get(size=lookback + 1),
        }
        data = pd.DataFrame(ohlc)

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

        data['trend'] = 0  # Congestionado
        data.loc[data['uptrend'], 'trend'] = 1  # Tendencia Alta
        data.loc[data['downtrend'], 'trend'] = -1  # Tendencia Baixa

        if not data.empty and 'trend' in data.columns:
            self.lines.trend[0] = data['trend'].iat[-1]

        
class ATR(bt.indicators.ATR):
    pass

class PriceActionStrategy(bt.Strategy):
    params = (
        ("lookback", 20),
        ("atr_period", 14),
        ("partial_exit_ratio", 0.5),
        ("trailing_stop_atr_multiplier", 1),
        ("initial_capital", 500),
        ("risk_per_trade", 10)
    )

    def __init__(self, data0, data1):
        self.data0 = data0
        self.data1 = data1
        self.market_trend = MarketTrend(self.data0, lookback=self.params.lookback)
        self.atr = ATR(self.data1, period=self.params.atr_period)
        self.h1 = None
        self.l1 = None
        self.order = None
        self.position_open_price = None
        self.stop_loss = None

    # O restante da classe
    def _set_stoploss(self):
            # Calcular o stop loss
        if self.market_trend[0] == 1:  # Tendência de alta
            self.stop_loss = self.data1.low[-1] - self.atr[0]
        elif self.market_trend[0] == -1:  # Tendência de baixa
            self.stop_loss = self.data1.high[-1] + self.atr[0]
        else:
            self.stop_loss = None

    def next(self):
     
        self._set_stoploss()

        if self.market_trend[0] == 1:
            print(f'Tendência de alta: {self.data1.datetime.datetime(0)}') 
        elif self.market_trend[0] == -1:
            print(f'Tendência de baixa: {self.data1.datetime.datetime(0)}')       
        else:
            print(f'Congestionado: {self.data1.datetime.datetime(0)}')	

        if self.stop_loss is not None:
            position_size = self.calculate_position_size(self.stop_loss)

            # Se a tendência for de alta no timeframe de 15 minutos
            if self.market_trend[0] == 1:
                if self.buy_signal():
                    print(f"DEBUG BUY: datetime[0]={self.data1.datetime.datetime(0)}, data1.low[-1]={self.data1.low[-1]}, atr[0]={self.atr[0]}, stop_loss={self.stop_loss}")
                    self.buy(data=self.data1, size=position_size)

            # Se a tendência for de baixa no timeframe de 15 minutos
            elif self.market_trend[0] == -1:
                if self.sell_signal():
                    print(f"DEBUG SELL: datetime[0]={self.data1.datetime.datetime(0)}, data1.low[-1]={self.data1.low[-1]}, atr[0]={self.atr[0]}, stop_loss={self.stop_loss}")
                    self.sell(data=self.data1, size=position_size)

        # Gerenciar a saída da posição
        if self.position:
            print(f"Position: {self.position.size}, Price: {self.data1.close[0]}, Stop Loss: {self.stop_loss}")
            
               
            if self.position.size > 0:  # Posição comprada
                self.stop_loss = max(self.stop_loss, self.data1.high[0] - self.params.trailing_stop_atr_multiplier * self.atr[0])
                if self.data1.close[0] >= self.position_open_price + self.target_price:
                    self.sell(data=self.data1, exectype=bt.Order.Limit, price=self.target_price, size=self.position.size * self.params.partial_exit_ratio)
                    print(f"PLACE SELL TARGET PROFIT: datetime[0]={self.data1.datetime.datetime(0)}, data1.low[-1]={self.data1.low[-1]}, atr[0]={self.atr[0]}, stop_loss={self.stop_loss}")
                else:
                    print(f"PLACE SELL STOP LOSS: datetime[0]={self.data1.datetime.datetime(0)}, data1.low[-1]={self.data1.low[-1]}, atr[0]={self.atr[0]}, stop_loss={self.stop_loss}")  
                    self.sell(data=self.data1, exectype=bt.Order.Stop, price=self.stop_loss)

            elif self.position.size < 0:  # Posição vendida
                if self.data1.close[0] <= self.position_open_price - self.target_price:
                    print(f"PLACE BUY TARGET GAIN: datetime[0]={self.data1.datetime.datetime(0)}, data1.low[-1]={self.data1.low[-1]}, atr[0]={self.atr[0]}, stop_loss={self.stop_loss}")  
                    self.buy(data=self.data1, exectype=bt.Order.Limit, price=self.target_price, size=-self.position.size * self.params.partial_exit_ratio)

                self.stop_loss = min(self.stop_loss, self.data1.low[0] + self.params.trailing_stop_atr_multiplier * self.atr[0])
                print(f"PLACE BUY TARGET GAIN: datetime[0]={self.data1.datetime.datetime(0)}, data1.low[-1]={self.data1.low[-1]}, atr[0]={self.atr[0]}, stop_loss={self.stop_loss}")  
                    
                self.buy(data=self.data1, exectype=bt.Order.Stop, price=self.stop_loss)
        else:
          
            # Se a tendência for de alta no timeframe de 15 minutos
            if self.market_trend[0] == 1:
                self.stop_loss = self.data1.high[-1] + self.atr[0]
                position_size = self.calculate_position_size(self.stop_loss)
                if self.buy_signal():                    
                    self.buy(data=self.data1, size=position_size)

            # Se a tendência for de baixa no timeframe de 15 minutos
            elif self.market_trend[0] == -1:
                self.stop_loss =self.data1.high[0]+self.atr[0]
                position_size = self.calculate_position_size(self.stop_loss)
                if self.sell_signal():
                    self.sell(data=self.data1, size=position_size)
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.position_open_price = order.executed.price
                print(f" Buy Order executed: {order.executed.price}, Price: {self.data1.close[0]}, Stop Loss: {self.stop_loss}")
                
                if self.h1:
                    self.target_price = self.h1 - self.data1.low[-1]
                    self.stop_loss = self.data1.low[-1] - self.atr[0]                 

            elif order.issell():
                print(f" Sell Order executed: {order.executed.price}, Price: {self.data1.close[0]}, Stop Loss: {self.stop_loss}")
                
                self.position_open_price = order.executed.price
                if self.l1:
                    self.target_price = self.data1.high[-1] - self.l1
                    self.stop_loss = self.data1.high[-1] + self.atr[0]

            self.order = None
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.order = None
    def buy_signal(self):
            # Implementar a lógica para identificar o padrão H2 no timeframe de 5 minutos
            if self.h1 is None:
                if self.data.high[0] > self.data.high[-1]:
                    self.h1 = self.data.high[0]
            elif self.data.high[0] < self.h1:
                if self.data.open[0] > self.data.close[0]:  # Candle de alta
                    if self.data.high[0] > self.data.high[-1]:  # Máxima maior que a máxima do candle anterior
                        self.h1 = None
                        return True
            return False
    def sell_signal(self):
        # Implementar a lógica para identificar o padrão L2 no timeframe de 5 minutos
        if self.l1 is None:
            if self.data.low[0] < self.data.low[-1]:
                self.l1 = self.data.low[0]
        elif self.data.low[0] > self.l1:
            if self.data.open[0] < self.data.close[0]:  # Candle de baixa
                if self.data.low[0] < self.data.low[-1]:  # Mínima menor que a mínima do candle anterior
                    self.l1 = None
                    return True
        return False

    def calculate_position_size(self, stop_loss):
        risk = self.params.risk_per_trade
        capital = self.broker.getvalue()
        position_size = (capital * risk) / abs(stop_loss * self.data1.close[0])
        return position_size
    
def getpandadata(symbol, timeframe):
    exchange = ccxt.binance()
    # Calculate the timestamp for a month ago
    now = exchange.milliseconds()
    #month_ago = now - 30 * 24 * 60 * 60 * 1000  # 30 days in milliseconds   
    months_ago = now - 3*30 * 24 * 60 * 60 * 1000  # 30 days in milliseconds   
    # Obter os dados de OHLCV
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=months_ago)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    data = bt.feeds.PandasData(dataname=df, datetime="timestamp", open="open", high="high", low="low", close="close", volume="volume")

    return data

if __name__ == "__main__":
    cerebro = bt.Cerebro()

    # Adicionar timeframe de 15 minutos
    start_time = int(datetime.datetime(2021, 1, 1).timestamp()) * 1000
    end_time = int(datetime.datetime(2021, 3, 1).timestamp()) * 1000
   
    symbol =  'BTC/USDT'
    data0 = getpandadata(symbol, '15m')
    
    cerebro.adddata(data0)

    # Adicionar timeframe de 5 minutos
    data1 = getpandadata(symbol, '5m')
    # data1 = data0.clone()
    # data1._timeframe = bt.TimeFrame.Minutes
    # data1._compression = 5
    cerebro.adddata(data1)

    cerebro.addstrategy(PriceActionStrategy, data0=data0, data1=data1)
    # Definir o capital inicial
    cerebro.broker.setcash(500)
    cerebro.run()
    # Plotar os resultados
    cerebro.plot()