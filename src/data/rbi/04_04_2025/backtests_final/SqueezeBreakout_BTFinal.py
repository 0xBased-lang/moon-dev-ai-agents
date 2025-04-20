I'll fix the code while maintaining the original strategy logic and adding Moon Dev themed debug prints. Here's the corrected version:

```python
# 🌙 MOON DEV BACKTESTING IMPLEMENTATION 🌙
from backtesting import Backtest, Strategy
import pandas as pd
import talib
import numpy as np

# ========== DATA PREPARATION ==========
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)
data['DateTime'] = pd.to_datetime(data['datetime'])
data.set_index('DateTime', inplace=True)

# ========== SQUEEZE BREAKOUT STRATEGY ==========
class SqueezeBreakout(Strategy):
    risk_percent = 0.01  # 🌙 1% risk per trade
    
    def init(self):
        # 🌟 INDICATORS USING TA-LIB
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14, name='ADX')
        self.ema_20 = self.I(talib.EMA, self.data.Close, timeperiod=20, name='EMA_20')
        self.atr_20 = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=20, name='ATR_20')
        self.volume_ma50 = self.I(talib.SMA, self.data.Volume, timeperiod=50, name='VOL_MA50')
        
        # 🌙 MOON DEV INIT LOG
        print("🌙✨ MOON DEV STRATEGY INITIALIZED ✨🌙")
        print(f"🌌 Indicators Loaded: ADX(14), EMA(20), ATR(20), Volume MA(50)")
        
    def next(self):
        # ✨ MOON DEV DEBUG CHECK
        if len(self.data) < 50:  # Ensure all indicators are valid
            return
            
        # 🌈 CURRENT VALUES
        price = self.data.Close[-1]
        adx_val = self.adx[-1]
        ema_val = self.ema_20[-1]
        atr_val = self.atr_20[-1]
        vol_ma = self.volume_ma50[-1]
        
        # 🌀 KELTNER CHANNEL CALCULATIONS
        upper_kc = ema_val + 2 * atr_val
        lower_kc = ema_val - 2 * atr_val
        
        print(f"🌙 MOON DEV SIGNAL CHECK 🌙 | ADX: {adx_val:.1f} | Price: {price:.2f} | Vol: {self.data.Volume[-1]:.2f} vs MA50: {vol_ma:.2f}")
        
        # 🚀 ENTRY LOGIC
        if not self.position:
            # LONG ENTRY (Breakout with confirmation)
            if adx_val > 25 and price > upper_kc and self.data.Volume[-1] > vol_ma:
                risk_amount = self.equity * self.risk_percent
                risk_per_share = price - ema_val  # SL at EMA
                if risk_per_share > 0:
                    size = int(round(risk_amount / risk_per_share))
                    self.buy(size=size, sl=ema_val)
                    print(f"🚀🌕 MOON DEV LONG ENTRY 🚀🌕 | Size: {size} | Entry: {price:.2f} | SL: {ema_val:.2f}")
            
            # SHORT ENTRY (Breakdown with confirmation)
            elif adx_val > 25 and price < lower_kc and self.data.Volume[-1] > vol_ma:
                risk_amount = self.equity * self.risk_percent
                risk_per_share = ema_val - price  # SL at EMA
                if risk_per_share > 0:
                    size = int(round(risk_amount / risk_per_share))
                    self.sell(size=size, sl=ema_val)
                    print(f"🌑🚀 MOON DEV SHORT ENTRY 🌑🚀 | Size: {size} | Entry: {price:.2f} | SL: {ema_val:.2f}")