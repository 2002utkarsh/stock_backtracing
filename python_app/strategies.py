import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

def moving_average_crossover(df, short_window=50, long_window=200):
    """
    Generates trading signals based on a moving average crossover strategy.
    """
    signals = pd.DataFrame(index=df.index)
    signals['signal'] = 0.0

    # Create short and long simple moving averages (using lowercase 'close')
    signals['short_mavg'] = df['close'].rolling(window=short_window, min_periods=1, center=False).mean()
    signals['long_mavg'] = df['close'].rolling(window=long_window, min_periods=1, center=False).mean()

    # Get index labels from the short_window position onwards, then use with .loc
    signals.loc[signals.index[short_window:], 'signal'] = \
        np.where(signals['short_mavg'][short_window:] > signals['long_mavg'][short_window:], 1, 0)

    # Take the difference of the signals to get actual trading orders
    signals['positions'] = signals['signal'].diff()
    
    # Map positions to buy/sell signals
    trade_signals = signals['positions'].replace({1.0: 1, -1.0: -1, 0.0: 0})
    
    return trade_signals

def ml_strategy(df):
    """
    Generates trading signals using a simple Logistic Regression model.
    """
    # 1. Feature Engineering (using lowercase 'close')
    df['sma50'] = df['close'].rolling(50).mean()
    df['sma200'] = df['close'].rolling(200).mean()
    df['return'] = df['close'].pct_change()
    df['volatility'] = df['return'].rolling(20).std()
    df.dropna(inplace=True)
    
    features = ['sma50', 'sma200', 'volatility']
    X = df[features]
    
    # 2. Target Variable (using lowercase 'close')
    df['target'] = np.where(df['close'].shift(-5) > df['close'], 1, 0)
    y = df['target']
    
    if len(X) == 0:
        return pd.Series(0, index=df.index)

    # 3. Train the model
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    model = LogisticRegression()
    model.fit(X_train, y_train)
    
    # 4. Generate Predictions/Signals
    all_predictions = model.predict(X)
    signals = pd.Series(all_predictions, index=X.index).reindex(df.index).fillna(0)
    
    trade_signals = signals.diff().fillna(0)
    trade_signals = trade_signals.replace({1.0: 1, -1.0: -1})
    
    return trade_signals