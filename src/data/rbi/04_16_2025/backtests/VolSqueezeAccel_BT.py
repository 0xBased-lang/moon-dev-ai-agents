```python
# 🌙 Moon Dev's VolSqueezeAccel Backtest 🌙
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import talib
import numpy as np

# 🚀 Data Preparation Rocket Launch 🚀
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path)

# 🌙 Data Cleansing Ritual
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# 🌌 Cosmic Column Alignment
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)

data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

class VolSqueezeAccel(Strategy):
    def init(self):
        # 🌗 Phase 1: Orbital Indicator Calculations
        # 📡 Deploying Bollinger Bands Array
        self.bb_upper = self.I(self._calculate_bb_upper, self.data.Close)
        self.bb_middle = self.I(self._calculate_bb_middle, self.data.Close)
        self.bb_lower = self.I(self._calculate_bb_lower, self.data.Close)
        
        # 🌌 Band Width Nebula Analysis
        self.bb_width = self.I(lambda u, l, m: (u - l)/m, 
                              self.bb_upper, self.bb_lower, self.bb_middle)
        self.bb_width_avg = self.I(talib.SMA, self.bb_width, 20)
        
        # 🚀 Volume Thrust Accelerator
        self.volume_roc = self.I(talib.ROC, self.data.Volume, 5)
        self.volume_roc_mean = self.I(talib.SMA, self.volume_roc, 20)
        self.volume_roc_std = self.I(talib.STDDEV, self.volume_roc, 20)
        self.volume_accel = self.I(lambda r, m, s: (r - m)/s,
                                  self.volume_roc, self.volume_roc_mean, self.volume_roc_std)
        
        # 🛡️ ATR Force Field Generator
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 14)
        
    def _calculate_bb_upper(self, close):
        upper, _, _ = talib.BBANDS(close, 20, 2, 2)
        return upper
    
    def _calculate_bb_middle(self, close):
        _, middle, _ = talib.BBANDS(close, 20, 2, 2)
        return middle
    
    def _calculate_bb_lower(self, close):
        _, _, lower = talib.BBANDS(close, 20, 2, 2)
        return lower

    def next(self):
        # 🌙 Lunar Debug Console
        print(f"\n🌕 Moon Phase Update | Close: {self.data.Close[-1]:.2f} | Volume Z: {self.volume_accel[-1]:.2f}σ | BB Width: {self.bb_width[-1]:.4f}")
        
        if self.position:
            # 🚨 Active Position Management
            price = self.data.Close[-1]
            if self.position.is_long:
                if self.data.Low[-1] <= self.position.sl:
                    print(f"🌘 LONG STOP LOSS ACTIVATED! Collision at {self.position.sl:.2f}")
                    self.position.close()
                elif self.data.High[-1] >= self.position.tp:
                    print(f"🌖 LONG TAKE PROFIT REACHED! Docking at {self.position.tp:.2f}")
                    self.position.close()
            else:
                if self.data.High[-1] >= self.position.sl:
                    print(f"🌒 SHORT STOP LOSS TRIGGERED! Breach at {self.position.sl:.2f}")
                    self.position.close()
                elif self.data.Low[-1] <= self.position.tp:
                    print(f"🌔 SHORT TAKE PROFIT ACHIEVED! Landing at {self.position.tp:.2f}")
                    self.position.close()
            return

        # 🌑 New Moon Entry Conditions
        bb_squeeze_threshold = 0.5 * self.bb_width_