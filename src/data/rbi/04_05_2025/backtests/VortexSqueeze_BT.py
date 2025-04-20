```python
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import talib
import pandas_ta as ta
import numpy as np

# Load and preprocess data
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')

# Clean column names
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])

# Rename columns to Backtesting.py format
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume',
    'datetime': 'DateTime'
}, inplace=True)

# Set datetime index
data['DateTime'] = pd.to_datetime(data['DateTime'])
data.set_index('DateTime', inplace=True)

class VortexSqueeze(Strategy):
    risk_percent = 0.01  # 1% risk per trade
    atr_period = 14
    obv_lookback = 5
    squeeze_period = 20
    
    def init(self):
        # Calculate indicators with self.I()
        h, l, c = self.data.High, self.data.Low, self.data.Close
        
        # Vortex Indicator 🌪️
        self.vi = self.data.ta.vortex(append=False)
        self.vi_plus = self.I(ta.vortex, h, l, c, 14, column='VIn_14', name='VI+')
        self.vi_minus = self.I(ta.vortex, h, l, c, 14, column='VIm_14', name='VI-')
        
        # On-Balance Volume 📊
        self.obv = self.I(talib.OBV, c, self.data.Volume, name='OBV')
        
        # Bollinger Bands 📉
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(ta.bbands, c, 20, 2, name='BBANDS')
        self.bb_bandwidth = self.I(lambda: (self.bb_upper - self.bb_lower)/self.bb_middle, name='BB Width')
        
        # ATR for risk management 🔍
        self.atr = self.I(talib.ATR, h, l, c, self.atr_period, name='ATR')
        
    def next(self):
        # Skip early bars where indicators are NaN
        if len(self.data) < max(20, self.atr_period, self.squeeze_period)+1:
            return
        
        # Get current values
        vi_plus = self.vi_plus[-1]
        vi_minus = self.vi_minus[-1]
        obv_today = self.obv[-1]
        obv_past = self.obv[-self.obv_lookback]
        bb_width_today = self.bb_bandwidth[-1]
        atr = self.atr[-1]

        # Moon Dev Entry Logic 🌙✨
        if not self.position:
            # Long Entry Conditions ✅
            if (crossover(vi_plus, vi_minus) and 
                obv_today > obv_past and 
                bb_width_today == min(self.bb_bandwidth[-self.squeeze_period:])):
                
                # Position Sizing Calculation ⚖️
                stop_loss = self.data.Close[-1] - 2*atr
                risk_per_share = self.data.Close[-1] - stop_loss
                position_size = int(round((self.equity * self.risk_percent)/risk_per_share))
                
                if position_size > 0:
                    self.buy(size=position_size, sl=stop_loss, tag='MoonEntry')
                    print(f"🌙 MOON DEV LONG SIGNAL 🌙 | Size: {position_size:,} | Entry: {self.data.Close[-1]:.2f} | SL: {stop_loss:.2f}")

        # Moon Dev Exit Logic 🚀
        else:
            if crossover(vi_minus, vi_plus):
                self.position.close()
                print(f"🌑 EXIT SIGNAL TRIGGERED 🌑 | Price: {self.data.Close[-1]:.2f} | Profit: {self.position.pl_pct:.2f}%")
            
            # Update trailing stop 🔒
            if self.position.is_long:
                self.position.sl = max(self.position.sl or 0, self.data.Close[-1