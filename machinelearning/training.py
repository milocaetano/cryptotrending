import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from tensorflow import keras
from keras.layers import Dense
from keras.models import Sequential

def read_data_from_folder(folder):
    all_data = []
    for file in os.listdir(folder):
        if file.endswith(".csv"):
            file_path = os.path.join(folder, file)
            data = pd.read_csv(file_path)
            all_data.append(data)
    if not all_data:  # Adicionada a verificação aqui
        print(f"No CSV files found in {folder}")
        return pd.DataFrame()
    return pd.concat(all_data, ignore_index=True)

folder = "C:\\Machine\\"
downtrend_data = read_data_from_folder(f"{folder}downtrend")
uptrend_data = read_data_from_folder(f"{folder}/uptrend")
congestion_data = read_data_from_folder(f"{folder}/congestion")

merged_data = pd.concat([downtrend_data, uptrend_data, congestion_data], ignore_index=True)

# Remova as colunas 'Label' e 'timestamp'
X = merged_data.drop(columns=['Label', 'timestamp'])

y = merged_data['Label']

# Normalize os dados
min_vals = np.min(X, axis=0)
max_vals = np.max(X, axis=0)
X_normalized = (X - min_vals) / (max_vals - min_vals)

# Converta os rótulos para valores numéricos
label_mapping = {'uptrend': 0, 'downtrend': 1, 'congestion': 2}
y_numerical = y.replace(label_mapping)

# Divida os dados em conjuntos de treinamento e teste
X_train, X_test, y_train, y_test = train_test_split(X_normalized, y_numerical, test_size=0.2, random_state=42)

model = Sequential([
    Dense(32, activation='relu', input_shape=(X_train.shape[1],)),
    Dense(16, activation='relu'),
    Dense(3, activation='softmax')
])

model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

model.fit(X_train, y_train, epochs=50, batch_size=32, validation_split=0.2)
loss, accuracy = model.evaluate(X_test, y_test)
print(f"Accuracy: {accuracy:.2f}")
model.save(f"{folder}\\output\\crypto_trend_classifier.h5")
