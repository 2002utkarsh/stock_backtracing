import ctypes
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from strategies import moving_average_crossover, ml_strategy

# 1. Define the C++ structure in Python
class StockTick(ctypes.Structure):
    _fields_ = [("timestamp", ctypes.c_longlong),
                ("open", ctypes.c_double),
                ("high", ctypes.c_double),
                ("low", ctypes.c_double),
                ("close", ctypes.c_double),
                ("volume", ctypes.c_int)]

# 2. Load the compiled C++ library
# --- Find this section in your main.py file ---

# 2. Load the compiled C++ library
try:
    engine = ctypes.CDLL('../cpp_engine/libbacktester.so')
except OSError:
    engine = ctypes.CDLL('../cpp_engine/backtester.dll')

# --- And replace it with this: ---

# 2. Load the compiled C++ library
# It's now in the same directory, so the path is very simple.
# engine = ctypes.CDLL('./libbacktester.so')

# 3. Define the function signature from the C++ code
engine.perform_backtest.argtypes = [
    ctypes.POINTER(StockTick),
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_double)
]
engine.perform_backtest.restype = None

# --- Main Application Logic ---

# 4. Ask user for a ticker and download data
ticker = input("▶️ Please enter the stock ticker to backtest (e.g., AAPL, MSFT, SPY): ").upper()

try:
    print(f"⬇️ Downloading historical data for {ticker}...")
    
    # Using the Ticker object is more robust for single stocks and avoids the MultiIndex issue.
    stock_data = yf.Ticker(ticker)
    df = stock_data.history(period="10y", auto_adjust=True)

    if df.empty:
        raise ValueError(f"No data found for ticker '{ticker}'. Please check the symbol.")
    
    # Standardize column names to lowercase for consistency
    df.columns = df.columns.str.lower()
    
    print("✅ Download complete.")
except Exception as e:
    print(f"❌ Error: {e}")
    exit() # Exit if download fails

# 5. Generate trading signals
print("🧠 Generating trading signals...")
# --- CHOOSE YOUR STRATEGY ---
signals = moving_average_crossover(df)
# signals = ml_strategy(df.copy())
# ----------------------------
signals = signals.reindex(df.index).fillna(0)

num_ticks = len(df)

print("✅ Signals generated.")

# 6. Convert pandas DataFrame to an array of C++ structs
ticks_array = (StockTick * num_ticks)()
for i, row in enumerate(df.itertuples()):
    ticks_array[i] = StockTick(
        int(row.Index.timestamp()),
        row.open,
        row.high,
        row.low,
        row.close,
        int(row.volume)
    )

# 7. Prepare signals and output arrays for C++
integer_signals = signals.astype(int)
signals_array = (ctypes.c_int * num_ticks)(*integer_signals.values)

# --- THIS IS THE MISSING LINE THAT HAS BEEN ADDED BACK ---
portfolio_history = (ctypes.c_double * num_ticks)()
# ---------------------------------------------------------

# 8. Call the C++ engine!
print("🚀 Running backtest with C++ engine...")
engine.perform_backtest(ticks_array, num_ticks, signals_array, portfolio_history)
print("✅ Backtest complete.")

# 9. Visualize the results
results = pd.Series(list(portfolio_history), index=df.index)

plt.style.use('seaborn-v0_8-darkgrid')
plt.figure(figsize=(14, 9))

# Plot portfolio value
ax1 = plt.subplot(2, 1, 1)
results.plot(ax=ax1, label="Portfolio Value", color="royalblue")
ax1.set_ylabel("Portfolio Value ($)")
ax1.set_title(f"📈 Performance of Moving Average Crossover on {ticker}")
plt.legend()

# Plot stock price and buy/sell markers
ax2 = plt.subplot(2, 1, 2, sharex=ax1)
df['close'].plot(ax=ax2, label=f"{ticker} Close Price", color="black", alpha=0.7)
ax2.plot(df.loc[signals == 1].index, df['close'][signals == 1], '^', markersize=10, color='lime', lw=0, label='Buy Signal')
ax2.plot(df.loc[signals == -1].index, df['close'][signals == -1], 'v', markersize=10, color='red', lw=0, label='Sell Signal')
ax2.set_ylabel("Stock Price ($)")
plt.legend()

plt.tight_layout()

# At the end of main.py, replace plt.show() with this:
plt.savefig("backtest_results.png")
print("✅ Plot saved to backtest_results.png")