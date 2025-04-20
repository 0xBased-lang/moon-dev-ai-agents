I'll debug the code while maintaining the original strategy logic. Here's the fixed version with Moon Dev themed debug prints:

```python
# 🌙 Moon Dev Backtest Engine: ChaikinBandwidth Strategy Implementation ✨
# 🚀 Version 1.0 - Debugged by Moon Dev AI

import pandas as pd
from backtesting import Backtest, Strategy
import talib
import numpy as np

class ChaikinBandwidth(Strategy):
    risk_pct = 0.01
    bb_period = 20
    bb_dev = 2
    chaikin_fast = 3
    chaikin_slow = 10
    swing_period = 20
    bandwidth_threshold = 0.5
    tp_multiplier = 1.5

    def init(self):
        # 🌙 Chaikin Oscillator with Volume Magic
        self.chaikin = self.I(talib.ADOSC, self.data.High, self.data.Low, 
                            self.data.Close, self.data.Volume, 
                            fastperiod=self.chaikin_fast, 
                            slowperiod=self.chaikin_slow)
        
        # ✨ Bollinger Bands Configuration
        self.upper, self.middle, self.lower = self.I(talib.BBANDS, 
                                                   self.data.Close, 
                                                   timeperiod=self.bb_period,
                                                   nbdevup=self.bb_dev,
                                                   nbdevdn=self.bb_dev)
        
        # 🚀 Bandwidth Calculation
        self.bb_width = (self.upper - self.lower) / self.middle
        self.bb_width_ma = self.I(talib.SMA, self.bb_width, timeperiod=self.bb_period)
        
        # 🌙 Swing Detection System
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=self.swing_period)
        self.swing_high = self.I(talib.MAX, self.data.High, timeperiod=self.swing_period)
        
        # ✨ Divergence Detection Indicators
        self.price_low_roll = self.I(talib.MIN, self.data.Low, timeperiod=5)
        self.chaikin_low_roll = self.I(talib.MIN, self.chaikin, timeperiod=5)
        self.price_high_roll = self.I(talib.MAX, self.data.High, timeperiod=5)
        self.chaikin_high_roll = self.I(talib.MAX, self.chaikin, timeperiod=5)

    def next(self):
        if len(self.data) < max(self.bb_period, self.swing_period, 5) + 1:
            return

        # 🌙 Current Market Conditions
        current_close = self.data.Close[-1]
        chaikin = self.chaikin[-1]
        bb_width = self.bb_width[-1]
        bb_width_ma = self.bb_width_ma[-1]

        # ✨ Long Entry Logic
        if not self.position:
            # Bullish Divergence Check
            bull_div = (self.price_low_roll[-1] < self.price_low_roll[-2] and
                       self.chaikin_low_roll[-1] > self.chaikin_low_roll[-2])
            
            # Volatility Contraction
            vol_contraction = bb_width < bb_width_ma * self.bandwidth_threshold
            
            # Price Confirmation
            price_confirm = current_close > self.middle[-1]

            if bull_div and vol_contraction and price_confirm:
                # 🚀 Risk Management Calculation
                sl_price = min(self.swing_low[-1], self.lower[-1])
                risk_per_share = current_close - sl_price
                if risk_per_share > 0:
                    size = int(round((self.equity * self.risk_pct) / risk_per_share))
                    if size > 0:  # 🌙 Ensure valid position size
                        self.buy(size=size, sl=sl_price)
                        self.entry_width = bb_width
                        print(f"🌙🚀 BULLISH BREAKOUT! Size: {size} | Entry: {current_close:.2f} | SL: {sl_price:.2f}")

            # ✨ Short Entry Logic
            # Bearish Divergence Check
            bear_div = (self.price_high_roll[-1] > self.price_high_roll[-2] and
                       self.chaikin_high_roll[-1] < self.chaikin_high_roll[-2])
            
            # Price Confirmation
            price_confirm_short = current_close < self.middle[-1]

            if bear_div and vol_contraction and price_confirm_short: