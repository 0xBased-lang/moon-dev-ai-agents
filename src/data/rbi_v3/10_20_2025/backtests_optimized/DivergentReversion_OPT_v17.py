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
    adx_threshold = 20  # 🌙 Tightened ADX threshold to 20 for stronger ranging market filter, reducing false signals in weak trends
    risk_per_trade = 0.015  # 🌙 Increased to 1.5% risk per trade to amplify returns while still managing risk, aiming for higher equity growth
    atr_multiplier_sl = 2
    atr_multiplier_tp = 5  # 🌙 Extended TP to 5x ATR for improved 1:2.5 RR, capturing larger reversions in volatile BTC 15m setups

    def init(self):
        # RSI(14) - 🌙 Changed to standard 14 period for more responsive mean reversion signals
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.rsi_sma = self.I(talib.SMA, self.rsi, timeperiod=20)
        
        # Stochastic %K(14,3,3) - 🌙 Switched to standard Stochastic parameters for better oversold/overbought detection without excessive noise
        self.stoch_k, _ = self.I(talib.STOCH, self.data.High, self.data.Low, self.data.Close,
                                  fastk_period=14, slowk_period=3, slowd_period=3)
        self.stoch_sma = self.I(talib.SMA, self.stoch_k, timeperiod=20)
        
        # ATR(14) for dynamic stops
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
        # ADX(14) for trend filter
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
        # Volume SMA(20) - 🌙 Added volume filter to ensure entries only on above-average volume, improving signal quality and avoiding low-conviction setups
        self.volume_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        
        print("🌙 Moon Dev: Indicators initialized with optimizations ✨")

    def next(self):
        # 🌙 Handle exits first for both long and short positions using symmetric reversion signals
        if self.position:
            if self.position.is_long:
                if (self.rsi[-1] > self.rsi_sma[-1]) or (self.stoch_k[-1] < self.stoch_sma[-1]):
                    self.position.close()
                    print(f"🌙 Moon Dev: Long Exit on Reversion Signal at {self.data.Close[-1]:.2f} 🚀")
            elif self.position.is_short:
                if (self.rsi[-1] < self.rsi_sma[-1]) or (self.stoch_k[-1] > self.stoch_sma[-1]):
                    self.position.close()
                    print(f"🌙 Moon Dev: Short Exit on Reversion Signal at {self.data.Close[-1]:.2f} 🚀")
            return  # Early return after handling exit to avoid new entries while in position
        
        # 🌙 Entry logic only if no position and sufficient data - increased to 30 bars for all indicators to stabilize
        if (not self.position) and (len(self.rsi) > 30):
            # 🌙 Common filters: low ADX for ranging markets and volume confirmation for higher-quality setups
            if (self.adx[-1] < self.adx_threshold) and (self.data.Volume[-1] > self.volume_sma[-1]):
                
                entry_price = self.data.Close[-1]
                atr_val = self.atr[-1]
                
                # Long entry on bullish divergence: RSI bearish but Stoch bullish
                if (self.rsi[-1] < self.rsi_sma[-1]) and (self.stoch_k[-1] > self.stoch_sma[-1]):
                    sl_price = entry_price - (self.atr_multiplier_sl * atr_val)
                    tp_price = entry_price + (self.atr_multiplier_tp * atr_val)
                    risk_distance = entry_price - sl_price
                    
                    equity = self.equity
                    risk_amount = equity * self.risk_per_trade
                    position_size = risk_amount / risk_distance
                    position_size = max(0.01, min(1000, position_size))  # 🌙 Added bounds to position size for realism and to prevent extreme allocations
                    
                    if position_size > 0 and not np.isnan(sl_price) and not np.isnan(tp_price) and sl_price < entry_price < tp_price:
                        self.buy(size=position_size, limit=entry_price, sl=sl_price, tp=tp_price)
                        print(f"🌙 Moon Dev: Long Entry at {entry_price:.2f}, Size: {position_size}, SL: {sl_price:.2f}, TP: {tp_price:.2f} ✨")
                    else:
                        print("🌙 Moon Dev: Invalid long position size or SL/TP levels, skipping entry ⚠️")
                
                # Short entry on bearish divergence: RSI bullish but Stoch bearish (using elif to avoid conflicting signals on same bar)
                elif (self.rsi[-1] > self.rsi_sma[-1]) and (self.stoch_k[-1] < self.stoch_sma[-1]):
                    sl_price = entry_price + (self.atr_multiplier_sl * atr_val)
                    tp_price = entry_price - (self.atr_multiplier_tp * atr_val)
                    risk_distance = sl_price - entry_price
                    
                    equity = self.equity
                    risk_amount = equity * self.risk_per_trade
                    position_size = risk_amount / risk_distance
                    position_size = max(0.01, min(1000, position_size))  # 🌙 Added bounds to position size for realism and to prevent extreme allocations
                    
                    if position_size > 0 and not np.isnan(sl_price) and not np.isnan(tp_price) and tp_price < entry_price < sl_price:
                        self.sell(size=position_size, limit=entry_price, sl=sl_price, tp=tp_price)
                        print(f"🌙 Moon Dev: Short Entry at {entry_price:.2f}, Size: {position_size}, SL: {sl_price:.2f}, TP: {tp_price:.2f} ✨")
                    else:
                        print("🌙 Moon Dev: Invalid short position size or SL/TP levels, skipping entry ⚠️")

# Run backtest
bt = Backtest(df, DivergentReversion, cash=1000000, commission=0.002, exclusive_orders=True, trade_on_close=True)

print("🌙 Moon Dev: Running backtest... 🚀")
stats = bt.run()
print(stats)