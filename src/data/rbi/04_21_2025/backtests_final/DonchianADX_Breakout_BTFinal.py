import pandas as pd
import talib
from backtesting import Backtest, Strategy

# Load and preprocess data
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

class DonchianADXBreakout(Strategy):
    risk_percent = 0.01
    
    def init(self):
        self.donchian_upper = self.I(talib.MAX, self.data.High, timeperiod=50)
        self.donchian_lower = self.I(talib.MIN, self.data.Low, timeperiod=50)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
    def next(self):
        if len(self.data.Close) < 50:
            return
        
        du = self.donchian_upper[-1]
        dl = self.donchian_lower[-1]
        adx = self.adx[-1]
        prev_adx = self.adx[-2] if len(self.adx) > 1 else 0
        
        if not self.position:
            # Long entry logic
            if self.data.Close[-1] > du and adx > 25 and adx > prev_adx:
                risk_amount = self.risk_percent * self.equity
                risk_per_share = self.data.Close[-1] - dl
                if risk_per_share > 0:
                    size = int(round(risk_amount / risk_per_share))
                    if size > 0:
                        tp = self.data.Close[-1] + 2 * (self.data.Close[-1] - dl)
                        self.buy(size=size, sl=dl, tp=tp)
                        print(f"🚀🌙 MOON SHOT! LONG ENTRY: {self.data.Close[-1]:.2f} | Size: {size} | SL: {dl:.2f} | TP: {tp:.2f}")
            
            # Short entry logic
            elif self.data.Close[-1] < dl and adx > 25 and adx > prev_adx:
                risk_amount = self.risk_percent * self.equity
                risk_per_share = du - self.data.Close[-1]
                if risk_per_share > 0:
                    size = int(round(risk_amount / risk_per_share))
                    if size > 0:
                        tp = self.data.Close[-1] - 2 * (du - self.data.Close[-1])
                        self.sell(size=size, sl=du, tp=tp)
                        print(f"📉🌙 CRATER DIVE! SHORT ENTRY: {self.data.Close[-1]:.2f} | Size: {size} | SL: {du:.2f} | TP: {tp:.2f}")

    def notify_trade(self, trade):
        if trade.is_closed:
            profit = trade.pl
            emoji = "🚀🌙 MOON BOUND!" if profit >= 0 else "💥🌧️ CRASH LANDING!"
            print(f"🌕🌑 MOON CYCLE COMPLETE! {emoji} Closed P&L: ${profit:.2f}")

bt = Backtest(data, DonchianADXBreakout, cash=1_000_000, commission=.002, trade_on_close=True)
stats = bt.run()
print(stats)
print(stats._strategy)