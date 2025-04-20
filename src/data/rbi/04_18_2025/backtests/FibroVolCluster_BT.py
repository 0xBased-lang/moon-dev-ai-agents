```python
import pandas as pd
import talib
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover, crossunder

# Moon Dev Data Preparation 🌙✨
def prepare_data(path):
    data = pd.read_csv(path)
    # Clean column names
    data.columns = data.columns.str.strip().str.lower()
    # Drop unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
    # Map columns to backtesting.py format
    data = data.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    return data

data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = prepare_data(data_path)

class FibroVolCluster(Strategy):
    risk_pct = 0.01  # 1% risk per trade 🌙
    max_exposure = 0.05  # 5% portfolio exposure 🚀
    swing_period = 20
    consolidation_bars = 10
    bb_period = 20
    bb_dev = 2
    atr_period = 14
    
    def init(self):
        # Moon Dev Indicators 🌙📈
        self.swing_high = self.I(talib.MAX, self.data.High, self.swing_period, name='Swing High')
        self.swing_low = self.I(talib.MIN, self.data.Low, self.swing_period, name='Swing Low')
        
        # Bollinger Bands for volatility
        self.upper_bb, self.middle_bb, self.lower_bb = self.I(
            talib.BBANDS, self.data.Close, 
            timeperiod=self.bb_period, nbdevup=self.bb_dev, 
            nbdevdn=self.bb_dev, matype=0, name='BBANDS'
        )
        self.bb_width = (self.upper_bb - self.lower_bb) / self.middle_bb
        
        # OBV for volume confirmation
        self.obv = self.I(talib.OBV, self.data.Close, self.data.Volume, name='OBV')
        
        # Swing detection for OBV divergence
        self.obv_highs = self.I(talib.MAX, self.obv, 5, name='OBV Highs')
        self.obv_lows = self.I(talib.MIN, self.obv, 5, name='OBV Lows')
        self.price_highs = self.I(talib.MAX, self.data.High, 5, name='Price Highs')
        self.price_lows = self.I(talib.MIN, self.data.Low, 5, name='Price Lows')
        
        # ATR for volatility filter
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, self.atr_period, name='ATR')

    def next(self):
        # Moon Dev Core Logic 🌙⚡
        if len(self.data) < 50 or self.position:
            return
            
        # Calculate current Fibonacci levels
        swing_high = self.swing_high[-1]
        swing_low = self.swing_low[-1]
        if swing_high is None or swing_low is None:
            return
            
        fib_382 = swing_high - (swing_high - swing_low) * 0.382
        fib_618 = swing_high - (swing_high - swing_low) * 0.618
        
        # Volatility contraction check
        bb_width = self.bb_width[-1]
        atr = self.atr[-1]
        volatility_ok = bb_width < 0.05 or atr < np.nanmean(self.atr[-self.atr_period:])
        
        # Price consolidation check
        in_zone = all(fib_618 < close < fib_382 for close in self.data.Close[-self.consolidation_bars:])
        
        # OBV divergence detection
        bullish_div = (self.price_lows[-1] < self.price_lows[-2] and 
                      self.obv_lows[-1] > self.obv_lows[-2])
        bearish_div = (self.price_highs[-1] > self.price_highs[-2] and 
                      self.obv_highs