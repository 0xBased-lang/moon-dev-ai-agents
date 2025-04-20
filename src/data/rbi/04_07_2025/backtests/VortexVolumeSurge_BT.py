Here's the complete implementation of the VortexVolumeSurge strategy for backtesting.py:

```python
import pandas as pd
import talib
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# Clean and prepare data
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')

# Clean column names and remove unnamed columns
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Proper column mapping
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# Set datetime index
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

class VortexVolumeSurge(Strategy):
    def init(self):
        # Calculate Vortex Indicator components
        tr = self.I(talib.TRANGE, self.data.High, self.data.Low, self.data.Close)
        sum_tr = self.I(talib.SUM, tr, 14)
        
        # Calculate VM+ and VM-
        prev_low = self.I(lambda x: x.shift(1), self.data.Low)
        prev_high = self.I(lambda x: x.shift(1), self.data.High)
        vm_plus = self.I(lambda h, l: np.abs(h - l), self.data.High, prev_low)
        vm_minus = self.I(lambda h, l: np.abs(h - l), prev_high, self.data.Low)
        
        # Calculate sums
        sum_vm_plus = self.I(talib.SUM, vm_plus, 14)
        sum_vm_minus = self.I(talib.SUM, vm_minus, 14)
        
        # Final Vortex calculations
        self.vi_plus = self.I(lambda x, y: x/y, sum_vm_plus, sum_tr, name='VI+')
        self.vi_minus = self.I(lambda x, y: x/y, sum_vm_minus, sum_tr, name='VI-')
        
        # Volume indicators
        self.volume_sma = self.I(talib.SMA, self.data.Volume, 480)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 14)
        
        self.trailing_stop = None

    def next(self):
        # Wait for sufficient data
        if len(self.data) < 480 + 14:
            return
            
        # Entry conditions
        if (crossover(self.vi_plus, self.vi_minus) and
            self.data.Volume[-1] > self.volume_sma[-1] * 1.2 and
            not self.position):
            
            # Calculate position size with 1% risk
            risk_amount = self.equity * 0.01
            atr_value = self.atr[-1]
            if atr_value == 0:
                return  # Safety check
            
            position_size = int(round(risk_amount / (3 * atr_value)))
            if position_size > 0:
                self.buy(size=position_size)
                self.trailing_stop = self.data.Close[-1] - 3 * atr_value
                print(f"🌙 MOON DEV ALERT! 🚀 Long entry {position_size} units at {self.data.Close[-1]} ✨")
                print(f"   Initial stop: {self.trailing_stop} | ATR: {atr_value:.2f}")

        # Manage open positions
        if self.position:
            # Update trailing stop
            current_atr = self.atr[-1]
            new_stop = max(self.trailing_stop, 
                          self.data.High[-1] - 3 * current_atr)
            
            # Check exit condition
            if self.data.Close[-1] < new_stop:
                self.position.close()
                print(f"🌙 MOON DEV EXIT! 🛑 Closed at {self.data.Close[-1]} ✨")
                print(f"   Final stop: {new_stop} | Profit: {self.position.pl_pct:.2f}%")
                
            self.trailing_stop = new_stop

# Execute backtest
bt = Backtest(data, VortexVolumeSurge, cash=1_000_000, trade_on_close=True)
stats = bt.run()
print(stats)
print(stats._strategy