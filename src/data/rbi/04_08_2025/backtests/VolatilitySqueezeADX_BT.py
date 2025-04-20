```python
# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import talib
from backtesting import Strategy, Backtest

class VolatilitySqueezeADX(Strategy):
    adx_period = 14
    bb_period = 20
    risk_percent = 0.01
    lookback_period = 35040  # 1 year in 15m intervals
    
    def init(self):
        # Clean and prepare data
        self.data.df.columns = self.data.df.columns.str.strip().str.lower()
        self.data.df = self.data.df.drop(columns=[col for col in self.data.df.columns if 'unnamed' in col])
        
        # Calculate indicators using TA-Lib
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, self.adx_period)
        self.plus_di = self.I(talib.PLUS_DI, self.data.High, self.data.Low, self.data.Close, self.adx_period)
        self.minus_di = self.I(talib.MINUS_DI, self.data.High, self.data.Low, self.data.Close, self.adx_period)
        
        # Bollinger Bands components
        upper, middle, lower = self.I(talib.BBANDS, self.data.Close, self.bb_period, 2, 2, 0)
        self.bbw = (upper - lower) / middle
        
        # BBW percentile calculation
        self.bbw_percentile = self.I(lambda x: x.rolling(self.lookback_period).quantile(0.2), self.bbw)
        
        # Volatility measurement
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 14)
        
        print("🌙 Moon Dev Indicators Initialized! BBW/ADX/ATR Ready for Action! 🚀")

    def next(self):
        current_price = self.data.Close[-1]
        current_time = self.data.index[-1]
        
        if len(self.adx) < 3 or len(self.bbw) < self.lookback_period:
            return
            
        # Current indicator values
        adx_val = self.adx[-1]
        bbw_val = self.bbw[-1]
        bbw_pct = self.bbw_percentile[-1]
        di_diff = self.plus_di[-1] - self.minus_di[-1]
        
        # Entry conditions
        volatility_squeeze = bbw_val < bbw_pct
        strong_trend = adx_val > 25
        trend_direction = "LONG" if di_diff > 0 else "SHORT"
        
        print(f"🌙 Moon Dev Scanning: {current_time} | ADX: {adx_val:.1f} | BBW: {bbw_val:.4f} | Trend: {trend_direction}")
        
        # Entry logic
        if not self.position:
            if volatility_squeeze and strong_trend:
                risk_amount = self.equity * self.risk_percent
                atr_val = self.atr[-1] if self.atr[-1] > 0 else 0.01
                position_size = int(round(risk_amount / (2 * atr_val)))
                
                if di_diff > 0:
                    self.buy(size=position_size, sl=current_price - 2*atr_val)
                    print(f"🚀 MOON LAUNCH! LONG {position_size} @ {current_price:.2f} | SL: {current_price-2*atr_val:.2f}")
                else:
                    self.sell(size=position_size, sl=current_price + 2*atr_val)
                    print(f"🌑 BLACK HOLE! SHORT {position_size} @ {current_price:.2f} | SL: {current_price+2*atr_val:.2f}")
        
        # Exit logic
        else:
            position = self.position
            entry_threshold = position.entry_price * (1 + position.size/abs(position.size)*0.01)
            
            exit_condition1 = self.adx[-1] < 20
            exit_condition2 = self.bbw[-1] > bbw_pct
            
            if exit_condition1 or exit_condition2:
                self.position.close()
                print(f"✨ STARDUST EXIT! Closed @ {current_price:.2f} | Reason: {'ADX Drop' if exit_condition1 else 'Vol Expansion'}")

# Data preparation
data = pd.read_csv("/Users/md