```python
import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import talib
import pandas_ta as ta
import numpy as np

class MomentumConvergence(Strategy):
    def init(self):
        # Clean and prepare data
        self.data.df.columns = self.data.df.columns.str.strip().str.lower()
        self.data.df = self.data.df.drop(columns=[col for col in self.data.df.columns if 'unnamed' in col])
        self.data.df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']  # Ensure proper case
        
        # Calculate indicators with self.I()
        # Fisher Transform using pandas_ta
        self.fisher, self.fisher_signal = self.I(ta.fisher, high=self.data.High, low=self.data.Low, length=9, signal=9, 
                                                append=False, name=['FISHER', 'FISHER_SIGNAL'])
        
        # Volume-Weighted MACD Histogram
        macd = self.I(talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9,
                     name=['MACD', 'MACD_SIGNAL', 'MACD_HIST'])
        self.macd_hist = macd[2]
        self.vw_macd_hist = self.I(lambda: self.macd_hist * self.data.Volume, name='VW_MACD_HIST')
        
        # Chaikin Money Flow
        self.cmf = self.I(ta.cmf, high=self.data.High, low=self.data.Low, close=self.data.Close, 
                         volume=self.data.Volume, length=21, name='CMF')
        
        # ATR for stop loss
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14, name='ATR')
        
        # Track entry bar for time-based exit
        self.entry_bar = 0

    def next(self):
        # Moon Dev Debug Prints
        print(f"🌙 Current Close: {self.data.Close[-1]} | Fisher: {self.fisher[-1]:.2f} | CMF: {self.cmf[-1]:.2f}")
        
        # Entry Conditions
        if not self.position:
            # Long Entry
            fisher_cross = crossover(self.fisher, self.fisher_signal)
            hist_converge = abs(self.vw_macd_hist[-1]) < abs(self.vw_macd_hist[-2])
            if fisher_cross and hist_converge and self.cmf[-1] > 0:
                self.enter_long()
                
            # Short Entry
            fisher_cross_short = crossover(self.fisher_signal, self.fisher)
            if fisher_cross_short and hist_converge and self.cmf[-1] < 0:
                self.enter_short()
        else:
            # Exit Conditions
            if self.position.is_long:
                if crossover(self.fisher_signal, self.fisher) or \
                   len(self.data) - self.entry_bar >= 10:
                    self.exit_long()
            else:
                if crossover(self.fisher, self.fisher_signal) or \
                   len(self.data) - self.entry_bar >= 10:
                    self.exit_short()
            
            # Trailing Stop (2x ATR)
            if self.position.is_long:
                sl = self.data.Close[-1] - 2 * self.atr[-1]
                self.position.sl = max(self.position.sl or 0, sl)
            else:
                sl = self.data.Close[-1] + 2 * self.atr[-1]
                self.position.sl = min(self.position.sl or np.inf, sl)

    def enter_long(self):
        risk_pct = 0.01
        risk_amount = self.equity * risk_pct
        sl_distance = 2 * self.atr[-1]
        position_size = int(round(risk_amount / sl_distance))
        
        if position_size > 0:
            print(f"🌙✨🚀 MOON DEV LONG ENTRY: Buying {position_size} units at {self.data.Close[-1]}")
            self.buy(size=position_size, sl=self.data.Close[-1] - sl_distance)
            self.entry_bar = len(self.data)

    def enter_short(self):
        risk_pct = 0.01
        risk_amount = self.equity * risk_pct
        sl_distance = 2 * self.atr[-1]
        position_size = int(round(risk_amount / sl_distance))
        
        if position_size > 0:
            print(f