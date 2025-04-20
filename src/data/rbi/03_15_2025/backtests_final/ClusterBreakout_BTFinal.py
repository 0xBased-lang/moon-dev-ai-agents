Here's the debugged code with Moon Dev themed fixes 🌙✨. I've addressed technical issues while preserving the original strategy logic:

```python
import pandas as pd
import talib
from backtesting import Backtest, Strategy

class ClusterBreakout(Strategy):
    risk_pct = 0.01  # 1% risk per trade
    
    def init(self):
        # 🌙 Calculate Moon Indicators
        self.cluster_high = self.I(talib.MAX, self.data.High, timeperiod=20, name='🌙 Cluster High')
        self.cluster_low = self.I(talib.MIN, self.data.Low, timeperiod=20, name='🌙 Cluster Low')
        self.trend_low = self.I(talib.MIN, self.data.Low, timeperiod=50, name='✨ Trend Low')
        self.entry_price = None

    def next(self):
        # Wait for enough data points
        if len(self.data) < 50:
            return

        # 🚀 Entry Logic
        if not self.position:
            # Check ascending trend condition
            if self.trend_low[-1] > self.trend_low[-2]:
                # Breakout confirmation
                if self.data.Close[-1] > self.cluster_high[-1]:
                    stop_loss_price = self.trend_low[-1]
                    
                    # 🌙 Calculate Moon Position Size
                    risk_per_share = self.data.Close[-1] - stop_loss_price
                    if risk_per_share <= 0:
                        print("🌑⚠️ Risk per share <= 0 - Cosmic anomaly avoided!")
                        return
                        
                    position_size = (self.equity * self.risk_pct) / risk_per_share
                    position_size = int(round(position_size))  # 🌙 Round to whole units
                    
                    if position_size > 0:
                        self.buy(size=position_size)
                        self.entry_price = self.data.Close[-1]
                        print(f"🚀🌕 **LIFTOFF!** Buying {position_size} units at {self.entry_price:.2f}")
                        print(f"   🌙 Stop Loss: {stop_loss_price:.2f} | Cluster High: {self.cluster_high[-1]:.2f}")

        # ✨ Exit Logic
        elif self.position:
            current_price = self.data.Close[-1]
            
            # 1% Retracement Exit
            if current_price < self.entry_price * 0.99:
                self.position.close()
                print(f"🌑✨ **GRAVITY PULL** Selling at {current_price:.2f} (1% Retracement)")
                
            # Trend Line Break Exit
            elif current_price < self.trend_low[-1]:
                self.position.close()
                print(f"🌑🌪️ **BLACK HOLE EXIT** Selling at {current_price:.2f} (Trend Break)")

# 🌙 Cosmic Data Preparation
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
try:
    data = pd.read_csv(data_path)
    
    # Clean column names
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])

    # Map to backtesting.py format
    data.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }, inplace=True)

    # Convert datetime
    if 'datetime' in data.columns:
        data['DateTime'] = pd.to_datetime(data['datetime'])
        data.set_index('DateTime', inplace=True)
        data.sort_index(inplace=True)
    else:
        raise ValueError("🌑⚠️ No datetime column found in data - Cosmic alignment failed!")
        
except Exception as e:
    print(f"🌑⚠️ Data loading error: {str(e)}")
    raise

# 🚀 Launch Backtest
try:
    bt = Backtest(data, ClusterBreakout, cash=1_000_000, commission=.002)
    stats = bt.run()

    # 🌕 Display Moon Results
    print("\n🌙✨🌙✨🌙✨🌙✨🌙✨🌙✨🌙✨🌙✨")
    print("      MOON DEV BACKTEST RESULTS")
    print("🌙✨🌙✨🌙✨🌙✨🌙✨🌙✨🌙✨🌙✨\n")
    print(stats)
    print("\n🌙 Strategy Details:")
    print(stats._strategy)

except Exception as e:
    print(f"