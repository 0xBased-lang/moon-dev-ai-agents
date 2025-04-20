```python
# 🌙 Moon Dev Backtest Engine - VortexAccelTrend Strategy Implementation
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# =====================
# DATA PREPARATION
# =====================
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')

# Clean and format columns
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

# =====================
# CORE STRATEGY CLASS
# =====================
class VortexAccelTrend(Strategy):
    risk_pct = 0.01  # 1% risk per trade 🌙
    atr_multiplier = 2
    vol_accel_threshold = 0.2
    max_positions = 5  # Maximum concurrent trades
    
    def init(self):
        # 🌪️ Vortex Indicator Calculations
        self.vi_plus, self.vi_minus = self.I(talib.VORTEX, 
            self.data.High, self.data.Low, self.data.Close, 14)
        
        # 📈 Volume Acceleration System
        self.vol_accel = self.I(self._calc_vol_accel, self.data.Volume, 288)
        
        # 🎚️ ATR for Risk Management
        self.atr = self.I(talib.ATR,
            self.data.High, self.data.Low, self.data.Close, 14)
        
        self.trailing_stop = None

    def _calc_vol_accel(self, volume, period):
        """Calculate volume acceleration using pure TA-Lib"""
        ma = talib.SMA(volume, timeperiod=period)
        return (volume - ma) / ma  # Percentage acceleration

    def next(self):
        price = self.data.Close[-1]
        print(f"🌙 Moon Pulse: ${price:.2f} | VI+={self.vi_plus[-1]:.2f} VI-={self.vi_minus[-1]:.2f} | Vol Accel={self.vol_accel[-1]:.2%}")
        
        # Protect against early calculation errors
        if len(self.data) < 288 or not all([self.vi_plus, self.vi_minus, self.atr]):
            return

        # =====================
        # EXIT LOGIC
        # =====================
        if self.position.is_long:
            # Trail stop update
            self.trailing_stop = max(self.trailing_stop, 
                self.data.High[-1] - self.atr[-1] * self.atr_multiplier)
            
            if crossover(self.vi_minus, self.vi_plus):
                print(f"🚨 VI- OVER VI+! Closing LONG at {self.data.Close[-1]:.2f} 🌕")
                self.position.close()
            elif self.data.Low[-1] < self.trailing_stop:
                print(f"🔴 Trail STOP! Closing LONG at {self.trailing_stop:.2f} 🛑")
                self.position.close()
                
        elif self.position.is_short:
            # Trail stop update
            self.trailing_stop = min(self.trailing_stop,
                self.data.Low[-1] + self.atr[-1] * self.atr_multiplier)
            
            if crossover(self.vi_plus, self.vi_minus):
                print(f"🚨 VI+ OVER VI-! Closing SHORT at {self.data.Close[-1]:.2f} 🌑")
                self.position.close()
            elif self.data.High[-1] > self.trailing_stop:
                print(f"🔴 Trail STOP! Closing SHORT at {self.trailing_stop:.2f} 🛑")
                self.position.close()

        # =====================
        # ENTRY LOGIC
        # =====================
        if not self.position and len(self.trades) < self.max_positions:
            risk_amount = self.risk_pct * self.equity
            atr_value = self.atr[-1] or 0.01  # Avoid division by zero
            
            if atr_value <= 0:
                print("⚠️ Critical ATR Error - Market Closed