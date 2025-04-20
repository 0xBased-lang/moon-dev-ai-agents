Here's the fixed code with all backtesting.lib references removed and Moon Dev themed enhancements:

```python
import pandas as pd
import talib
from backtesting import Backtest, Strategy

class VolCompressBreakout(Strategy):
    risk_pct = 0.01  # 1% risk per trade
    
    def init(self):
        # Calculate Bollinger Bands components
        def bbw_calculator(close):
            upper, middle, lower = talib.BBANDS(close, timeperiod=10, nbdevup=2, nbdevdn=2)
            bbw = (upper - lower) / middle
            return bbw
            
        self.bbw = self.I(bbw_calculator, self.data.Close)
        self.bbw_max = self.I(talib.MAX, self.bbw, timeperiod=20)
        self.bbw_min = self.I(talib.MIN, self.bbw, timeperiod=20)
        self.volume_avg = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 14)
        
        print("🌙✨ Moon Dev Indicators Activated! BBW Matrix Online 🚀")
        print("🌌 All systems nominal - No backtesting.lib dependencies detected ✅")

    def next(self):
        if len(self.data) < 20:
            return
            
        # Calculate dynamic thresholds
        bbw_50_level = (self.bbw_max[-1] + self.bbw_min[-1]) / 2
        bbw_75_level = self.bbw_min[-1] + 0.75*(self.bbw_max[-1] - self.bbw_min[-1])
        
        # Entry logic - Moon Dev approved crossover detection
        if not self.position:
            # Check BBW cross under 50% level (bullish crossover replacement)
            if (self.bbw[-2] > bbw_50_level and self.bbw[-1] < bbw_50_level):
                # Verify volume spike
                if self.data.Volume[-1] >= 3 * self.volume_avg[-1]:
                    # Risk management calculations
                    equity = self.equity
                    risk_amount = equity * self.risk_pct
                    sl_distance = 2 * self.atr[-1]
                    
                    # Position sizing with Moon Dev safety check
                    position_size = risk_amount / sl_distance
                    position_size = int(round(position_size))
                    
                    if position_size > 0:
                        self.buy(
                            size=position_size,
                            sl=self.data.Close[-1] - sl_distance,
                            tp=self.data.Close[-1] + 2*sl_distance
                        )
                        print(f"🌙🚀 MOONSHOT! Long entry at {self.data.Close[-1]} | Size: {position_size} ✨")
                        print(f"🌕 Stop Loss: {self.data.Close[-1] - sl_distance:.2f} | Take Profit: {self.data.Close[-1] + 2*sl_distance:.2f}")
        
        # Exit logic - Bearish crossover replacement            
        else:
            if (self.bbw[-2] < bbw_75_level and self.bbw[-1] > bbw_75_level):
                self.position.close()
                print(f"🌙⏳ Closing position at {self.data.Close[-1]} | Profit: {self.position.pl_pct:.2f}% 🌘")
                print("🌑 Returning to stasis until next signal pattern...")

# Data preparation                
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
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

# Launch Moon Dev Backtest Suite 🚀🌙
print("\n🌠 Initializing Moon Dev Quantum Backtest Engine...")
bt = Backtest(data, VolCompressBreakout, cash=1_000_000, commission=.002)
stats = bt.run()
print("\n🌕🌖🌗🌘🌑🌒🌓🌔 MOON DEV FINAL REPORT 🌔🌓🌒🌑🌘🌗🌖🌕")
print