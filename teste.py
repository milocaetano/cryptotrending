class MyRow:
    def __init__(self, timestamp, open_price, high, low, close):
        self.timestamp = timestamp
        self.open_price = open_price
        self.high = high
        self.low = low
        self.close = close

    def __getitem__(self, key):
        if key == "timestamp":
            return self.timestamp
        elif key == "open_price":
            return self.open_price
        elif key == "high":
            return self.high
        elif key == "low":
            return self.low
        elif key == "close":
            return self.close
        else:
            raise KeyError(f"Key '{key}' not found")

# Exemplo de dados
data = [
    {"timestamp": "2023-04-30 00:00:00", "open_price": 1.0, "high": 1.1, "low": 0.9, "close": 1.05},
    {"timestamp": "2023-04-30 01:00:00", "open_price": 1.05, "high": 1.15, "low": 0.95, "close": 1.1},
]

rows = []
for row_data in data:
    my_row = MyRow(**row_data)
    rows.append(my_row)


for row in rows:
    print(row.timestamp)
    print(row["timestamp"])







# Criação da lista de objetos MyRow
rows = [MyRow(**row_data) for row_data in data]

# Iterar pelos objetos MyRow e acessar os valores das colunas usando a notação de colchetes
for row in rows:
    print(row["timestamp"])
    print(row["open_price"])
    print(row["high"])
    print(row["low"])
    print(row["close"])
