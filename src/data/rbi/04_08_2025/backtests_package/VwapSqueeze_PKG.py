Here's the fixed code with all backtesting.lib imports removed and replaced with proper implementations, along with Moon Dev themed improvements:

```python
import pandas as pd
import talib
import pandas_ta as ta
from backtesting import Backtest, Strategy
import numpy as np  # Added for array operations 🌙

class VwapSqueeze(Strategy):
    risk_percent = 0.01  # 1% risk per trade 🌙
    
    def init(self):
        # Add indicators using proper self.I() wrapper
        self.vwap = self.I(ta.vwap, 
                          high=self.data.High, 
                          low=self.data.Low, 
                          close=self.data.Close,
                          volume=self.data.Volume,
                          name='VWAP')
        
        # Bollinger Bands (20,2)
        self.bb_upper = self.I(lambda c: talib.BBANDS(c, 20, 2, 2)[0], self.data.Close)
        self.bb_lower = self.I(lambda c: talib.BBANDS(c, 20, 2, 2)[2], self.data.Close)
        
        # Volume SMA for confirmation
        self.volume_sma = self.I(talib.SMA, self.data.Volume, 20)
        
        # Track band width history for squeeze detection
        self.band_width_history = []

    def next(self):
        # Wait for sufficient data 🌙
        if len(self.data) < 20 or len(self.vwap) < 3:
            return

        current_close = self.data.Close[-1]
        current_vwap = self.vwap[-1]
        prev_vwap = self.vwap[-2]
        
        # Calculate Bollinger Band width
        bb_width = self.bb_upper[-1] - self.bb_lower[-1]
        self.band_width_history.append(bb_width)
        if len(self.band_width_history) > 20:
            self.band_width_history.pop(0)
            
        # Detect squeeze (20-period low in BB width) ✨
        squeeze = bb_width <= min(self.band_width_history[-20:]) if len(self.band_width_history) >= 20 else False
        
        # Volume confirmation check
        volume_ok = self.data.Volume[-1] > self.volume_sma[-1]
        
        # VWAP slope calculation
        vwap_slope = current_vwap - prev_vwap

        # Moon Dev Risk Management System 🚀
        def calculate_size(entry_price, stop_price):
            risk_amount = self.equity * self.risk_percent
            risk_per_unit = abs(entry_price - stop_price)
            return int(round(risk_amount / risk_per_unit)) if risk_per_unit > 0 else 0

        # Entry Logic 🌙✨
        if not self.position:
            if squeeze and volume_ok:
                # Long Entry (replaced crossover with direct comparison)
                if (self.data.Close[-2] <= self.vwap[-2]) and (current_close > current_vwap):
                    sl = self.bb_lower[-1]
                    size = calculate_size(current_close, sl)
                    if size > 0:
                        self.buy(size=size, sl=sl)
                        print(f"🌙🚀 MOON DEV LONG SIGNAL! Size: {size} | Entry: {current_close} | SL: {sl}")
                
                # Short Entry (replaced crossunder with direct comparison)
                elif (self.data.Close[-2] >= self.vwap[-2]) and (current_close < current_vwap):
                    sl = self.bb_upper[-1]
                    size = calculate_size(current_close, sl)
                    if size > 0:
                        self.sell(size=size, sl=sl)
                        print(f"🌙🚀 MOON DEV SHORT SIGNAL! Size: {size} | Entry: {current_close} | SL: {sl}")

        # Exit Logic 💫
        else:
            if self.position.is_long:
                if (vwap_slope < 0) and (current_close < current_vwap):
                    self.position.close()
                    print(f"🌙💫 LONG EXIT | Price: {current_close} | VWAP Slope Turning Bearish")
                    
            elif self.position.is_short:
                if (vwap_slope > 0) and (current_close > current_vwap):
                    self.position.close()
                    print(f"🌙💫 SHORT EXIT | Price: {current_close} | VWAP Slope Turning Bullish")

# Data preprocessing 🌙
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip