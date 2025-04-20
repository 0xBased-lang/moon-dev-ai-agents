Here's the debugged backtest code with Moon Dev themed improvements while maintaining the original strategy logic:

```python
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import backtesting as bt  # For Order type reference

class VolatilitySurge(Strategy):
    risk_percent = 0.01  # 1% risk per trade
    atr_period = 14
    atr_sma_period = 20
    bb_period = 20
    swing_period = 20

    def init(self):
        # Calculate indicators with proper TA-Lib integration
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.atr_sma = self.I(talib.SMA, self.atr, self.atr_sma_period)
        
        # Bollinger Bands using lambda wrappers to extract bands
        self.bb_upper = self.I(lambda x: talib.BBANDS(x, self.bb_period, 2, 2)[0], self.data.Close)
        self.bb_lower = self.I(lambda x: talib.BBANDS(x, self.bb_period, 2, 2)[2], self.data.Close)
        
        # Swing low calculation
        self.swing_low = self.I(talib.MIN, self.data.Low, self.swing_period)

    def next(self):
        # Moon Dev Safety Checks 🌙
        if len(self.data) < max(self.atr_period, self.bb_period, self.swing_period) + 1:
            return

        # Current index calculations
        current_bar = len(self.data) - 1
        prev_bar = current_bar - 1
        
        if current_bar < 1 or current_bar + 1 >= len(self.data):
            return

        # Moon Dev Signal Detection 🌙✨
        atr_cross = (self.atr[prev_bar] < self.atr_sma[prev_bar]) and (self.atr[current_bar] > self.atr_sma[current_bar])
        close_above_bb = self.data.Close[current_bar] > self.bb_upper[current_bar]
        
        if not self.position and atr_cross and close_above_bb:
            # Moon Dev Risk Management 🌙💰
            stop_loss = min(self.swing_low[current_bar], self.bb_lower[current_bar])
            entry_price = self.data.Open[current_bar + 1]
            risk_per_share = entry_price - stop_loss
            
            if risk_per_share <= 0:
                print(f"🌙⚠️ MOON DEV WARNING: Invalid risk calculation (Risk: {risk_per_share:.2f})")
                return  # Invalid risk calculation
            
            # Position sizing calculation with proper rounding
            risk_amount = self.equity * self.risk_percent
            position_size = int(round(risk_amount / risk_per_share))
            
            if position_size > 0:
                # Moon Dev Entry Print 🌙🚀
                tp_price = entry_price + 2 * risk_per_share
                print(f"🌙🚀 MOON DEV LONG ENTRY! 🌙 | Price: {entry_price:.2f} | Size: {position_size}")
                print(f"   🛡️ SL: {stop_loss:.2f} | 🎯 TP: {tp_price:.2f} | Risk/Reward: 1:2")
                
                self.buy(size=position_size, 
                        sl=stop_loss,
                        tp=tp_price,
                        exectype=bt.Order.Order.Open)

# Moon Dev Data Preparation 🌙📊
try:
    data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
    
    # Clean and format columns
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col], errors='ignore')
    data = data.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })

    # Convert index to datetime
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    
    # Verify required columns exist
    required_cols = ['Open', 'High', 'Low', 'Close']
    if not all(col in data.columns for col in required_cols):
        raise ValueError("🌙❌ MOON DEV ERROR: Missing required price columns in data