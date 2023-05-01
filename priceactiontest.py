import backtrader as bt
import ccxt
import pandas as pd
import numpy as np
import datetime
# Defina sua chave API e segredo aqui
api_key = "sua_api_key"
api_secret = "seu_api_secret"

# Defina o par de ativos e intervalo de tempo aqui
symbol = "ALPHA/USDT"
timeframe = "5m"

class CongestionStrategy(bt.Strategy):
    params = (
        ("sma14", 14),
        ("sma21", 21),
        ("sma99", 50),
        ("lookback", 5),
        ("congestion_lookback", 14),
        ("congestion_threshold", 0.01),
        ("stop_loss", 0.01),  # Parâmetro de stop loss
        ("take_profit", 0.02),  # Parâmetro de take profit
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

        self.sma14 = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.sma14
        )
        self.sma21 = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.sma21
        )
        self.sma99 = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.sma99
        )

        self.order = None  # Para rastrear uma ordem pendente

    def next(self):
        if self.order:  # Se houver uma ordem pendente, não faça nada
            return

        if not self.position:  # Se não estivermos no mercado, verifique a possibilidade de entrar
            trend, candle, congestion_chance = self.analyze_trend()
            congestion_chance= False
            if trend == "Alta" and not congestion_chance:
                self.order = self.buy()
                self.stop_price = self.data.close[0] * (1 - self.params.stop_loss)
                self.take_profit_price = self.data.close[0] * (1 + self.params.take_profit)

            elif trend == "Baixa" and not congestion_chance:
                self.order = self.sell()
                self.stop_price = self.data.close[0] * (1 + self.params.stop_loss)
                self.take_profit_price = self.data.close[0] * (1 - self.params.take_profit)

        else:  # Se estivermos no mercado, verifique se é hora de sair
            if self.position.size > 0:  # Estamos comprados (long)
                if self.data.close[0] <= self.stop_price or self.data.close[0] >= self.take_profit_price:
                    self.order = self.sell()  # Venda para fechar a posição

            elif self.position.size < 0:  # Estamos vendidos (short)
                if self.data.close[0] >= self.stop_price or self.data.close[0] <= self.take_profit_price:
                    self.order = self.buy()  # Compre para fechar a posição

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            self
            if order.isbuy():
                print(f"{bt.num2date(order.executed.dt)}: Comprado ao preço {order.executed.price:.2f}")
            elif order.issell():
                print(f"{bt.num2date(order.executed.dt)}: Vendido ao preço {order.executed.price:.2f}")

        self.order = None

    def calculate_congestion(self):
        close_prices = self.dataclose.get(size=self.params.congestion_lookback + 1)
        pct_changes = [(close_prices[i + 1] - close_prices[i]) / close_prices[i] for i in range(len(close_prices) - 1)]
        pct_changes_abs = np.abs(pct_changes)
        avg_pct_change = np.mean(pct_changes_abs)

        return avg_pct_change < self.params.congestion_threshold

    def analyze_trend(self):
        sma99_trending_up = self.sma99[-1] > self.sma99[-2]
        sma99_trending_down = self.sma99[-1] < self.sma99[-2]

        if (
            self.sma14[-1] > self.sma21[-1]
            and self.sma99[-1] < self.sma21[-1]
            and self.sma99[-1] < self.sma14[-1]
            and sma99_trending_up
        ):
            trend = "Alta"
        elif (
            self.sma14[-1] < self.sma21[-1]
            and self.sma99[-1] > self.sma21[-1]
            and self.sma99[-1] > self.sma14[-1]
            and sma99_trending_down
        ):
            trend = "Baixa"
        else:
            trend = "Neutro"

        congestion_chance = self.calculate_congestion()

        return trend, None, congestion_chance

if __name__ == "__main__":
    # Configurar a exchange
    # Calcula a data de um mês atrás
    now = datetime.datetime.now()
    one_month_ago = now - datetime.timedelta(days=30)

    # Configurar a exchange
    exchange = ccxt.binance()

    # Obter os dados de OHLCV do último mês
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=int(one_month_ago.timestamp() * 1000))
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    data = bt.feeds.PandasData(dataname=df, datetime="timestamp", open="open", high="high", low="low", close="close", volume="volume")

    # Configurar o backtest
    cerebro = bt.Cerebro()
    cerebro.addstrategy(CongestionStrategy)
    cerebro.adddata(data)
    cerebro.broker.setcash(10000)
    cerebro.broker.setcommission(commission=0.001)

    # Executar o backtest
    cerebro.run()
    cerebro.plot()

    # Imprimir o valor final da carteira
    print("Valor final da carteira: %.2f" % cerebro.broker.getvalue())
