I'll fix the code while maintaining the original strategy logic. Here's the debugged version with Moon Dev themed improvements:

```python
# 🌙 Moon Dev's VolumetricVwap Backtest 🌙
import pandas as pd
import talib
from backtesting import Backtest, Strategy
import datetime

# Data preparation 🌐
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')

# Clean and prepare data columns ✨
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

class VolumetricVwap(Strategy):
    risk_per_trade = 0.01  # 1% risk per trade 🌡️
    
    def init(self):
        # Calculate VWAP using cumulative method 🌗
        typical_price = (self.data.High + self.data.Low + self.data.Close) / 3
        cumulative_tpv = (typical_price * self.data.Volume).cumsum()
        cumulative_vol = self.data.Volume.cumsum()
        self.vwap = cumulative_tpv / cumulative_vol
        self.I(lambda: self.vwap, name='VWAP')
        
        # Volume 90th percentile (20-period) 📊
        self.volume_90th = self.data.Volume.rolling(20).quantile(0.9)
        self.I(lambda: self.volume_90th, name='Volume_90th')
        
        # Bollinger Bands with %B calculation 📉
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, 
            self.data.Close, 
            timeperiod=20, 
            nbdevup=2, 
            nbdevdn=2, 
            matype=0
        )
        
        # Calculate %B indicator 🌙
        self.pct_b = (self.data.Close - self.bb_lower) / (self.bb_upper - self.bb_lower)
        self.I(lambda: self.pct_b, name='%B')
        
    def next(self):
        # Wait for sufficient data 🌌
        if len(self.data) < 20:
            return
            
        # Time-based entry cutoff ⏰
        current_time = self.data.index[-1].time()
        if current_time >= datetime.time(14, 30) and not self.position:
            return
            
        # Exit logic based on %B 🌓
        if self.position:
            if self.position.is_long and self.pct_b[-1] >= 0.8:
                self.position.close()
                print(f"🌙✨ LONG EXIT: %B reached 0.8 (overbought) | Price {self.data.Close[-1]} 🚀")
            elif self.position.is_short and self.pct_b[-1] <= 0.2:
                self.position.close()
                print(f"🌙✨ SHORT EXIT: %B reached 0.2 (oversold) | Price {self.data.Close[-1]} 🌑")
                
        # Entry logic 🚪
        if not self.position:
            prev_idx = -2  # Previous bar index
            
            # Long entry conditions 🌕
            if (self.data.Close[prev_idx] < self.vwap[prev_idx] and self.data.Close[-1] > self.vwap[-1]) and \
               (self.data.Volume[prev_idx] > self.volume_90th[prev_idx]):
                
                # Risk management calculations 🛡️
                entry_price = self.data.Open[-1]
                lookback = 5
                start_idx = max(0, len(self.data) - lookback - 1)
                stop_loss = min(self.data.Low[start_idx:-1])
                risk_amount = self.equity * self.risk_per_trade
                risk_per_share = entry_price - stop_loss
                
                if risk_per_share > 0:
                    size = int(round(risk_amount / risk_per_share))
                    self.buy(size=size, sl=stop_loss)
                    print(f"🌙✨ LONG ENTRY: {size} units @ {entry_price} | SL {stop_loss} 🚀")
            
            # Short entry conditions 🌑
            elif (self.vwap[prev_idx] < self.data.Close