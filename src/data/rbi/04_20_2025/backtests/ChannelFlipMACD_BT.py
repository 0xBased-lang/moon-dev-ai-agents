import pandas as pd
import talib
from backtesting import Backtest, Strategy

class ChannelFlipMACD(Strategy):
    def init(self):
        self.donchian_upper = self.I(talib.MAX, self.data.High, 20)
        self.donchian_lower = self.I(talib.MIN, self.data.Low, 20)
        self.macd_hist = self.I(lambda c: talib.MACD(c, 12, 26, 9)[2], self.data.Close)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 14)
        self.highest_high = None

    def next(self):
        price = self.data.Close[-1]
        
        if not self.position:
            hist = self.macd_hist
            if (len(hist) > 1 and hist[-1] > 0 and hist[-2] <= 0
                and price > self.donchian_upper[-1]
                and (self.atr[-1]/price) <= 0.03):
                
                risk_amount = self.equity * 0.01
                stop = 2 * self.atr[-1]
                size = int(round(risk_amount / stop))
                
                if size > 0:
                    self.buy(size=size, sl=price-stop)
                    self.highest_high = self.data.High[-1]
                    print(f"🌙✨🚀 MOON DEV LONG ENTRY @ {price:.2f} | Size: {size} | SL: {price-stop:.2f}")

        elif self.position.is_long:
            self.highest_high = max(self.highest_high, self.data.High[-1])
            new_sl = self.highest_high - 2*self.atr[-1]
            if new_sl > self.position.sl:
                self.position.sl = new_sl
                print(f"🔧 Updated Moon Trail SL: {new_sl:.2f}")

# Data preprocessing
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
data.rename(columns={k: k.title() for k in data.columns}, inplace=True)
data.set_index(pd.to_datetime(data['Datetime']), inplace=True)
data = data[['Open', 'High', 'Low', 'Close', 'Volume']]

bt = Backtest(data, ChannelFlipMACD, cash=1_000_000)
stats = bt.run()
print(stats)
print(stats._strategy)