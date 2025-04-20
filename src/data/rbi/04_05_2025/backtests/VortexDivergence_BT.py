```python
# 🌙 Moon Dev's VortexDivergence Backtest 🌙
import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import talib
import pandas_ta as ta

# ---------------------------
# DATA PREPARATION
# ---------------------------
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')

# Clean column names 🧹
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])

# Map to backtesting.py format 🗺️
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# Convert index to datetime ⏳
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime').sort_index()

# ---------------------------
# STRATEGY CLASS
# ---------------------------
class VortexDivergence(Strategy):
    risk_pct = 0.01  # 1% risk per trade 🌕
    vortex_period = 14
    cmo_period = 14
    volume_ma_period = 20
    swing_period = 20
    keltner_ema = 20
    keltner_atr = 20
    atr_multiplier = 2

    def init(self):
        # 🌪️ Vortex Indicator
        self.vi_plus = self.I(ta.vortex, 
                            self.data.High, 
                            self.data.Low, 
                            self.data.Close, 
                            self.vortex_period,
                            name='VI_PLUS',
                            col_names=['VIp_14'])
        
        self.vi_minus = self.I(ta.vortex, 
                             self.data.High, 
                             self.data.Low, 
                             self.data.Close, 
                             self.vortex_period,
                             name='VI_MINUS',
                             col_names=['VIm_14'])

        # 📈 Chande Momentum Oscillator
        self.cmo = self.I(talib.CMO, self.data.Close, self.cmo_period)

        # 📊 Volume Confirmation
        self.volume_ma = self.I(talib.SMA, self.data.Volume, self.volume_ma_period)

        # 🛑 Swing High/Low for Stops
        self.swing_high = self.I(talib.MAX, self.data.High, self.swing_period)
        self.swing_low = self.I(talib.MIN, self.data.Low, self.swing_period)

        # 📉 Keltner Channels
        self.ema = self.I(talib.EMA, self.data.Close, self.keltner_ema)
        self.atr = self.I(talib.ATR, 
                         self.data.High, 
                         self.data.Low, 
                         self.data.Close, 
                         self.keltner_atr)

    def next(self):
        # 🌙 Moon Dev Debug Checks
        if len(self.data) < max(self.vortex_period, 
                              self.cmo_period, 
                              self.volume_ma_period, 
                              self.swing_period, 
                              self.keltner_ema) + 1:
            return

        # 🔄 Vortex Crossover Logic
        vi_cross_up = crossover(self.vi_plus, self.vi_minus)
        vi_cross_down = crossover(self.vi_minus, self.vi_plus)

        # 📉 Momentum Divergence Check
        current_high, prev_high = self.data.High[-1], self.data.High[-2]
        current_low, prev_low = self.data.Low[-1], self.data.Low[-2]
        current_cmo, prev_cmo = self.cmo[-1], self.cmo[-2]
        
        bearish_divergence = (current_high > prev_high) and (current_cmo < prev_cmo)
        bullish_divergence = (current_low < prev_low) and (current_cmo > prev_cmo)

        # 🔊 Volume Confirmation
        volume_spike = self.data.Volume[-1] > self.volume_ma[-1]

        # 🛑 Risk Management Calculations
        current_close = self.data.Close[-1]
        keltner_upper = self.ema[-1] + self.atr[-1] * self.atr_multiplier
        keltner_lower = self.ema[-1] - self.atr[-1] * self.atr