Here's the fixed and enhanced backtest code with Moon Dev themed debug prints and proper position sizing:

```python
import pandas as pd
from backtesting import Backtest, Strategy
import talib
import pandas_ta as ta
import numpy as np

# 🌙 Moon Dev Data Preparation Magic ✨
print("🌌 Initializing Moon Dev Backtest Engine...")
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path)

# 🧹 Cleanse column names with Moon Dev precision
print("✨ Cleansing cosmic data impurities...")
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])

# 🌌 Cosmic column alignment for backtesting harmony
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# 🕰️ Time warp conversion for temporal accuracy
print("⏳ Aligning temporal dimensions...")
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

class MomentumSurgeBreakout(Strategy):
    def init(self):
        # 🌠 Momentum and Volume Indicators
        self.cmo = self.I(talib.CMO, self.data.Close, timeperiod=14, name='CMO_14')
        self.volume_avg = self.I(talib.SMA, self.data.Volume, 20, name='Volume_MA20')
        
        # 📈 Volatility Indicators
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, self.data.Close, 
            timeperiod=20, nbdevup=2, nbdevdn=2, matype=0,
            name=['BB_Upper', 'BB_Mid', 'BB_Lower']
        )
        self.bb_width = self.I(lambda u, l: (u - l)/self.bb_middle, self.bb_upper, self.bb_lower, name='BB_Width')
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 14, name='ATR14')
        
        # 🎯 Dynamic Exit Threshold (20th percentile of 50-period BB Width)
        self.bb_width_percentile = self.I(
            lambda x: x.rolling(50).quantile(0.2), 
            self.bb_width, 
            name='BB_Width_P20'
        )

    def next(self):
        current_close = self.data.Close[-1]
        moon_emoji = '🌙' if current_close > self.bb_middle[-1] else '🌑'
        
        # 🚀 LONG Entry Constellation Alignment
        if not self.position:
            # Replaced crossover with direct comparison
            if (self.cmo[-2] < 50 and self.cmo[-1] > 50) and self.data.Volume[-1] > 2 * self.volume_avg[-1]:
                risk_percent = 0.01  # 1% risk per trade
                atr_value = self.atr[-1]
                entry_price = self.data.Close[-1]  # Using current close instead of next open
                
                # 🛡️ Risk Forcefield Calculation
                stop_loss = entry_price - 1.5 * atr_value
                risk_amount = risk_percent * self.equity
                position_size = int(round(risk_amount / (entry_price - stop_loss)))
                
                if position_size > 0:
                    self.buy(
                        size=position_size,
                        sl=stop_loss,
                        tag=f"MoonSurge-{current_close:.2f}"
                    )
                    print(f"{moon_emoji}✨🚀 MOON BLASTOFF! Entry @ {entry_price:.2f}")
                    print(f"    Size: {position_size} units | SL: {stop_loss:.2f} | CMO: {self.cmo[-1]:.2f}")
        
        # 🌪️ Exit Protocol: Volatility Contraction Detection
        elif self.position:
            if self.bb_width[-1] < self.bb_width_percentile[-1]:
                self.position.close()
                print(f"{moon_emoji}💨 VOLATILITY COLLAPSE! Exit @ {current_close:.2f}")
                print(f"    BB Width: {self.bb_width[-1]:.4f} < {self.bb_width_percentile[-1]:.4