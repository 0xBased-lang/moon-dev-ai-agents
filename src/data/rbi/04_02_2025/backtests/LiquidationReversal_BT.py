```python
# 🌙 MOON DEV BACKTESTING SCRIPT FOR LIQUIDATION REVERSAL STRATEGY
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# =====================
# DATA PREPARATION
# =====================
data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')

# Clean and prepare columns 🌙✨
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# =====================
# STRATEGY IMPLEMENTATION
# =====================
class LiquidationReversal(Strategy):
    ema_period = 20
    atr_period = 14
    keltner_multiplier = 2.5
    swing_lookback = 20
    obv_window = 5
    risk_pct = 0.015
    buffer_pct = 0.0075

    def init(self):
        # 🌙 INDICATORS USING TALIB
        self.swing_high = self.I(talib.MAX, self.data.High, timeperiod=self.swing_lookback, name='🌙 SWING HIGH')
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=self.swing_lookback, name='🌑 SWING LOW')
        self.obv = self.I(talib.OBV, self.data.Close, self.data.Volume, name='✨ OBV')
        self.ema = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_period, name='📈 EMA')
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period, name='🌊 ATR')

    def next(self):
        # 🌙 MOON DEV DEBUGGING CHECKS
        if len(self.data) < max(self.swing_lookback, self.atr_period, self.ema_period) + self.obv_window:
            return

        # ✨ CURRENT VALUES
        price = self.data.Close[-1]
        upper_keltner = self.ema[-1] + (self.atr[-1] * self.keltner_multiplier)
        lower_keltner = self.ema[-1] - (self.atr[-1] * self.keltner_multiplier)

        # 🚀 BEARISH DIVERGENCE CHECK (SHORT)
        if self.data.High[-1] >= self.swing_high[-1] * (1 - self.buffer_pct):
            obv_divergence = self.obv[-1] < self.obv[-self.obv_window]
            if obv_divergence and not self.position:
                sl_price = self.swing_high[-1] * (1 + self.buffer_pct)
                risk_per_share = sl_price - price
                position_size = int(round((self.risk_pct * self.equity) / risk_per_share))
                
                if position_size > 0:
                    self.sell(size=position_size, sl=sl_price, tag='🌑 BEARISH DIVERGENCE')
                    print(f"🚀🌑 MOON DEV SHORT ENTRY | Price: {price:.2f} | Size: {position_size} | SL: {sl_price:.2f}")

        # 🌙 BULLISH DIVERGENCE CHECK (LONG)
        if self.data.Low[-1] <= self.swing_low[-1] * (1 + self.buffer_pct):
            obv_divergence = self.obv[-1] > self.obv[-self.obv_window]
            if obv_divergence and not self.position:
                sl_price = self.swing_low[-1] * (1 - self.buffer_pct)
                risk_per_share = price - sl_price
                position_size = int(round((self.risk_pct * self.equity) / risk_per_share))
                
                if position_size > 0:
                    self.buy(size=position_size, sl=sl_price, tag='✨ BULLISH DIVERGENCE')
                    print(f"🌙✨ MOON DEV LONG ENTRY | Price: