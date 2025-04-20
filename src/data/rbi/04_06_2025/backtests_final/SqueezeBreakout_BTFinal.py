Here's the debugged version of your SqueezeBreakout strategy with all technical fixes while preserving the original strategy logic:

```python
# 🌙 Moon Dev SqueezeBreakout Backtest ✨
import pandas as pd
import talib
import numpy as np
from backtesting import Backtest, Strategy

# =====================
# DATA PREPARATION 🌙
# =====================
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"

# Load and clean data
data = pd.read_csv(data_path, parse_dates=['datetime'])
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Column mapping for backtesting.py
required_columns = {
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume',
    'tick': 'Tick'  # Ensure Tick data exists in CSV
}
data = data.rename(columns=required_columns)
data = data[['Open', 'High', 'Low', 'Close', 'Volume', 'Tick']]

# =====================
# STRATEGY CLASS 🚀
# =====================
class SqueezeBreakout(Strategy):
    risk_per_trade = 0.01  # 1% risk per trade
    rr_ratio = 2  # Risk:Reward ratio
    time_exit_bars = 3  # Bars until time exit

    def init(self):
        # 🌙 Keltner Channel Indicators
        self.ema = self.I(talib.EMA, self.data.Close, timeperiod=20)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=20)
        self.upper_kc = self.I(lambda: self.ema + 2*self.atr)
        self.lower_kc = self.I(lambda: self.ema - 2*self.atr)
        
        # ✨ Consolidation Detection
        self.kc_width = self.I(lambda: self.upper_kc - self.lower_kc)
        self.kc_width_avg = self.I(talib.SMA, self.kc_width, timeperiod=20)
        
        # 📉 Volume Confirmation
        self.volume_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        
        # 🔍 Swing High/Low for Stops
        self.swing_high = self.I(talib.MAX, self.data.High, timeperiod=20)
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=20)
        
        self.trade_active = False

    def next(self):
        # Wait for sufficient data
        if len(self.data.Close) < 20:
            return

        # 🌙 Current Market Conditions
        current_close = self.data.Close[-1]
        consolidation = self.kc_width[-1] < self.kc_width_avg[-1]
        volume_ok = self.data.Volume[-1] > self.volume_sma[-1]  # Fixed volume condition (should be > for breakout)
        tick_value = self.data.Tick[-1]

        # 🚀 Long Entry Conditions
        long_signal = (
            consolidation and
            volume_ok and
            current_close > self.upper_kc[-1] and
            tick_value > 500
        )

        # 🌑 Short Entry Conditions
        short_signal = (
            consolidation and
            volume_ok and
            current_close < self.lower_kc[-1] and
            tick_value < -500
        )

        # 💰 Risk Management Calculations
        if not self.position:
            if long_signal:
                self.enter_long()
            elif short_signal:
                self.enter_short()
        else:
            self.check_exits()

    def enter_long(self):
        entry_price = self.data.Close[-1]
        stop_price = self.swing_low[-1]
        risk_distance = entry_price - stop_price
        
        if risk_distance <= 0:
            print(f"✨ Moon Dev Alert: Invalid long stop at {stop_price:.2f}")
            return

        position_size = (self.equity * self.risk_per_trade) / risk_distance
        take_profit = entry_price + self.rr_ratio * risk_distance
        
        self.buy(
            size=round(position_size, 2),  # Properly rounded position size
            sl=stop_price,
            tp=take_profit,
            tag={'entry_bar': len