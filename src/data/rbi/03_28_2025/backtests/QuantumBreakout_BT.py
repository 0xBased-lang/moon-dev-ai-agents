```python
import pandas as pd
from backtesting import Backtest, Strategy
import talib
import numpy as np

# Load and prepare data
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')

# Clean and format columns
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
required_columns = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}
data = data.rename(columns=required_columns)

class QuantumBreakout(Strategy):
    risk_pct = 0.01  # 1% risk per trade
    
    def init(self):
        # OBI indicators 🌙
        self.mean_obi = self.I(talib.SMA, self.data['obi'], timeperiod=20)
        self.std_obi = self.I(talib.STDDEV, self.data['obi'], timeperiod=20)
        
        # Bollinger Bands setup ✨
        def bb_upper(close, tp, dev): 
            u, _, _ = talib.BBANDS(close, timeperiod=tp, nbdevup=dev)
            return u
        def bb_lower(close, tp, dev): 
            _, _, l = talib.BBANDS(close, timeperiod=tp, nbdevup=dev)
            return l
            
        self.upper_bb = self.I(bb_upper, self.data.Close, 20, 2)
        self.lower_bb = self.I(bb_lower, self.data.Close, 20, 2)
        
        # BB Width calculation 🌀
        self.bb_width = self.I(lambda u, l, m: ((u-l)/m)*100, 
                             self.upper_bb, self.lower_bb, 
                             self.I(talib.SMA, self.data.Close, 20))
        
        print("🌙 QuantumBreakout Strategy Activated! Ready for stellar performance! 🚀")

    def next(self):
        current_price = self.data.Close[-1]
        obi = self.data['obi'][-1]
        mean_obi = self.mean_obi[-1]
        std_obi = self.std_obi[-1]
        
        # Entry conditions 🌗
        if not self.position:
            # Long constellation 🌕
            if (obi > mean_obi + 2*std_obi and 
                self.bb_width[-1] < 0.5 and 
                current_price > self.upper_bb[-1]):
                
                risk_amount = self.equity * self.risk_pct
                sl = self.lower_bb[-1]
                risk_per_unit = current_price - sl
                size = int(round(risk_amount/risk_per_unit))
                
                if size > 0:
                    self.buy(size=size, sl=sl, tp=current_price + 2*(current_price-sl))
                    print(f"🚀 LONG Signal! Entry: {current_price:.2f} | Size: {size} | RR: 2:1")
            
            # Short constellation 🌑
            elif (obi < mean_obi - 2*std_obi and 
                  self.bb_width[-1] < 0.5 and 
                  current_price < self.lower_bb[-1]):
                
                risk_amount = self.equity * self.risk_pct
                sl = self.upper_bb[-1]
                risk_per_unit = sl - current_price
                size = int(round(risk_amount/risk_per_unit))
                
                if size > 0:
                    self.sell(size=size, sl=sl, tp=current_price - 2*(sl - current_price))
                    print(f"🌑 SHORT Signal! Entry: {current_price:.2f} | Size: {size} | RR: 2:1")
        
        # Exit conditions 🌓
        else:
            # Close on BB width expansion
            if self.bb_width[-1] >= 2:
                self.position.close()
                print(f"✨ Closing on BB Width Expansion: {self.bb_width[-1]:.2f}%")
                
            # Close if OBI reverts to mean
            if (self.position.is_long and obi <= mean_obi) or \
               (self.position.is_short and obi >= mean_obi):
                self.position.close()
                print(f"🌙 OBI Reversion Exit | Current: {obi:.2f} vs Mean: {mean_obi:.2f}")