```python
# 🌙 Moon Dev's FadeVortex Backtest Implementation
import pandas as pd
import talib
import pandas_ta as ta
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover, crossunder
from pathlib import Path

# ================ DATA PREPARATION ================
def load_data(data_path):
    # Load and clean data
    data = pd.read_csv(data_path)
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    
    # Column mapping with proper case
    data.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }, inplace=True)
    
    # Convert datetime and set index
    data['datetime'] = pd.to_datetime(data['datetime'])
    data.set_index('datetime', inplace=True)
    return data

# ================ STRATEGY CLASS ================
class FadeVortex(Strategy):
    # Strategy parameters
    ci_period = 14
    bb_period = 20
    vwap_period = 20
    volume_ma_period = 5
    recent_extreme_period = 5
    risk_pct = 0.01  # 1% risk per trade
    
    def init(self):
        # ===== INDICATORS =====
        # Choppiness Index (pandas_ta implementation)
        self.ci = self.I(ta.chop,
                        self.data.High, 
                        self.data.Low, 
                        self.data.Close, 
                        length=self.ci_period,
                        name='Choppiness')
        
        # Volume MA (using TALib)
        self.volume_ma = self.I(talib.SMA,
                               self.data.Volume,
                               timeperiod=self.volume_ma_period,
                               name='Volume MA')
        
        # Bollinger Bands (using TALib)
        self.upper_bb, self.middle_bb, self.lower_bb = [
            self.I(talib.BBANDS,
                  self.data.Close,
                  timeperiod=self.bb_period,
                  nbdevup=2,
                  nbdevdn=2,
                  matype=0,
                  position=i,
                  name=f'BB_{["Upper","Middle","Lower"][i]}')
            for i in range(3)
        ]
        
        # 20-period VWAP (manual calculation)
        def calculate_vwap():
            tp = (self.data.High + self.data.Low + self.data.Close) / 3
            tp_volume = tp * self.data.Volume
            return talib.SUM(tp_volume, timeperiod=20) / talib.SUM(self.data.Volume, timeperiod=20)
        
        self.vwap = self.I(calculate_vwap, name='VWAP')
        
        # Recent extremes
        self.recent_high = self.I(talib.MAX,
                                 self.data.High,
                                 timeperiod=self.recent_extreme_period,
                                 name='Recent High')
        self.recent_low = self.I(talib.MIN,
                                self.data.Low,
                                timeperiod=self.recent_extreme_period,
                                name='Recent Low')
        
        # Track entry bar for time-based exits
        self.entry_bar = None

    def next(self):
        # Skip first bars until all indicators are ready
        if len(self.data) < max(self.ci_period, self.bb_period, self.vwap_period) + 1:
            return
        
        # ===== ENTRY LOGIC =====
        current_ci = self.ci[-1]
        current_volume = self.data.Volume[-1]
        volume_ma = self.volume_ma[-1]
        
        # Common entry conditions
        if current_ci > 75 and current_volume < volume_ma:
            price = self.data.Close[-1]
            vwap = self.vwap[-1]
            
            # Short Entry: Price near recent high
            if self.data.High[-1] >= self.recent_high[-1] * 0.999:
                if not self.position.is_short:
                    self.calculate_position_size('short')
            
            # Long Entry: Price near recent low
            elif self.data.Low[-1] <= self.recent_low[-1] * 1.001:
                if not self.position.is_long:
                    self.calculate_position_size('long')

        # ===== EXIT LOGIC =====
        if self.position.is_long:
            # Long exit conditions
            if