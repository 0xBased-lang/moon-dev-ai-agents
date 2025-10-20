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
    adx_threshold = 20  # 🌙 Moon Dev: Tightened ADX threshold from 25 to 20 for stricter ranging market filter to avoid weak trends
    risk_per_trade = 0.01  # 1% risk maintained for good risk management
    atr_multiplier_sl = 2
    atr_multiplier_tp = 6  # 🌙 Moon Dev: Increased TP multiplier from 4 to 6 for 1:3 RR to capture larger moves and boost returns

    def init(self):
        # RSI(20) - kept period as is, standard for mean reversion
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=20)
        self.rsi_sma = self.I(talib.SMA, self.rsi, timeperiod=20)
        
        # Stochastic %K(8) - kept fast settings for quick signals
        self.stoch_k, _ = self.I(talib.STOCH, self.data.High, self.data.Low, self.data.Close,
                                  fastk_period=8, slowk_period=1, slowd_period=1)
        self.stoch_sma = self.I(talib.SMA, self.stoch_k, timeperiod=20)  # 🌙 Moon Dev: Could tune to 10 for faster, but kept 20 for stability
        
        # ATR(14) for dynamic stops - unchanged
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
        # ADX(14) for trend filter - unchanged period
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
        # 🌙 Moon Dev: Added volume SMA filter to confirm entries on higher volume for better quality signals
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        
        print("🌙 Moon Dev: Indicators initialized with volume filter ✨")

    def next(self):
        # 🌙 Moon Dev: Enhanced exit logic for both long and short positions
        if self.position.is_long:
            # Long exit on reversion: RSI crosses above SMA or Stoch crosses below SMA
            if (self.rsi[-1] > self.rsi_sma[-1]) or (self.stoch_k[-1] < self.stoch_sma[-1]):
                self.position.close()
                print(f"🌙 Moon Dev: Long Exit on Reversion Signal at {self.data.Close[-1]:.2f} 🚀")
            return
        
        if self.position.is_short:
            # Short exit on reversion: RSI crosses below SMA or Stoch crosses above SMA
            if (self.rsi[-1] < self.rsi_sma[-1]) or (self.stoch_k[-1] > self.stoch_sma[-1]):
                self.position.close()
                print(f"🌙 Moon Dev: Short Exit on Reversion Signal at {self.data.Close[-1]:.2f} 🚀")
            return
        
        # 🌙 Moon Dev: Added symmetric long entries to capture upside reversion in ranging markets, doubling opportunities
        # Entry conditions only if no position and sufficient history
        if (not self.position) and (len(self.rsi) > 20) and (self.adx[-1] < self.adx_threshold):
            
            # Volume filter for all entries
            vol_confirm = self.data.Volume[-1] > self.vol_sma[-1]
            
            # Long entry: RSI oversold (below SMA), Stoch overbought (above SMA) - divergence for upside reversion
            if vol_confirm and (self.rsi[-1] < self.rsi_sma[-1]) and (self.stoch_k[-1] > self.stoch_sma[-1]):
                entry_price = self.data.Close[-1]
                atr_val = self.atr[-1]
                sl_price = entry_price - (self.atr_multiplier_sl * atr_val)
                tp_price = entry_price + (self.atr_multiplier_tp * atr_val)
                risk_distance = entry_price - sl_price
                
                equity = self.equity
                risk_amount = equity * self.risk_per_trade
                position_size = risk_amount / risk_distance
                position_size = max(0.001, min(1.0, position_size))  # 🌙 Moon Dev: Allow fractional sizes (0-1 normalized? but adjusted to realistic min/max for BTC units)
                
                if position_size > 0 and not np.isnan(sl_price) and not np.isnan(tp_price) and sl_price < entry_price < tp_price:
                    self.buy(size=position_size, limit=entry_price, sl=sl_price, tp=tp_price)
                    print(f"🌙 Moon Dev: Long Entry at {entry_price:.2f}, Size: {position_size:.4f}, SL: {sl_price:.2f}, TP: {tp_price:.2f} ✨")
                else:
                    print("🌙 Moon Dev: Invalid long position size or SL/TP levels, skipping entry ⚠️")
                return
            
            # Short entry: RSI overbought (above SMA), Stoch oversold (below SMA) - divergence for downside reversion
            if vol_confirm and (self.rsi[-1] > self.rsi_sma[-1]) and (self.stoch_k[-1] < self.stoch_sma[-1]):
                entry_price = self.data.Close[-1]
                atr_val = self.atr[-1]
                sl_price = entry_price + (self.atr_multiplier_sl * atr_val)
                tp_price = entry_price - (self.atr_multiplier_tp * atr_val)
                risk_distance = sl_price - entry_price
                
                equity = self.equity
                risk_amount = equity * self.risk_per_trade
                position_size = risk_amount / risk_distance
                position_size = max(0.001, min(1.0, position_size))  # 🌙 Moon Dev: Allow fractional sizes for better precision in crypto trading
                
                if position_size > 0 and not np.isnan(sl_price) and not np.isnan(tp_price) and tp_price < entry_price < sl_price:
                    self.sell(size=position_size, limit=entry_price, sl=sl_price, tp=tp_price)
                    print(f"🌙 Moon Dev: Short Entry at {entry_price:.2f}, Size: {position_size:.4f}, SL: {sl_price:.2f}, TP: {tp_price:.2f} ✨")
                else:
                    print("🌙 Moon Dev: Invalid short position size or SL/TP levels, skipping entry ⚠️")

# Run backtest
bt = Backtest(df, DivergentReversion, cash=1000000, commission=0.002, exclusive_orders=True, trade_on_close=True)

print("🌙 Moon Dev: Running backtest... 🚀")
stats = bt.run()
print(stats)