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
    lookback = 25  # Increased lookback for better divergence detection in volatile markets 🌙
    recent_period = 12  # Slightly increased recent period to capture more relevant lows
    stoch_window = 5
    risk_pct = 0.02  # Increased risk per trade to 2% for higher exposure while managing drawdown ✨
    rr = 3  # Increased reward ratio to 3:1 to capture more upside in BTC trends 🚀
    max_bars = 30  # Extended max hold time to allow trends to develop further
    atr_mult_sl = 2.0  # Increased ATR multiple for trailing stop to give more room
    buffer_mult = 0.75  # Adjusted buffer for SL to balance tightness and avoiding whipsaws

    def init(self):
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.slowk = self.I(lambda h, l, c: talib.STOCH(h, l, c, fastk_period=14, slowk_period=3, slowd_period=3)[0], self.data.High, self.data.Low, self.data.Close)
        self.slowd = self.I(lambda h, l, c: talib.STOCH(h, l, c, fastk_period=14, slowk_period=3, slowd_period=3)[1], self.data.High, self.data.Low, self.data.Close)
        self.sma200 = self.I(talib.SMA, self.data.Close, timeperiod=200)
        self.sma50 = self.I(talib.SMA, self.data.Close, timeperiod=50)  # Added shorter SMA for additional trend confirmation 🌙
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)  # Added volume SMA for momentum filter ✨
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)  # Added ADX for trend strength filter 🚀
        self.entry_bar = None
        self.entry_price = None
        self.sl_price = None
        self.tp_price = None
        self.div_low = None
        self.div_bar = None
        self.trailing_active = False  # Flag for trailing stop activation
        print("🌙 Moon Dev Backtest Initialized! ✨ Initializing indicators... 🚀")

    def next(self):
        if len(self.data) < 220:  # Enough for SMA200 + lookback
            return

        current_price = self.data.Close[-1]
        current_bar = len(self.data) - 1
        current_vol = self.data.Volume[-1]

        # Check if divergence signal still valid
        if self.div_bar is not None and (current_bar - self.div_bar > self.max_bars):
            self.div_bar = None
            self.div_low = None
            print("🌙 Moon Dev: Divergence signal timed out after max_bars. 🔚")

        # RSI Divergence Detection (approximation) - Fine-tuned periods for better signal quality
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

        bull_div = (low2 < low1) and (rsi2 > rsi1) and (rsi2 < 50) and (distance <= 7)  # Slightly relaxed distance for more opportunities but still recent ✨
        if bull_div:
            self.div_low = low2
            self.div_bar = current_bar
            print(f"🌙 Moon Dev: Bullish RSI Divergence detected! Price low: {low2}, RSI: {rsi2} ✨ Distance: {distance} bars")

        # Stochastic Convergence - Added oversold condition on D for stronger signal
        k_now = self.slowk[-1]
        d_now = self.slowd[-1]
        k_prev = self.slowk[-self.stoch_window]
        d_prev = self.slowd[-self.stoch_window]
        gap_now = abs(d_now - k_now)
        gap_prev = abs(d_prev - k_prev)
        stoch_converge = (k_now < 20) and (k_now > k_prev) and (gap_now < gap_prev) and (k_now < d_now) and (d_now < 30)  # Added D oversold filter 🚀
        if stoch_converge:
            print(f"🚀 Moon Dev: Stochastic Convergence! %K: {k_now}, %D: {d_now}, Gap narrowed! 🌙")

        # Entry Logic - Added volume, ADX, and SMA50 filters for higher quality setups
        if not self.position and self.div_bar is not None and stoch_converge and current_price > self.sma200[-1] and current_price > self.sma50[-1] and current_vol > self.vol_sma[-1] and self.adx[-1] > 20:
            print(f"🌙 Moon Dev: All entry conditions met! Attempting LONG entry... 🚀")
            # Calculate SL: below div low with adjusted buffer, fallback to ATR-based if invalid
            div_low = self.div_low
            atr_val = self.atr[-1]
            sl_price = div_low - (atr_val * self.buffer_mult)
            entry_price = current_price
            risk_per_unit = entry_price - sl_price
            if risk_per_unit <= 0:
                sl_price = entry_price - (atr_val * self.atr_mult_sl)  # Fallback to pure ATR SL for validity
                risk_per_unit = entry_price - sl_price
            if risk_per_unit <= 0:
                print(f"🌙 Moon Dev: Invalid risk per unit: {risk_per_unit}, skipping entry. ⚠️")
                return
            size_frac = self.risk_pct * entry_price / risk_per_unit
            size = min(1.0, size_frac)
            if size > 0:
                tp_price = entry_price + self.rr * risk_per_unit
                self.buy(size=size, sl=sl_price, tp=tp_price)
                self.entry_price = entry_price
                self.sl_price = sl_price
                self.tp_price = tp_price
                self.entry_bar = current_bar
                self.div_bar = None
                self.div_low = None
                self.trailing_active = False
                print(f"🌙 Moon Dev: LONG ENTRY! Size: {size} (fraction), Entry: {entry_price}, SL: {sl_price}, TP: {tp_price} 🚀✨")
            else:
                print(f"🌙 Moon Dev: Calculated size {size} <=0, skipping entry. ⚠️")

        # Exit Logic & Trailing Stop
        if self.position:
            bars_held = current_bar - self.entry_bar if self.entry_bar is not None else 0
            rsi_now = self.rsi[-1]
            k_cross_below_d = (self.slowk[-2] >= self.slowd[-2]) and (self.slowk[-1] < self.slowd[-1])

            # Time-based exit
            if bars_held > self.max_bars:
                self.position.close()
                print(f"🌙 Moon Dev: Time-based EXIT after {bars_held} bars! 😴")
                return

            # Dynamic exits
            if k_cross_below_d:
                self.position.close()
                print(f"🌙 Moon Dev: Stochastic %K crossed below %D! EXIT 📉")
                return
            if rsi_now > 70:
                self.position.close()
                print(f"🌙 Moon Dev: RSI Overbought >70! EXIT 📈")
                return
            # Additional trend break exit
            if current_price < self.sma50[-1]:
                self.position.close()
                print(f"🌙 Moon Dev: Price below SMA50! Trend break EXIT 📉")
                return

            # Trailing Stop Implementation - Activates after 1 ATR profit, trails at 2 ATR below current
            unrealized_pnl = current_price - self.entry_price
            if unrealized_pnl > self.atr[-1]:
                if not self.trailing_active:
                    self.trailing_active = True
                    print("🌙 Moon Dev: Trailing stop activated! 🚀")
                trail_sl = current_price - (self.atr[-1] * self.atr_mult_sl)
                if trail_sl > self.sl_price:
                    self.position.sl = trail_sl
                    self.sl_price = trail_sl
                    print(f"🌙 Moon Dev: Trailing SL updated to {trail_sl} ✨")

            print(f"🌙 Moon Dev: Position held. Bars: {bars_held}, Price: {current_price}, RSI: {rsi_now}, %K: {self.slowk[-1]} ✨")

# Run backtest
bt = Backtest(data, DivergentConvergence, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)