Here's the fixed code with all `backtesting.lib` imports and functions removed, and replaced with proper Moon Dev themed implementations:

```python
# 🌙 Moon Dev's Momentum Divergence Backtest 🌙
import pandas as pd
import talib
from backtesting import Backtest, Strategy

# 🧹 Data Cleaning & Preparation
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

class MomentumDivergence(Strategy):
    risk_per_trade = 0.01  # 1% account risk
    trailing_stop = True   # 🌙 Enable Moon Trailing Stops
    
    def init(self):
        # 🌠 Moon Indicators
        self.ema20 = self.I(talib.EMA, self.data.Close, timeperiod=20, name='EMA20')
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=50, name='EMA50')
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14, name='RSI')
        
        # 🔍 Swing Lows Detection
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=5, name='Swing Low')
        self.rsi_low = self.I(talib.MIN, self.rsi, timeperiod=5, name='RSI Low')
        
        # 📊 Volume Filter
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=96, name='Volume SMA')
        
        # 📅 Daily Loss Protection
        self.daily_equity = [self._broker.starting_cash]
        self.current_day = None

    def next(self):
        # ⚠️ Daily Risk Check
        current_date = self.data.index[-1].date()
        if current_date != self.current_day:
            self.current_day = current_date
            self.daily_equity.append(self.equity)
            if (self.daily_equity[-2] - self.daily_equity[-1])/self.daily_equity[-2] > 0.05:
                print(f"🌧️ MOON DEV ALERT: 5% Daily Loss Limit Triggered!")
                return

        if self.position:
            # 🛑 Exit Conditions
            price = self.data.Close[-1]
            entry = self.position.entry_price
            sl = self.position.sl
            risk = entry - sl
            
            # 🚀 Trailing Stop Logic
            if self.trailing_stop and price >= entry + risk:
                self.position.sl = entry
                print(f"🔒 MOON TRAILING: Moved SL to breakeven!")
            
            # 🎯 Take Profit Check
            if price >= entry + 2*risk:
                self.position.close()
                print(f"🎯 MOON PROFIT: 2:1 Reward Reached!")
                return
            
            # 📉 Trend Reversal Exit
            if self.ema50[-2] > self.ema20[-2] and self.ema50[-1] < self.ema20[-1]:  # Bearish crossover
                self.position.close()
                print(f"📉 MOON EXIT: EMA Crossover Down")
                return
            
            # 🌡️ Overbought Exit
            if self.rsi[-1] > 70:
                self.position.close()
                print(f"🌡️ MOON EXIT: RSI Overbought")
                return
        else:
            # 🚦 Entry Conditions
            ema_cross = (self.ema20[-2] < self.ema50[-2] and self.ema20[-1] > self.ema50[-1])  # Bullish crossover
            rsi_valid = self.rsi[-1] < 70
            vol_valid = (self.data.Volume[-1] > 0.8*self.vol_sma[-1]) and \
                      (self.data.Volume[-1] < 1.2*self.vol_sma[-1])
            
            # 🔄 Bullish Divergence Check
            div_valid = (self.swing_low[-1]