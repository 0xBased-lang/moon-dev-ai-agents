# 🌙 Moon Dev's Yield Curve Reversal Backtest 🌙
from backtesting import Backtest, Strategy
import pandas as pd
import talib
import numpy as np

# 🚀 Data Preparation Rocket Launch 🚀
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')

# 🌌 Cosmic Data Cleaning 🌌
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)

class YieldCurveReversal(Strategy):
    risk_pct = 0.02  # 🌑 2% Moon Dust Risk per Trade
    tp_pct = 0.05    # 🚀 5% Rocket Fuel Take Profit
    sl_pct = 0.02    # 🛡️ 2% Force Field Stop Loss
    
    def init(self):
        # 🌠 Cosmic Indicator Initialization 🌠
        self.vix_curve = self.I(lambda x: x, self.data.df['vix_futures_30d'], name='VIX_CURVE')
        self.treasury_3m = self.I(lambda x: x, self.data.df['treasury_3m'], name='TREASURY_3M')
        self.ma50 = self.I(talib.SMA, self.data.Close, timeperiod=50, name='MA50')
        self.price = self.data.Close
        
        print("🌕 Lunar Indicators Activated: VIX Curve, Treasury Yield, MA50")
        print("✨ Moon Dev AI successfully initialized all cosmic indicators! 🌌")

    def next(self):
        # 🌙 Moon Phase Check - Wait for full indicator formation 🌙
        if len(self.data.Close) < 50:
            print("🌑 Waiting for full moon phase (indicator formation)...")
            return

        current_price = self.data.Close[-1]
        equity = self.equity
        position = self.position

        # 🌓 Cosmic Divergence Detection 🌓
        yield_spread = self.vix_curve[-1] - self.treasury_3m[-1]
        
        # 🚀 Long Entry: Negative Yield Spread 🌌
        if not position and yield_spread < 0:
            risk_amount = equity * self.risk_pct
            sl_price = current_price * (1 - self.sl_pct)
            risk_per_share = current_price - sl_price
            
            if risk_per_share > 0:
                position_size = risk_amount / risk_per_share
                position_size = int(round(position_size))
                
                if position_size > 0:
                    tp_price = current_price * (1 + self.tp_pct)
                    self.buy(size=position_size, sl=sl_price, tp=tp_price)
                    print(f"🌙✨🚀 MOON SHOT! Long Entry @ {current_price:.2f}")
                    print(f"   Size: {position_size} | SL: {sl_price:.2f} | TP: {tp_price:.2f}")
                    print("🌌 Cosmic alignment achieved! Negative yield spread detected 🌠")

        # 🌗 Exit Signal: Price Descends Below MA50 🌘
        elif position and self.ma50[-2] > self.price[-2] and self.ma50[-1] < self.price[-1]:
            self.position.close()
            print(f"🌙☄️ COMET RETREAT! Exit @ {current_price:.2f}")
            print("🌑 Price descended below MA50 - Cosmic retreat initiated! 🛡️")

# 🌕 Launching Moon Base Backtest 🌕
bt = Backtest(data, YieldCurveReversal, cash=1_000_000, exclusive_orders=True)
stats = bt.run()

# 🌟 Cosmic Performance Report 🌟
print("\n🌌🌠🌑 MOON DEV FINAL REPORT 🌑🌠🌌")
print(stats)
print(stats._strategy)
print("✨🌙 Moon Dev AI successfully completed cosmic backtest! 🌌🚀")