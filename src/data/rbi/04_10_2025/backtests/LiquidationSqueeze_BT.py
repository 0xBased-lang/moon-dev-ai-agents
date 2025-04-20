```python
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# Moon Dev Data Preparation 🌙
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
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

class LiquidationSqueeze(Strategy):
    bb_period = 20
    devup = 2
    devdn = 2
    swing_period = 20
    squeeze_threshold = 0.05  # 5% bandwidth
    risk_pct = 0.01
    
    def init(self):
        # 🌙 Moon Dev Indicators Setup
        self.sma = self.I(talib.SMA, self.data.Close, self.bb_period)
        self.stddev = self.I(talib.STDDEV, self.data.Close, self.bb_period)
        self.upper_band = self.I(lambda: self.sma + 2*self.stddev, name='Upper BB')
        self.lower_band = self.I(lambda: self.sma - 2*self.stddev, name='Lower BB')
        self.swing_high = self.I(talib.MAX, self.data.High, self.swing_period, name='Swing High')
        self.swing_low = self.I(talib.MIN, self.data.Low, self.swing_period, name='Swing Low')
        self.volume_ma = self.I(talib.SMA, self.data.Volume, 20, name='Volume MA')

    def next(self):
        if len(self.data) < max(self.bb_period, self.swing_period):
            return

        # 🌙 Current Market Conditions
        current_close = self.data.Close[-1]
        bandwidth = (self.upper_band[-1] - self.lower_band[-1])/self.sma[-1]
        
        # ✨ Squeeze Detection
        squeeze_active = bandwidth < self.squeeze_threshold
        
        # 🚨 Liquidation Cluster Checks
        near_upper = current_close >= self.upper_band[-1] * 0.995
        near_lower = current_close <= self.lower_band[-1] * 1.005
        volume_spike = self.data.Volume[-1] > self.volume_ma[-1]

        if not self.position:
            # 🌕 LONG Entry: Squeeze + Lower Band + Cluster Support
            if squeeze_active and near_lower and volume_spike:
                if current_close >= self.swing_low[-1] * 0.99:
                    risk_amount = self.equity * self.risk_pct
                    sl_price = self.swing_low[-1] * 0.99
                    position_size = int(round(risk_amount/(current_close - sl_price)))
                    self.buy(size=position_size, sl=sl_price, 
                            tag="🌙 LONG: Squeeze + Cluster Support!")
                    print(f"🌕 MOON DEV LONG ENTRY @ {current_close:.2f} | Size: {position_size} 🚀")

            # 🌑 SHORT Entry: Squeeze + Upper Band + Cluster Resistance
            elif squeeze_active and near_upper and volume_spike:
                if current_close <= self.swing_high[-1] * 1.01:
                    risk_amount = self.equity * self.risk_pct
                    sl_price = self.swing_high[-1] * 1.01
                    position_size = int(round(risk_amount/(sl_price - current_close)))
                    self.sell(size=position_size, sl=sl_price,
                             tag="🌙 SHORT: Squeeze + Cluster Resistance!")
                    print(f"🌑 MOON DEV SHORT ENTRY @ {current_close:.2f} | Size: {position_size} 💥")

        else:
            # 🎯 Exit Rules
            position_age = len(self.data) - self.position.entry_bar
            
            # Breakout Exit
            if (self.position.is_long and current_close > self.upper_band[-1]) or \
               (self.position.is_short and current_close < self.lower_band[-1]):
                self.position.close()
                print(f"🎯 MOON DEV BREAKOUT EXIT