from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import talib
import pandas_ta as ta

# Data preprocessing
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)

class VolatilitySqueezeAdaptive(Strategy):
    keltner_multiplier = 1.5
    hist_percentile = 20
    vwma_length = 20
    risk_pct = 0.01
    atr_stop_mult = 1
    lookback = 100

    def init(self):
        self.ema = self.I(talib.EMA, self.data.Close, 5)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 5)
        self.upper_keltner = self.I(lambda e,a: e + self.keltner_multiplier*a, self.ema, self.atr)
        self.lower_keltner = self.I(lambda e,a: e - self.keltner_multiplier*a, self.ema, self.atr)
        self.keltner_width = self.I(lambda u,l: u-l, self.upper_keltner, self.lower_keltner)
        self.vol_percentile = self.I(lambda w: w.rolling(self.lookback).quantile(self.hist_percentile/100), self.keltner_width)
        self.vwma = self.I(ta.vwma, self.data.Close, self.data.Volume, self.vwma_length)

    def next(self):
        if not self.position:
            if self.keltner_width[-2] < self.vol_percentile[-2] and self.data.Close[-2] > self.upper_keltner[-2]:
                entry_price = self.data.Open[-1]
                atr_val = self.atr[-1]
                sl_price = entry_price - (atr_val * self.atr_stop_mult)
                risk_per_unit = entry_price - sl_price
                position_size = int(round((self.equity * self.risk_pct) / risk_per_unit))
                
                if position_size > 0:
                    self.buy(size=position_size, sl=sl_price)
                    print(f"🌙✨ MOON DEV ENTRY: LONG {position_size} @ {entry_price:.2f} | SL: {sl_price:.2f} 🚀")
        else:
            if crossover(self.vwma, self.data.Close):
                self.position.close()
                print(f"🌙🚨 MOON DEV EXIT: CLOSE @ {self.data.Close[-1]:.2f} | Profit: {self.position.pl_usd:.2f} ✨")

bt = Backtest(data, VolatilitySqueezeAdaptive, cash=1_000_000)
stats = bt.run()
print(stats)
print(stats._strategy)