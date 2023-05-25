import matplotlib.pyplot as plt
import getdata as gd
import plotly.graph_objects as go

def plot_candlestick(dados, symbol):
    fig = go.Figure(data=[go.Candlestick(x=dados['timestamp'],
                                         open=dados['Open'],
                                         high=dados['High'],
                                         low=dados['Low'],
                                         close=dados['Close'])])
    fig.update_layout(title=f'{symbol} Candlestick Chart',
                      xaxis_title='Date',
                      yaxis_title='Price',
                      xaxis_rangeslider_visible=False)
    fig.show()
    

def plot_data(dados, symbol):
    plt.figure(figsize=(15, 7))
    plt.plot(dados["timestamp"], dados["Close"], label="Close Price")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.title(f"{symbol} Close Price")
    plt.legend()
    plt.show()


if(__name__ == '__main__'):

    symbol = "BTCUSDT"
    dados= gd.get_data(symbol, "5m", "202304190300", "202304221300")
    plot_data(dados, symbol)
    plot_candlestick(dados, symbol)