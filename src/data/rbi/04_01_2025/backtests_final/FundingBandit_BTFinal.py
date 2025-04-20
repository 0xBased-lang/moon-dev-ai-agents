Here's the debugged version of your FundingBandit backtest code with Moon Dev themed improvements 🌙✨:

```python
# 🌙 Moon Dev's FundingBandit Backtest Implementation
from backtesting import Strategy, Backtest
import talib
import pandas as pd
import numpy as np

class FundingBandit(Strategy):
    # Strategy parameters 🌙
    bb_period = 20
    bb_dev = 2
    high_funding = 0.001  # 0.1% threshold
    normal_funding = 0.0005  # Exit threshold
    risk_pct = 0.01  # 1% risk per trade
    trail_stop = 0.03  # 3% trailing stop

    def init(self):
        # Initialize Bollinger Bands using TA-Lib 🌙📈
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS,
            self.data.Close,
            timeperiod=self.bb_period,
            nbdevup=self.bb_dev,
            nbdevdn=self.bb_dev,
            matype=talib.MA_Type.SMA
        )
        
        # Print Moon Dev initialization message 🌙✨
        print("🌙✨ Moon Dev Indicators Activated! Tracking Funding Bandit Signals...")
        print("   All indicators powered by pure TA-Lib magic ✨")

    def next(self):
        current_close = self.data.Close[-1]
        current_funding = self.data.Funding_Rate[-1]
        
        # Entry Logic 🌙🚀
        if not self.position:
            if (current_close < self.bb_lower[-1]) and (current_funding > self.high_funding):
                # Risk management calculation 🌙💰
                risk_amount = self.equity * self.risk_pct
                risk_per_unit = current_close * self.trail_stop
                position_size = int(round(risk_amount / risk_per_unit))
                
                if position_size > 0:
                    self.buy(size=position_size)
                    self.trailing_high = current_close  # Initialize trailing high
                    print(f"🌙🚀 MOON ENTRY! Price: {current_close:.2f}, Size: {position_size} units")
                    print(f"   Funding Rate: {current_funding:.4%} 🌡️, Lower BB: {self.bb_lower[-1]:.2f} 📉")

        # Exit Logic 🌙🛑
        elif self.position:
            # Update trailing high 🌙📈
            self.trailing_high = max(self.trailing_high, self.data.High[-1])
            stop_price = self.trailing_high * (1 - self.trail_stop)

            # Trailing stop check 🌙🔍
            if self.data.Low[-1] <= stop_price:
                self.position.close()
                print(f"🌙🛑 TRAILING STOP! Exit at: {stop_price:.2f}")
            
            # Funding normalization check 🌙🌡️
            elif current_funding < self.normal_funding:
                self.position.close()
                print(f"🌙🛑 FUNDING NORMALIZED! Rate: {current_funding:.4%}")

# Data Preparation 🌙📂
try:
    data = pd.read_csv(
        "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv",
        parse_dates=['datetime'],
        index_col='datetime'
    )
except FileNotFoundError:
    print("🌙⚠️ MOON ALERT! Data file not found. Please check the path.")
    raise

# Clean and format data 🌙🧹
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume',
    'funding_rate': 'Funding_Rate'  # Must exist in original data
})

# Verify required columns exist 🌙🔍
required_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'Funding_Rate']
if not all(col in data.columns for col in required_cols):
    missing = [col for col in required_cols if col not in data.columns]
    print(f"🌙⚠️ CRITICAL MOON ALERT! Missing columns: {missing}")
    raise ValueError("Required data columns missing")

# Run Backtest 🌙⚡
bt = Backtest(data, FundingBandit, cash=