import backtrader as bt
import ccxt
import pandas as pd
import random 
from backtrader_plotting import Bokeh

# Defina sua chave API e segredo aqui
api_key = "sua_api_key"
api_secret = "seu_api_secret"

# Defina o par de ativos e intervalo de tempo aqui
symbol = "BTC/USDT"
timeframe = "5m"

class DoubleLeverage(bt.Strategy):
    params = dict(
        leverage=20,
        target_profit=1,
        max_consecutive_losses=3,
        cool_down_period=50
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.current_bet = self.p.target_profit
        self.consecutive_losses = 0
        self.cool_down_counter = 0

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
            else:
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def next(self):
        if self.order:
            return

        if self.cool_down_counter > 0:
            self.cool_down_counter -= 1
            return

        flip = random.random() > 0.5

        if flip:  # Comprar (aposta longa)
            self.order = self.buy(size=self.current_bet * self.p.leverage)
        else:  # Vender (aposta curta)
            self.order = self.sell(size=self.current_bet * self.p.leverage)

    def notify_trade(self, trade):
       if trade.isclosed:
            profit = trade.pnlcomm
     

            if profit >= self.current_bet:
                self.current_bet = self.p.target_profit
                self.consecutive_losses = 0
            else:
                self.current_bet *= 2
                self.consecutive_losses += 1

                if self.consecutive_losses >= self.p.max_consecutive_losses:
                    self.cool_down_counter = self.p.cool_down_period


class SmaCross(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        pfast=10,  # period for the fast moving average
        pslow=30   # period for the slow moving average
    )

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)  # fast moving average
        sma2 = bt.ind.SMA(period=self.p.pslow)  # slow moving average
        isCrossed = bt.ind.CrossOver(sma1, sma2)  # crossover signal
        print(f"Crossed: {isCrossed}")

        self.crossover = isCrossed  # crossover signal

    def next(self):
        if not self.position:  # not in the market
            if self.crossover > 0:  # if fast crosses slow to the upside
                self.buy(size=0.01)  # enter long
                print('Buy order created')

        elif self.crossover < 0:  # in the market & cross to the downside
            self.close()  # close long position
            print('Sell order created')


class MyStrategy(bt.Strategy):

    def __init__(self):
        self.dataclose = self.datas[0].close

    def next(self):
         # Sortear um valor aleatório entre 0 e 1
        flip = int(random.random() > 0.5)  # Alterar bt.random() para random.random()

        if flip == 1:
            # Comprar
            self.buy(size=0.01)

        else:
            # Vender
            self.sell(size=0.01)

# (Restante do código da estratégia SmaCross e MyStrategy)

def getpandadata(symbol, timeframe):
    exchange = ccxt.binance()

    # Obter os dados de OHLCV
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    data = bt.feeds.PandasData(dataname=df, datetime="timestamp", open="open", high="high", low="low", close="close", volume="volume")

    return data


if __name__ == "__main__":
    # Configurar a exchange
  
    # Configurar o backtest
    cerebro = bt.Cerebro()
    cerebro.addstrategy(DoubleLeverage)
    cerebro.adddata(data)
    cerebro.broker.setcash(10000)
    cerebro.broker.setcommission(commission=0.001)

    # Executar o backtest
    cerebro.run()
    # Imprimir o valor final da carteira
    print("Valor final da carteira: %.2f" % cerebro.broker.getvalue())
    print("Valor final de cash: %.2f" % cerebro.broker.getcash())
    # Plotar o gráfico de timeframe de 5 minutos    
    #b = Bokeh(style='bar')
    cerebro.plot()
