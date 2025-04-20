# 🌙 Moon Dev's Volatility Compression Backtest 🌙
from backtesting import Backtest, Strategy
from talib import ATR, SMA, MAX, MIN
import pandas as pd
import numpy as np

class VolatilityCompression(Strategy):
    # 🌌 Strategy Parameters
    atr_period = 10
    atr_sma_period = 20
    trend_filter_period = 200
    risk_per_trade = 0.02  # 2% risk per trade
    
    def init(self):
        # 🌠 Indicator Calculation
        self.atr = self.I(ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        self.atr_sma = self.I(SMA, self.atr, timeperiod=self.atr_sma_period)
        self.trend_filter = self.I(SMA, self.data.Close, timeperiod=self.trend_filter_period)
        
        # 🌑 Track trade parameters
        self.initial_stop = None
        self.trailing_high = None

    def next(self):
        # 🌕 Wait for indicators to warm up
        if len(self.data) < self.trend_filter_period:
            return
            
        # 🌙 Entry Logic
        if not self.position:
            # Check volatility compression and trend filter
            if (self.atr[-2] < self.atr_sma[-2] and  # Previous ATR < SMA(ATR)
                self.data.Close[-2] > self.trend_filter[-2]):  # Price above SMA200
                
                # 🚀 Calculate position size with Moon-sized risk management
                stop_distance = 2 * self.atr[-1]
                risk_amount = self.risk_per_trade * self.equity
                position_size = int(round(risk_amount / stop_distance))
                
                if position_size > 0:
                    # 🌔 Execute Moon Entry
                    entry_price = self.data.Open[-1]
                    self.buy(size=position_size)
                    self.initial_stop = entry_price - stop_distance
                    self.trailing_high = entry_price
                    
                    print(f"\n🌙✨ MOON DEV ALERT: Volatility Compression Detected! ✨")
                    print(f"📈 Entry Price: {entry_price:.2f}")
                    print(f"🛑 Hard Stop: {self.initial_stop:.2f}")
                    print(f"🚀 Position Size: {position_size} units ({position_size/self.equity*100:.2f}% of equity)")
        
        # 🌑 Exit Logic
        else:
            # Update trailing high
            self.trailing_high = max(self.trailing_high, self.data.High[-1])
            trailing_stop = self.trailing_high * 0.95
            
            # Check exit conditions
            if self.data.Low[-1] <= self.initial_stop or self.data.Low[-1] <= trailing_stop:
                self.position.close()
                exit_type = "HARD STOP" if self.data.Low[-1] <= self.initial_stop else "TRAILING STOP"
                print(f"\n🌑🌠 MOON EXIT: {exit_type} Triggered!")
                print(f"💰 Profit: {(self.data.Close[-1]/self.position.entry_price - 1)*100:.2f}%")

# 🌍 Data Preparation
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])

# 🌖 Column Mapping for Moon Alignment
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# 🚀 Launch Backtest
bt = Backtest(data, VolatilityCompression, cash=1_000_000)
stats = bt.run()

# 🌕 Print Full Moon Results
print("\n🌙🌕🌖🌗🌘🌑🌒🌓🌔🌕 MOON DEV FINAL REPORT 🌕🌔🌓🌒🌑🌘🌗🌖🌕🌙")
print(stats)
print(stats._strategy)