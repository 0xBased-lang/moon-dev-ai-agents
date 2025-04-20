I'll fix the code to remove all `backtesting.lib` imports and replace crossover functions with proper implementations. Here's the corrected version with Moon Dev's package requirements:

```python
import pandas as pd
import pandas_ta as ta
import talib
from backtesting import Backtest, Strategy

class VortexSurge(Strategy):
    def init(self):
        # Clean data handled externally - now calculate indicators
        self.vi_plus = self.I(ta.vortex, high=self.data.High, low=self.data.Low, length=14, name='VI+').iloc[:,0]
        self.vi_minus = self.I(ta.vortex, high=self.data.High, low=self.data.Low, length=14, name='VI-').iloc[:,1]
        
        # Price levels
        self.high_20 = self.I(talib.MAX, self.data.High, timeperiod=20, name='SwingHigh20')
        self.low_20 = self.I(talib.MIN, self.data.Low, timeperiod=20, name='SwingLow20')
        
        # Volume analysis
        self.volume_ma = self.I(talib.SMA, self.data.Volume, timeperiod=20, name='VolMA20')
        
        # Bollinger Bands Width
        upper, _, lower = self.I(talib.BBANDS, self.data.Close, 
                               timeperiod=20, nbdevup=2, nbdevdn=2, 
                               name=['BB_upper', 'BB_mid', 'BB_lower'])
        self.bbw = self.I(lambda: (upper - lower) / ((upper + lower)/2), name='BBW')
        
        # Volatility measure
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 
                         timeperiod=14, name='ATR14')

    def next(self):
        price = self.data.Close[-1]
        moon_emoji = '🌙✨🚀'  # Standard Moon Dev emojis
        
        # Entry logic
        if not self.position:
            # Long entry conditions (replaced crossover with manual check)
            if ((self.vi_plus[-2] < self.vi_minus[-2] and self.vi_plus[-1] > self.vi_minus[-1]) and
                price > self.high_20[-1] and
                self.data.Volume[-1] > 1.5 * self.volume_ma[-1]):
                
                # Risk management calculations
                sl_price = max(self.data.Low[-1], price - 1.5*self.atr[-1])
                risk_amount = self.equity * 0.01  # 1% risk
                position_size = int(round(risk_amount / (price - sl_price)))
                
                if position_size > 0:
                    self.buy(size=position_size, 
                            sl=sl_price,
                            tp=price + 3*(price - sl_price))
                    print(f"{moon_emoji} LONG ENTRY at {price:.2f}")
                    print(f"Size: {position_size}, SL: {sl_price:.2f}, TP: {price + 3*(price - sl_price):.2f}")
            
            # Short entry conditions (replaced crossover with manual check)
            elif ((self.vi_minus[-2] > self.vi_plus[-2] and self.vi_minus[-1] < self.vi_plus[-1]) and
                  price < self.low_20[-1] and
                  self.data.Volume[-1] > 1.5 * self.volume_ma[-1]):
                
                sl_price = min(self.data.High[-1], price + 1.5*self.atr[-1])
                risk_amount = self.equity * 0.01
                position_size = int(round(risk_amount / (sl_price - price)))
                
                if position_size > 0:
                    self.sell(size=position_size,
                             sl=sl_price,
                             tp=price - 3*(sl_price - price))
                    print(f"{moon_emoji} SHORT ENTRY at {price:.2f}")
                    print(f"Size: {position_size}, SL: {sl_price:.2f}, TP: {price - 3*(sl_price - price):.2f}")

        # Exit logic
        else:
            current_trade = self.position
            # Replaced crossovers with manual checks
            if current_trade.is_long and ((self.vi_minus[-2] < self.vi_plus[-2] and self.vi_minus[-1] > self.vi_plus[-1]) or self