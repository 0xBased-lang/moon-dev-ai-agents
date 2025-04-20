I'll help fix the code while maintaining the strategy logic and adding Moon Dev themed debug prints. Here's the corrected version:

```python
import pandas as pd
import talib
from backtesting import Backtest, Strategy

# Data Preparation
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')

# Clean and format data columns 🌙
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

class FractalChannelTrend(Strategy):
    fractal_period = 5
    channel_period = 20
    risk_pct = 1  # 1% risk per trade 🌕
    
    def init(self):
        # Moon-powered indicators 🌙✨
        self.fractal_high = self.I(talib.MAX, self.data.High, self.fractal_period, name='FRACTAL HIGH')
        self.fractal_low = self.I(talib.MIN, self.data.Low, self.fractal_period, name='FRACTAL LOW')
        
        self.upper_channel = self.I(talib.MAX, self.fractal_high, self.channel_period, name='UPPER CHANNEL')
        self.lower_channel = self.I(talib.MIN, self.fractal_low, self.channel_period, name='LOWER CHANNEL')
        
        self.last_fractal_high = None
        self.last_fractal_low = None

    def next(self):
        # Update lunar fractals 🌑🌕
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        
        if self.fractal_high[-1] == current_high:
            self.last_fractal_high = current_high
            print(f"🌙✨ New Moon Fractal HIGH at {current_high}")
            
        if self.fractal_low[-1] == current_low:
            self.last_fractal_low = current_low
            print(f"🌙✨ New Moon Fractal LOW at {current_low}")

        current_close = self.data.Close[-1]
        upper = self.upper_channel[-1]
        lower = self.lower_channel[-1]

        # Cosmic position management 🌌
        if not self.position:
            # Long entry when price breaks upper channel in uptrend 🚀
            if (self.data.Close[-2] < upper and self.data.Close[-1] > upper) and current_close > lower:
                if self.last_fractal_low:
                    sl = self.last_fractal_low * 0.99
                    risk_amount = self.risk_pct/100 * self.equity
                    size = int(round(risk_amount / (current_close - sl)))
                    if size > 0:
                        self.buy(size=size, sl=sl)
                        print(f"🚀🌕 MOON SHOT! Long {size} units @ {current_close} | SL: {sl}")
            
            # Short entry when price breaks lower channel in downtrend 🌠
            elif (self.data.Close[-2] > lower and self.data.Close[-1] < lower) and current_close < upper:
                if self.last_fractal_high:
                    sl = self.last_fractal_high * 1.01
                    risk_amount = self.risk_pct/100 * self.equity
                    size = int(round(risk_amount / (sl - current_close)))
                    if size > 0:
                        self.sell(size=size, sl=sl)
                        print(f"🌠🌑 BLACK HOLE! Short {size} units @ {current_close} | SL: {sl}")
        else:
            # Galactic exit conditions 🌟
            if self.position.is_long:
                if (self.data.Close[-2] > lower and self.data.Close[-1] < lower):
                    self.position.close()
                    print(f"🌙💤 Closing LONG @ {current_close}")
                elif self.last_fractal_low:
                    new_sl = self.last_fractal_low * 0.99
                    if new_sl > self.position.sl:
                        self.position.sl = new_sl
                        print(f"🌙✨ Trailing SL updated to {new