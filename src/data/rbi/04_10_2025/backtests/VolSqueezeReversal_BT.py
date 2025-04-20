```python
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import talib
import pandas as pd
import pandas_ta as ta

def bbands_upper(close, timeperiod=20, nbdev=2):
    upper, _, _ = talib.BBANDS(close, timeperiod=timeperiod, nbdevup=nbdev, nbdevdn=nbdev, matype=0)
    return upper

def bbands_middle(close, timeperiod=20, nbdev=2):
    _, middle, _ = talib.BBANDS(close, timeperiod=timeperiod, nbdevup=nbdev, nbdevdn=nbdev, matype=0)
    return middle

def bbands_lower(close, timeperiod=20, nbdev=2):
    _, _, lower = talib.BBANDS(close, timeperiod=timeperiod, nbdevup=nbdev, nbdevdn=nbdev, matype=0)
    return lower

class VolSqueezeReversal(Strategy):
    def prepare(self):
        # Clean and prepare data 🌙
        self.data.columns = self.data.columns.str.strip().str.lower()
        self.data = self.data.drop(columns=[col for col in self.data.columns if 'unnamed' in col])
        self.data.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }, inplace=True)
        
        if 'fundingrate' not in self.data.columns:
            raise ValueError("🚨 MOON DEV CRITICAL: Funding rate column missing!")

    def init(self):
        # Bollinger Band components ✨
        close = self.data.Close
        self.bb_upper = self.I(bbands_upper, close, 20, 2)
        self.bb_middle = self.I(bbands_middle, close, 20, 2)
        self.bb_lower = self.I(bbands_lower, close, 20, 2)
        
        # Volatility calculations 🌊
        self.bbw = self.I(lambda u, l, m: (u - l)/m, self.bb_upper, self.bb_lower, self.bb_middle)
        self.bbw_min = self.I(talib.MIN, self.bbw, 63)
        
        # ATR system 🌡️
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 14)
        self.atr_90th = self.I(lambda x: x.rolling(63).quantile(0.9), self.atr)

    def next(self):
        if len(self.data) < 63:
            return  # Wait for warmup 🌙
            
        if self.position:
            # Exit on volatility expansion 🚀
            if self.atr[-1] > self.atr_90th[-1]:
                self.position.close()
                print(f"🌕 MOON DEV EXIT SIGNAL: ATR Spike {self.atr[-1]:.2f} > {self.atr_90th[-1]:.2f}")
        else:
            # Entry logic 🌙✨
            current_bbw = self.bbw[-1]
            current_min = self.bbw_min[-1]
            funding = self.data.fundingrate[-1]
            
            if abs(current_bbw - current_min) < 1e-9 and funding < 0:
                # Risk management 🌗
                equity = self.equity
                entry_price = self.data.Close[-1]
                stop_loss = entry_price * (1 - 1.5*current_bbw)
                risk_per_unit = entry_price - stop_loss
                
                if risk_per_unit <= 0:
                    print("🚨 MOON DEV ALERT: Invalid risk calculation!")
                    return
                
                position_size = int(round((0.02 * equity) / risk_per_unit))
                
                if position_size > 0:
                    self.buy(size=position_size, sl=stop_loss)
                    print(f"🌙✨ MOON DEV ENTRY: Size {position_size} @ {entry_price:.2f} | SL: {stop_loss:.2f}")

# Execute backtest 🚀🌕
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv',
                   parse_dates=['datetime'], index_col='datetime')
bt = Backtest(data, VolSqueezeReversal, cash=1_000_000, commission=.002)