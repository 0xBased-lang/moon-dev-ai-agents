import pandas as pd
import talib
import numpy as np
from backtesting import Backtest, Strategy

# Data loading and cleaning
path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'date': 'datetime',
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})
data = data.set_index(pd.to_datetime(data['datetime'])).drop(columns=['datetime'])
print("🌙 Moon Dev: Data loaded and cleaned successfully! Columns: Open, High, Low, Close, Volume. Index: Datetime. ✨")

class DivergentConvergence(Strategy):
    pivot_window = 5  # Not used, using approximation
    lookback = 20  # 🌙 Moon Dev Optimization: Increased lookback to 20 for detecting stronger, more distant lows to improve divergence quality and capture bigger moves
    recent_period = 10  # 🌙 Moon Dev Optimization: Extended recent period to 10 for better recent low detection while filtering out excessive noise
    stoch_window = 14  # 🌙 Moon Dev Optimization: Adjusted stochastic window to 14 for alignment with standard settings and smoother, more reliable convergence signals
    risk_pct = 0.02  # 🌙 Moon Dev Optimization: Increased risk per trade to 2% to allow larger positions and higher potential returns with controlled exposure
    rr = 3.0  # 🌙 Moon Dev Optimization: Boosted RR to 3:1 to capture more of BTC's trending moves while balancing risk-reward
    max_bars = 50  # 🌙 Moon Dev Optimization: Doubled max hold time to 50 bars (about 12.5 hours on 15m) to give winners more room in volatile crypto trends
    atr_mult_sl = 1.5  # 🌙 Moon Dev Optimization: Tightened ATR multiplier for trailing stop to 1.5 to lock in profits faster without stopping out too early
    buffer_mult = 1.0  # 🌙 Moon Dev Optimization: Adjusted buffer to full ATR for more conservative initial SL placement to better handle BTC wicks

    def init(self):
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.slowk = self.I(lambda h, l, c: talib.STOCH(h, l, c, fastk_period=14, slowk_period=3, slowd_period=3)[0], self.data.High, self.data.Low, self.data.Close)
        self.slowd = self.I(lambda h, l, c: talib.STOCH(h, l, c, fastk_period=14, slowk_period=3, slowd_period=3)[1], self.data.High, self.data.Low, self.data.Close)
        self.sma200 = self.I(talib.SMA, self.data.Close, timeperiod=200)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Added volume SMA filter to enter only on above-average volume for higher conviction setups
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        # 🌙 Moon Dev Optimization: Added ADX for trend strength filter to avoid choppy markets and focus on trending conditions
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Added MACD for momentum confirmation to ensure upward momentum before entry, filtering out weak signals
        self.macd, self.macdsignal, _ = self.I(talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
        self.entry_bar = None
        self.entry_price = None
        self.sl_price = None
        self.tp_price = None
        self.div_low = None
        self.div_bar = None
        self.current_sl = None  # 🌙 Moon Dev Optimization: Track current trailing SL level
        print("🌙 Moon Dev Backtest Initialized! ✨ Initializing indicators... 🚀")

    def next(self):
        if len(self.data) < 220:  # Enough for SMA200 + lookback
            return

        current_price = self.data.Close[-1]
        current_bar = len(self.data) - 1

        # Check if divergence signal still valid
        if self.div_bar is not None and (current_bar - self.div_bar > self.max_bars):
            self.div_bar = None
            self.div_low = None
            print("🌙 Moon Dev: Divergence signal timed out after max_bars. 🔚")

        # RSI Divergence Detection (approximation)
        lows_older = self.data.Low[-self.lookback : -self.recent_period]
        rsi_older = self.rsi[-self.lookback : -self.recent_period]
        argmin_low_older = np.argmin(lows_older)
        low1 = lows_older[argmin_low_older]
        rsi1 = rsi_older[argmin_low_older]
        lows_recent_part = self.data.Low[-self.recent_period:]
        rsi_recent_part = self.rsi[-self.recent_period:]
        argmin_low_recent = np.argmin(lows_recent_part)
        low2 = lows_recent_part[argmin_low_recent]
        rsi2 = rsi_recent_part[argmin_low_recent]
        distance = self.recent_period - 1 - argmin_low_recent

        bull_div = (low2 < low1) and (rsi2 > rsi1) and (rsi2 < 40) and (distance <= 5)  # 🌙 Moon Dev Optimization: Tightened RSI threshold to <40 for stronger oversold divergences and increased distance tolerance to <=5 for more flexible signal timing
        if bull_div:
            self.div_low = low2
            self.div_bar = current_bar
            print(f"🌙 Moon Dev: Bullish RSI Divergence detected! Price low: {low2}, RSI: {rsi2} ✨ Distance: {distance} bars")

        # Stochastic Convergence
        k_now = self.slowk[-1]
        d_now = self.slowd[-1]
        k_prev = self.slowk[-self.stoch_window]
        d_prev = self.slowd[-self.stoch_window]
        gap_now = abs(d_now - k_now)
        gap_prev = abs(d_prev - k_prev)
        stoch_converge = (k_now < 20) and (k_now > k_prev) and (gap_now < gap_prev) and (k_now < d_now)  # 🌙 Moon Dev Optimization: Lowered %K threshold to <20 to capture more oversold convergence opportunities in BTC's volatile swings
        if stoch_converge:
            print(f"🚀 Moon Dev: Stochastic Convergence! %K: {k_now}, %D: {d_now}, Gap narrowed! 🌙")

        # Entry Logic
        if not self.position and self.div_bar is not None and stoch_converge and current_price > self.sma200[-1] and self.data.Volume[-1] > self.vol_sma[-1] and self.adx[-1] > 18 and self.macd[-1] > self.macd[-2] and self.data.Close[-1] > self.data.Open[-1]:  # 🌙 Moon Dev Optimization: Lowered ADX to >18 for more trending opportunities, added MACD momentum and bullish candle confirmation for higher-quality, lower-false-positive entries
            print(f"🌙 Moon Dev: All entry conditions met! Attempting LONG entry... 🚀")
            # Calculate SL: below div low with buffer
            div_low = self.div_low
            atr_val = self.atr[-1]
            sl_price = div_low - (atr_val * self.buffer_mult)
            entry_price = current_price
            risk_per_unit = entry_price - sl_price
            if risk_per_unit <= 0:
                print(f"🌙 Moon Dev: Invalid risk per unit: {risk_per_unit}, skipping entry. ⚠️")
                return
            size_frac = self.risk_pct * entry_price / risk_per_unit
            size = min(1.0, size_frac)
            if size > 0:
                tp_price = entry_price + self.rr * risk_per_unit
                self.buy(size=size, tp=tp_price)  # 🌙 Moon Dev Optimization: Removed fixed SL from order to enable manual trailing management
                self.entry_price = entry_price
                self.sl_price = sl_price
                self.tp_price = tp_price
                self.entry_bar = current_bar
                self.current_sl = sl_price  # 🌙 Moon Dev Optimization: Initialize trailing SL at entry SL level
                self.div_bar = None
                self.div_low = None
                print(f"🌙 Moon Dev: LONG ENTRY! Size: {size} (fraction), Entry: {entry_price}, Initial SL: {sl_price}, TP: {tp_price} 🚀✨")
            else:
                print(f"🌙 Moon Dev: Calculated size {size} <=0, skipping entry. ⚠️")

        # Exit Logic
        if self.position:
            bars_held = current_bar - self.entry_bar if self.entry_bar is not None else 0
            rsi_now = self.rsi[-1]
            k_cross_below_d = (self.slowk[-2] >= self.slowd[-2]) and (self.slowk[-1] < self.slowd[-1])

            # 🌙 Moon Dev Optimization: Update trailing SL dynamically every bar to lock in profits as price rises
            if self.current_sl is None:
                self.current_sl = self.sl_price
            new_trail_sl = current_price - (self.atr[-1] * self.atr_mult_sl)
            self.current_sl = max(self.current_sl, new_trail_sl)

            # Time-based exit
            if bars_held > self.max_bars:
                self.position.close()
                print(f"🌙 Moon Dev: Time-based EXIT after {bars_held} bars! 😴")
                self.current_sl = None
                return

            # Stochastic cross exit
            if k_cross_below_d:
                self.position.close()
                print(f"🌙 Moon Dev: Stochastic %K crossed below %D! EXIT 📉")
                self.current_sl = None
                return

            # RSI overbought exit
            if rsi_now > 80:  # 🌙 Moon Dev Optimization: Raised RSI exit threshold to >80 to allow more room for overbought conditions in strong trends, letting winners run longer
                self.position.close()
                print(f"🌙 Moon Dev: RSI Overbought >80! EXIT 📈")
                self.current_sl = None
                return

            # Trailing SL check - improved to use Low for more accurate wick detection
            if self.data.Low[-1] <= self.current_sl:
                self.position.close()
                print(f"🌙 Moon Dev: Trailing SL hit at Low {self.data.Low[-1]}! 📉")
                self.current_sl = None
                return

            print(f"🌙 Moon Dev: Position held. Bars: {bars_held}, Price: {current_price}, RSI: {rsi_now}, %K: {self.slowk[-1]}, Trail SL: {self.current_sl} ✨")

# Run backtest
bt = Backtest(data, DivergentConvergence, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)