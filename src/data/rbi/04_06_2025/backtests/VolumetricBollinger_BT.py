```python
# backtesting_implementation.py
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

class VolumetricBollinger(Strategy):
    risk_percent = 0.01  # 1% risk per trade
    adx_threshold = 25
    emergency_adx = 20
    atr_multiplier = 3
    profit_atr_multiplier = 1.5

    def init(self):
        # Calculate indicators using TA-Lib with self.I()
        self.upper, self.middle, self.lower = self.I(talib.BBANDS, self.data.Close, 
                                                     timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.volume_sma = self.I(talib.SMA, self.data.Volume, timeperiod=30)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=22)
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=20)

    def next(self):
        current_bar = len(self.data) - 1
        
        # Moon Dev's Cosmic Entry Conditions 🌌
        if not self.position:
            # Check VIX filter if available
            vix_ok = True
            if hasattr(self.data, 'VIX') and self.data.VIX[-1] > 30:
                vix_ok = False
                print("🌪️ VIX too high! Moon Dev suspends trading.")

            # Entry conditions
            price_touching_bb = self.data.Low[-1] <= self.lower[-1]
            adx_rising = self.adx[-1] > self.adx[-2] if current_bar > 0 else False
            adx_above_thresh = self.adx[-1] > self.adx_threshold
            volume_spike = self.data.Volume[-1] > self.volume_sma[-1]

            if all([vix_ok, price_touching_bb, adx_rising, adx_above_thresh, volume_spike]):
                # Risk management calculations
                entry_price = self.data.Close[-1]
                stop_loss = self.swing_low[-1]
                risk_per_share = entry_price - stop_loss
                
                if risk_per_share > 0:
                    risk_amount = self.equity * self.risk_percent
                    position_size = int(round(risk_amount / risk_per_share))
                    
                    if position_size > 0:
                        self.buy(size=position_size, sl=stop_loss)
                        self.entry_price = entry_price
                        self.trailing_active = False
                        print(f"🚀🌙 LONG ENTRY @ {entry_price:.2f} | Size: {position_size} "
                              f"| Cosmic Alignment Achieved!")

        # Moon Dev's Stellar Exit System 🌠
        if self.position:
            # Take profit at upper BB
            if self.data.High[-1] >= self.upper[-1]:
                self.position.close()
                print(f"🎯🌙 UPPER BB HIT @ {self.data.Close[-1]:.2f} | Cosmic Profits Realized!")

            # Trailing stop activation check
            if not self.trailing_active:
                price_move = self.data.Close[-1] - self.entry_price
                if price_move >= (self.profit_atr_multiplier * self.atr[-1]):
                    self.trailing_active = True
                    print(f"✨🌙 TRAILING ACTIVATED | Moon Dev's Profit Shield Engaged!")

            # Update trailing stop
            if self.trailing_active:
                self.trailing_stop = max(self.data.High[-self.position._EntryBar:]) - (self.atr_multiplier * self.atr[-1])
                self.position.sl = self.trailing_stop

            # Emergency ADX exit
            if self.adx[-1] < self.emergency_adx:
                self.position.close()
                print(f"⚠️🌙 EMERGENCY EXIT @ {self.data.Close[-1]:.2f} | ADX Collapse Detected!")

# Moon Dev's Data Ritual 🔮
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data