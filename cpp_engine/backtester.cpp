#include "backtester.h"
#include <vector>
#include <iostream>

// The core simulation function exposed to Python.
// It takes historical price data and a list of trading signals.
void run_simulation(
    const StockTick* ticks, 
    int num_ticks, 
    const int* signals, // 1 for Buy, -1 for Sell, 0 for Hold
    double* portfolio_history // Output array to store results
) {
    Portfolio portfolio(10000.0); // Start with $10,000 cash

    for (int i = 0; i < num_ticks; ++i) {
        const StockTick& current_tick = ticks[i];

        // Execute trade based on the signal for the current day.
        if (signals[i] == 1) { // Buy Signal
            portfolio.execute_buy(current_tick);
        } else if (signals[i] == -1) { // Sell Signal
            portfolio.execute_sell(current_tick);
        }

        // Record the total portfolio value for this time step.
        portfolio_history[i] = portfolio.get_total_value(current_tick);
    }
}

// This 'extern "C"' block is crucial. It tells the C++ compiler
// to generate a function that Python's ctypes can understand.
extern "C" {
    void perform_backtest(const StockTick* ticks, int num_ticks, const int* signals, double* portfolio_history) {
        run_simulation(ticks, num_ticks, signals, portfolio_history);
    }
}