import pandas as pd
import torch
import torch.nn as nn
import numpy as np
import math
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

class StockLSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, output_dim):
        super(StockLSTM, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).requires_grad_()
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).requires_grad_()
        out, _ = self.lstm(x, (h0.detach(), c0.detach()))
        out = self.fc(out[:, -1, :]) 
        return out


class StockPredictor:
    def __init__(self):
        self.scaler = MinMaxScaler(feature_range=(-1, 1))
        self.look_back = 50
        self.input_dim = 1
        self.hidden_dim = 32
        self.num_layers = 2
        self.output_dim = 1

    def load_data(self, train_data):
        train_data = self.scaler.fit_transform(train_data.reshape(-1, 1))
        data = []
        for index in range(len(train_data) - self.look_back):
            data.append(train_data[index: index + self.look_back])
        data = np.array(data)
        x_train = data[:, :-1]
        y_train = data[:, -1]
        self.x_train = torch.from_numpy(x_train).type(torch.Tensor)
        self.y_train = torch.from_numpy(y_train).type(torch.Tensor)

    def train_model(self, num_epochs=300):
        self.model = StockLSTM(self.input_dim, self.hidden_dim, self.num_layers, self.output_dim)
        loss_fn = torch.nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)
        hist = np.zeros(num_epochs)
        for t in range(num_epochs):
            y_train_pred = self.model(self.x_train)
            loss = loss_fn(y_train_pred, self.y_train)
            hist[t] = loss.item()
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            if t % 10 == 0 and t != 0:
                print("Epoch ", t, "MSE: ", loss.item())
        self.trained_model = self.model
        self.history = hist

    def predict(self, test_data):
        test_data = self.scaler.transform(test_data.reshape(-1, 1))
        data = []
        for index in range(len(test_data) - self.look_back):
            data.append(test_data[index: index + self.look_back])
        data = np.array(data)
        x_test = data[:, :-1]
        y_test = data[:, -1]
        self.x_test = torch.from_numpy(x_test).type(torch.Tensor)
        self.y_test = torch.from_numpy(y_test).type(torch.Tensor)

        y_test_pred = self.trained_model(self.x_test)
        self.predicted_values = self.scaler.inverse_transform(y_test_pred.detach().numpy())
        self.y_test_original = self.scaler.inverse_transform(self.y_test)

    def calculate_rmse(self):
        test_score = math.sqrt(mean_squared_error(self.y_test_original, self.predicted_values))
        print('Test Score: %.2f RMSE' % (test_score))

    def plot_results(self):
        figure, axes = plt.subplots(figsize=(15, 6))
        axes.plot(range(len(self.y_test_original)), self.y_test_original, color='red', label='Real Stock Price')
        axes.plot(range(len(self.y_test_original)), self.predicted_values, color='blue', label='Predicted Stock Price')
        plt.title('Stock Price Prediction')
        plt.xlabel('Day')
        plt.ylabel('Stock Price')
        plt.legend()
        plt.show()

# Usage example:
if __name__ == "__main__":
    # Create an instance of StockPredictor
    predictor = StockPredictor()

    data = pd.read_csv("stocks/SBER.csv", sep=';')
    need_data = data['<CLOSE>']  
    window_size = 10
    moving_average = need_data.rolling(window=window_size).mean()
    moving_average.dropna(inplace=True)
    
    train_data, test_data = train_test_split(moving_average.values, test_size=0.1, shuffle=False)


    # Load and train the model
    predictor.load_data(train_data)
    predictor.train_model()

    # Predict and evaluate
    predictor.predict( torch.from_numpy(test_data[:, :-1]))
    predictor.calculate_rmse()
    predictor.plot_results()
