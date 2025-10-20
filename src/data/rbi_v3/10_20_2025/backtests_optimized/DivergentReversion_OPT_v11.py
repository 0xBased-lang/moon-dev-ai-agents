import pandas as pd
import talib
import numpy as np
from backtesting import Backtest, Strategy

# Load data
data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
df = pd.read_csv(data_path)

# Clean column names
df.columns = df.columns.str.strip().str.lower()

# Drop any unnamed columns
df = df.drop(columns=[col for col in df.columns if 'unnamed' in col.lower()])

# Set datetime as index
df = df.set_index(pd.to_datetime(df['datetime']))

# Rename columns properly
df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)

# Sort index to ensure chronological order
df = df.sort_index()

# Ensure required columns
print("🌙 Moon Dev: Data loaded and cleaned. Shape:", df.shape)
print("Columns:", df.columns.tolist())

class DivergentReversion(Strategy):
    adx_threshold = 20  # 🌙 Moon Dev: Tightened ADX threshold to 20 for stricter ranging market filter to avoid weak signals
    risk_per_trade = 0.015  # 🌙 Moon Dev: Increased to 1.5% risk per trade for more aggressive positioning while maintaining risk control
    atr_multiplier_sl = 2
    atr_multiplier_tp = 6  # 🌙 Moon Dev: Improved RR to 1:3 by increasing TP multiplier to capture larger reversions

    def init(self):
        # RSI(14) - standard period for better responsiveness
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.rsi_sma = self.I(talib.SMA, self.rsi, timeperiod=14)
        
        # Stochastic %K(14,3,3) - switched to standard parameters for more reliable overbought/oversold readings
        self.stoch_k, self.stoch_d = self.I(talib.STOCH, self.data.High, self.data.Low, self.data.Close,
                                            fastk_period=14, slowk_period=3, slowd_period=3)
        self.stoch_sma = self.I(talib.SMA, self.stoch_k, timeperiod=14)
        
        # ATR(14) for dynamic stops
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
        # ADX(14) for trend filter
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
        # Volume SMA for confirmation filter - added to avoid low-volume false signals
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        
        print("🌙 Moon Dev: Indicators initialized with optimizations ✨")

    def next(self):
        # 🌙 Moon Dev: Check for exits first
        if self.position.is_long:
            # Exit long on opposite reversion signal
            if (self.rsi[-1] > self.rsi_sma[-1]) or (self.stoch_k[-1] < self.stoch_sma[-1]):
                self.position.close()
                print(f"🌙 Moon Dev: Long Exit on Reversion Signal at {self.data.Close[-1]:.2f} 🚀")
            return
        
        if self.position.is_short:
            # Exit short on opposite reversion signal
            if (self.rsi[-1] < self.rsi_sma[-1]) or (self.stoch_k[-1] > self.stoch_sma[-1]):
                self.position.close()
                print(f"🌙 Moon Dev: Short Exit on Reversion Signal at {self.data.Close[-1]:.2f} 🚀")
            return
        
        # Common filters for entries
        if (not self.position) and (len(self.rsi) > 14) and (self.adx[-1] < self.adx_threshold) and (self.data.Volume[-1] > self.vol_sma[-1]):
            entry_price = self.data.Close[-1]
            atr_val = self.atr[-1]
            
            # Long entry: RSI oversold but Stoch overbought (divergence for bullish reversion)
            if (self.rsi[-1] < self.rsi_sma[-1]) and (self.stoch_k[-1] > self.stoch_sma[-1]):
                sl_price = entry_price - (self.atr_multiplier_sl * atr_val)
                tp_price = entry_price + (self.atr_multiplier_tp * atr_val)
                risk_distance = entry_price - sl_price
                
                # Position sizing: risk defined % of equity
                equity = self._broker.get_cash() + self._broker.get_value(self.data.Close[-1])  # 🌙 Moon Dev: Use total equity for accurate sizing
                risk_amount = equity * self.risk_per_trade
                position_size = risk_amount / risk_distance  # Keep as float for precision
                
                # Check validity
                if position_size > 0 and not np.isnan(sl_price) and not np.isnan(tp_price) and sl_price < entry_price < tp_price:
                    self.buy(size=position_size, limit=entry_price, sl=sl_price, tp=tp_price)
                    print(f"🌙 Moon Dev: Long Entry at {entry_price:.2f}, Size: {position_size:.4f}, SL: {sl_price:.2f}, TP: {tp_price:.2f} ✨")
                else:
                    print("🌙 Moon Dev: Invalid long position size or SL/TP levels, skipping entry ⚠️")
            
            # Short entry: RSI overbought but Stoch oversold (divergence for bearish reversion)
            elif (self.rsi[-1] > self.rsi_sma[-1]) and (self.stoch_k[-1] < self.stoch_sma[-1]):
                sl_price = entry_price + (self.atr_multiplier_sl * atr_val)
                tp_price = entry_price - (self.atr_multiplier_tp * atr_val)
                risk_distance = sl_price - entry_price
                
                # Position sizing: risk defined % of equity
                equity = self._broker.get_cash() + self._broker.get_value(self.data.Close[-1])  # 🌙 Moon Dev: Use total equity for accurate sizing
                risk_amount = equity * self.risk_per_trade
                position_size = risk_amount / risk_distance  # Keep as float for precision
                
                # Check validity
                if position_size > 0 and not np.isnan(sl_price) and not np.isnan(tp_price) and tp_price < entry_price < sl_price:
                    self.sell(size=position_size, limit=entry_price, sl=sl_price, tp=tp_price)
                    print(f"🌙 Moon Dev: Short Entry at {entry_price:.2f}, Size: {position_size:.4f}, SL: {sl_price:.2f}, TP: {tp_price:.2f} ✨")
                else:
                    print("🌙 Moon Dev: Invalid short position size or SL/TP levels, skipping entry ⚠️")

# Run backtest
bt = Backtest(df, DivergentReversion, cash=1000000, commission=0.002, exclusive_orders=True, trade_on_close=True)

print("🌙 Moon Dev: Running optimized backtest... 🚀")
stats = bt.run()
print(stats)