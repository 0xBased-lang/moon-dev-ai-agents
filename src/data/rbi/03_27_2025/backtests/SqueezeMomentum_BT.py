```python
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import talib

class SqueezeMomentum(Strategy):
    risk_per_trade = 0.01  # 1% risk per trade
    
    def init(self):
        # Bollinger Bands
        self.bb_upper = self.I(talib.BBANDS, self.data.Close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0, name='UPPER', which=0)
        self.bb_lower = self.I(talib.BBANDS, self.data.Close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0, name='LOWER', which=2)
        
        # Chande Momentum Oscillator
        self.cmo = self.I(talib.CMO, self.data.Close, timeperiod=14, name='CMO')
        self.cmo_signal = self.I(talib.SMA, self.cmo, timeperiod=9, name='CMO_SIGNAL')
        
        # Volume MA
        self.volume_ma = self.I(talib.SMA, self.data.Volume, timeperiod=20, name='VOLUME_MA')
        
        # Swing High/Low for stop loss
        self.swing_high = self.I(talib.MAX, self.data.High, timeperiod=20, name='SWING_HIGH')
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=20, name='SWING_LOW')
        
        # Squeeze Detection
        self.bandwidth = self.I(lambda u, l: u - l, self.bb_upper, self.bb_lower, name='BANDWIDTH')
        self.min_bandwidth = self.I(talib.MIN, self.bandwidth, timeperiod=20, name='MIN_BW')

    def next(self):
        if not self.position:
            # Long Entry Conditions
            squeeze = self.bandwidth[-1] <= self.min_bandwidth[-1]
            cmo_up = crossover(self.cmo, self.cmo_signal)
            volume_ok = self.data.Volume[-1] > self.volume_ma[-1]
            price_break = self.data.Close[-1] > self.bb_upper[-1]
            
            if squeeze and cmo_up and volume_ok and price_break:
                sl_price = min(self.swing_low[-1], self.bb_lower[-1])
                risk = self.data.Close[-1] - sl_price
                if risk <= 0: return
                
                size = int(round((self.equity * self.risk_per_trade) / risk))
                if size > 0:
                    self.buy(size=size, sl=sl_price, tag='Long')
                    print(f"🌙 MOON DEV LONG ALERT! Entered {size} units at {self.data.Close[-1]} ✨")
            
            # Short Entry Conditions
            cmo_down = crossover(self.cmo_signal, self.cmo)
            price_break = self.data.Close[-1] < self.bb_lower[-1]
            
            if squeeze and cmo_down and volume_ok and price_break:
                sl_price = max(self.swing_high[-1], self.bb_upper[-1])
                risk = sl_price - self.data.Close[-1]
                if risk <= 0: return
                
                size = int(round((self.equity * self.risk_per_trade) / risk))
                if size > 0:
                    self.sell(size=size, sl=sl_price, tag='Short')
                    print(f"🌙 MOON DEV SHORT ALERT! Entered {size} units at {self.data.Close[-1]} ✨")
        else:
            # Exit Conditions
            if self.position.is_long:
                if crossover(self.cmo_signal, self.cmo) or self.data.Close[-1] < self.bb_upper[-1]:
                    self.position.close()
                    print(f"🌙 MOON DEV EXIT LONG! Closed at {self.data.Close[-1]} 🛑")
            elif self.position.is_short:
                if crossover(self.cmo, self.cmo_signal) or self.data.Close[-1] > self.bb_lower[-1]:
                    self.position.close()
                    print(f"🌙 MOON DEV EXIT SHORT! Closed at {self.data.Close[-1]} 🛑")

# Data Preparation
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data