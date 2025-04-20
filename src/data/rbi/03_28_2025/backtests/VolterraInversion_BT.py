```python
# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import talib

# Load and preprocess data
data = pd.read_csv(
    '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv',
    parse_dates=['datetime'],
    index_col='datetime'
)

# Clean column names and drop unnamed columns
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

class VolterraInversion(Strategy):
    risk_percent = 0.05  # 5% maximum allocation
    
    def init(self):
        # Term structure proxies (using SMA crossover)
        self.front_month = self.I(talib.SMA, self.data.Close, 5)
        self.back_month = self.I(talib.SMA, self.data.Close, 20)
        
        # Realized volatility calculations
        roc = self.I(talib.ROC, self.data.Close, 1)
        self.rv_5 = self.I(talib.STDDEV, roc, 5)
        self.rv_20 = self.I(talib.STDDEV, roc, 20)
        
        # Bollinger Bands components
        self.bb_upper = self.I(self._bb_upper, self.data.Close)
        self.bb_middle = self.I(self._bb_middle, self.data.Close)
        self.bb_lower = self.I(self._bb_lower, self.data.Close)
        
        # Volatility metrics
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 14)
        
    def _bb_upper(self, close):
        upper, _, _ = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
        return upper
        
    def _bb_middle(self, close):
        _, middle, _ = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
        return middle
        
    def _bb_lower(self, close):
        _, _, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
        return lower

    def next(self):
        # Moon Dev progress tracking
        if len(self.data) % 1000 == 0:
            print(f"🌙 PROGRESS: Processing bar {len(self.data)} - Price: {self.data.Close[-1]:.2f} ✨")
        
        if len(self.data) < 20:
            return

        # Entry conditions
        term_inversion = self.front_month[-1] > self.back_month[-1]
        vol_cross = crossover(self.rv_20, self.rv_5)
        
        # Entry logic
        if not self.position and term_inversion and vol_cross:
            atr_value = self.atr[-1] or 1  # Prevent division by zero
            risk_amount = self.equity * self.risk_percent
            position_size = int(round(risk_amount / (1.5 * atr_value)))
            
            if position_size > 0:
                self.sell(size=position_size, 
                         sl=self.data.Close[-1] + 1.5*atr_value,
                         tag="MOON_DEV_ENTRY")
                print(f"🚀 VOLTERRA ACTIVATED: Short {position_size} units at {self.data.Close[-1]:.2f}")
                print(f"   🌑 STOP LUNAR ORBIT: {self.data.Close[-1] + 1.5*atr_value:.2f}")

        # Exit conditions
        if self.position:
            # Term structure contango
            exit_contango = self.front_month[-1] < self.back_month[-1]
            
            # Bandwidth percentile calculation
            lookback = 252
            if len(self.data) > lookback:
                bw_history = [
                    (self.bb_upper[i] - self.bb_lower[i])/self.bb_middle[i] 
                    for i in range(-lookback, 0)
                ]
                current_bw = (self.bb_upper[-1] - self.bb_lower[-1])/self.bb_middle[-1]
                exit