Here's the fixed code with all backtesting.lib imports removed and replaced with proper implementations, along with Moon Dev themed debug prints:

```python
import pandas as pd
import talib
import numpy as np
from backtesting import Backtest, Strategy

# Load and preprocess data
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

class VolatilityTriad(Strategy):
    risk_pct = 0.01  # 1% risk per trade
    
    def init(self):
        # Bollinger Bands (20, 2)
        self.bb_upper = self.I(talib.BBANDS, self.data.Close, 20, 2, 2, 0)[0]
        self.bb_mid = self.I(talib.BBANDS, self.data.Close, 20, 2, 2, 0)[1]
        self.bb_lower = self.I(talib.BBANDS, self.data.Close, 20, 2, 2, 0)[2]
        
        # Keltner Channels (20, 1.5)
        self.ema = self.I(talib.EMA, self.data.Close, 20)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 20)
        self.keltner_upper = self.I(lambda: self.ema + 1.5*self.atr)
        self.keltner_lower = self.I(lambda: self.ema - 1.5*self.atr)
        
        # Volume indicators
        self.volume_ma = self.I(talib.SMA, self.data.Volume, 20)
        self.obv = self.I(talib.OBV, self.data.Close, self.data.Volume)
        
        # Trailing stop tracker
        self.trailing_stop = None

    def next(self):
        price = self.data.Close[-1]
        atr = self.atr[-1]
        
        # Triple confirmation conditions 🌙
        bb_squeeze = (self.bb_upper[-1] - self.bb_lower[-1]) < np.mean(self.bb_upper[-5:-1] - self.bb_lower[-5:-1])
        keltner_squeeze = (self.data.High[-1] < self.keltner_upper[-1]) and (self.data.Low[-1] > self.keltner_lower[-1])
        volume_decline = self.volume_ma[-1] < self.volume_ma[-5]
        
        # Entry logic 🚀
        long_trigger = ((self.data.Close[-2] < self.bb_upper[-2] and self.data.Close[-1] > self.bb_upper[-1]) or 
                       (self.data.Close[-2] < self.keltner_upper[-2] and self.data.Close[-1] > self.keltner_upper[-1])) and \
                       self.data.Volume[-1] > self.volume_ma[-1]
                       
        short_trigger = ((self.data.Close[-2] > self.bb_lower[-2] and self.data.Close[-1] < self.bb_lower[-1]) or 
                        (self.data.Close[-2] > self.keltner_lower[-2] and self.data.Close[-1] < self.keltner_lower[-1])) and \
                        self.data.Volume[-1] > self.volume_ma[-1]
        
        # Position sizing calculation ✨
        risk_amount = self.broker.equity * self.risk_pct
        stop_distance = 1.5 * atr
        
        if long_trigger and not self.position:
            size = int(round(risk_amount / stop_distance))
            if size > 0:
                self.buy(size=size, sl=price-stop_distance,
                        tp=price+3*stop_distance)
                self.trailing_stop = price - stop_distance
                print(f"🌙✨🚀 MOON DEV LONG ENTRY: {price:.2f} | Size: {size} | SL: {self.trailing_stop:.2f}")
        
        if short_trigger and not self.position:
            size = int(round(risk_amount / stop_distance))
            if