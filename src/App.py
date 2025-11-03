import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import matplotlib.pyplot as plt
# =====================
# Load & preprocess data
# =====================
df = pd.read_csv("utc/src/Banglore_traffic_Dataset.csv")
# Convert Date to datetime
df['Date'] = pd.to_datetime(df['Date'])
df = df.set_index('Date').sort_index()

# Add extra time-based features
df['DayOfWeek'] = df.index.dayofweek   # 0=Monday, 6=Sunday
df['Month'] = df.index.month           # 1-12a

# Features (X) and Target (y)
features = ['Congestion Level', 'DayOfWeek', 'Month']
data = df[features].values

# Train-Test Split (80% train, 20% test)
train_size = int(len(data) * 0.8)
train, test = data[:train_size], data[train_size:]

# Scale separately to avoid leakage
scaler = MinMaxScaler(feature_range=(0,1))
scaled_train = scaler.fit_transform(train)
scaled_test = scaler.transform(test)

# =====================
# Create sequences
# =====================
def create_sequences(data, seq_len=60):
    X, y = [], []
    for i in range(seq_len, len(data)):
        X.append(data[i-seq_len:i])   # all features in the sequence
        y.append(data[i, 0])          # predict congestion level only
    return np.array(X), np.array(y)

seq_len = 60
X_train, y_train = create_sequences(scaled_train, seq_len)
X_test, y_test = create_sequences(scaled_test, seq_len)

# =====================
# Build LSTM model
# =====================
model = Sequential([
    LSTM(100, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])),
    Dropout(0.2),
    LSTM(100, return_sequences=False),
    Dropout(0.2),
    Dense(50, activation='relu'),
    Dense(1)
])
model.compile(optimizer='adam', loss='mse')
# =====================
# Train model
# =====================
es = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

history = model.fit(
    X_train, y_train,
    validation_data=(X_test, y_test),
    epochs=50,
    batch_size=32,
    callbacks=[es],
    verbose=1
)
# =====================
# Predictions
# =====================
predicted = model.predict(X_test)

# Only inverse transform congestion level (first column)
# Build dummy array with predictions replacing column 0
dummy = np.zeros((predicted.shape[0], scaled_test.shape[1]))
dummy[:,0] = predicted[:,0]
predicted = scaler.inverse_transform(dummy)[:,0]

# Actual values (inverse transform y_test)
dummy_actual = np.zeros((len(y_test), scaled_test.shape[1]))
dummy_actual[:,0] = y_test
actual = scaler.inverse_transform(dummy_actual)[:,0]

# =====================
# Evaluation
# =====================
mse = mean_squared_error(actual, predicted)
mae = mean_absolute_error(actual, predicted)
print("MSE:", mse)
print("MAE:", mae)

# =====================
# Plot Results
# =====================
plt.figure(figsize=(12,6))
plt.plot(df.index[train_size+seq_len:], actual, label="Actual Traffic")
plt.plot(df.index[train_size+seq_len:], predicted, label="Predicted Traffic")
plt.legend()
plt.title("Bangalore Traffic Prediction (LSTM with Features)")
plt.xlabel("Date")
plt.ylabel("Congestion Level")
plt.show()