```python
# 🌙 MOON DEV BACKTESTING SCRIPT - CONFLUENCE BREAKOUT STRATEGY ✨

import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

class ConfluenceBreakout(Strategy):
    # Strategy parameters
    bb_period = 20
    bb_dev = 2
    kc_period = 20
    kc_multiplier = 1.5
    atr_trailing_period = 14
    risk_pct = 0.01
    
    def init(self):
        # 🌙 INDICATOR SETUP
        # Bollinger Bands
        def bb_upper(close, timeperiod, nbdevup, nbdevdn, matype):
            upper, _, _ = talib.BBANDS(close, timeperiod=timeperiod, 
                                      nbdevup=nbdevup, nbdevdn=nbdevdn, matype=matype)
            return upper
        
        self.bb_upper = self.I(bb_upper, self.data.Close, 
                              timeperiod=self.bb_period, 
                              nbdevup=self.bb_dev, 
                              nbdevdn=self.bb_dev,
                              matype=0,
                              name='BB_UPPER')
        
        # Keltner Channel components
        typical_price = (self.data.High + self.data.Low + self.data.Close) / 3
        self.kc_middle = self.I(talib.EMA, typical_price, 
                                timeperiod=self.kc_period,
                                name='KC_MIDDLE')
        self.atr_kc = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close,
                            timeperiod=self.kc_period, name='ATR_KC')
        
        # Volume MA
        self.volume_ma = self.I(talib.SMA, self.data.Volume, 
                               timeperiod=20, name='VOLUME_MA')
        
        # Trailing ATR
        self.atr_trailing = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close,
                                  timeperiod=self.atr_trailing_period, name='ATR_TRAIL')
        
        # Trade tracking
        self.entry_atr = None
        self.max_high = 0
        self.min_low = float('inf')

    def next(self):
        # 🌙 CALCULATE CURRENT VALUES
        current_close = self.data.Close[-1]
        current_volume = self.data.Volume[-1]
        
        # Keltner Channel dynamic calculation
        kc_upper = self.kc_middle[-1] + (self.atr_kc[-1] * self.kc_multiplier)
        kc_lower = self.kc_middle[-1] - (self.atr_kc[-1] * self.kc_multiplier)
        
        # 🌙 ENTRY LOGIC
        if not self.position:
            # Long entry conditions
            if (current_close > self.bb_upper[-1] and 
                current_close > kc_upper and 
                current_volume > self.volume_ma[-1]):
                
                # Risk management calculations
                self.entry_atr = self.atr_trailing[-1]
                risk_amount = self.equity * self.risk_pct
                risk_per_share = 1.5 * self.entry_atr
                position_size = int(round(risk_amount / risk_per_share))
                
                if position_size > 0:
                    sl_price = current_close - (1.5 * self.entry_atr)
                    self.buy(size=position_size, sl=sl_price)
                    self.max_high = current_close  # Reset high tracker
                    print(f"🌙✨ LONG ENTRY at {current_close:.2f} | Size: {position_size} 🚀")

            # Short entry conditions    
            elif (current_close < self.bb_lower[-1] and 
                  current_close < kc_lower and 
                  current_volume > self.volume_ma[-1]):
                
                self.entry_atr = self.atr_trailing[-1]
                risk_amount = self.equity * self.risk_pct
                risk_per_share = 1.5 * self.entry_atr
                position_size = int(round(risk_amount / risk_per_share))
                
                if position_size > 0:
                    sl_price = current_close + (1.5 * self.entry_atr)
                    self.sell(size=position_size, sl=sl_price)
                    self.min_low = current_close  # Reset low tracker
                    print(f"