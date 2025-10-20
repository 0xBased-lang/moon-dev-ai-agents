```python
import pandas as pd
import talib
import numpy as np
from backtesting import Backtest, Strategy
from collections import deque

# Data loading and cleaning
data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(data_path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})
data = data.set_index(pd.to_datetime(data['datetime']))
data = data[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

class AdaptiveDivergence(Strategy):
    pivot_length = 5  # 🌙 Increased to 5 for cleaner, less noisy swing detections, reducing false divergence signals and improving entry quality
    rsi_div_thresh = 2  # 🌙 Lowered to 2 for more divergence opportunities while maintaining signal strength, allowing higher trade frequency toward 50% target
    mom_long_thresh = 45  # 🌙 Slightly lowered to 45 to capture more bullish setups without sacrificing too much quality, boosting entry count
    mom_short_thresh = 55  # 🌙 Adjusted to 55 for bearish entries, creating asymmetry to favor longs in crypto's bullish bias for better returns
    risk_per_trade = 0.025  # 🌙 Increased to 2.5% risk per trade for moderately aggressive sizing, accelerating equity growth while controlling drawdowns
    sl_mult = 1.2  # 🌙 Widened slightly to 1.2x ATR to give trades more breathing room, reducing premature stops in volatile BTC swings
    tp_mult = 5.0  # 🌙 Increased to 5x ATR for improved 1:4+ R:R ratio (with SL adjustment), aiming to capture larger profits to hit 50% target
    trail_mult = 2.0  # 🌙 Loosened to 2x ATR for trailing, allowing more trend extension before locking profits, enhancing win sizes
    profit_trail = 1.5  # 🌙 Lowered activation to 1.5x ATR to start trailing earlier, protecting gains sooner in choppy conditions
    max_bars = 100  # 🌙 Extended to 100 bars for longer holds in sustained trends, giving positions ample time to achieve higher TP levels
    atr_avg_period = 20  # 🌙 Increased to 20 for smoother ATR average, better reflecting recent volatility regimes in 15m BTC data

    def init(self):
        self.bar_count = -1
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, self.data.Close, timeperiod=20, nbdevup=2, nbdevdn=2
        )
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.atr_avg = self.I(talib.SMA, self.atr, timeperiod=self.atr_avg_period)
        self.ema = self.I(talib.EMA, self.data.Close, timeperiod=21)  # 🌙 Kept 21-period EMA for short-term trend filter
        self.ema_long = self.I(talib.EMA, self.data.Close, timeperiod=50)  # 🌙 Added 50-period EMA as longer-term trend filter to avoid counter-trend trades, enhancing win rate
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)  # 🌙 Kept ADX for trend strength
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)  # 🌙 Kept volume SMA

        self.confirmed_swing_lows = deque(maxlen=3)  # 🌙 Kept at 3 for recent swings
        self.confirmed_swing_highs = deque(maxlen=3)
        self.last_checked = -1

        self.entry_price = None
        self.entry_atr = None
        self.is_long = None
        self.entry_bar = None
        self.trail_active = False
        self.trail_stop = None
        self.highest_since_entry = None
        self.lowest_since_entry = None
        self.current_mom = None
        self.prev_mom = None

        print(f"🌙 AdaptiveDivergence initialized! 🚀 Initial cash: {self._broker._cash:,} ✨")

    def next(self):
        self.bar_count += 1
        current_bar = self.bar_count
        if current_bar < 50:  # 🌙 Increased wait to 50 to ensure longer EMA initialization, avoiding early unreliable signals
            return

        # Compute current and prev momentum score
        current_close = self.data.Close[-1]
        current_bb_upper = self.bb_upper[-1]
        current_bb_lower = self.bb_lower[-1]
        if np.isnan(current_bb_upper) or np.isnan(current_bb_lower) or current_bb_upper == current_bb_lower:
            current_pct_b = 0.5
        else:
            current_pct_b = (current_close - current_bb_lower) / (current_bb_upper - current_bb_lower)
        self.current_mom = self.rsi[-1] * current_pct_b

        if current_bar > 0:
            prev_close = self.data.Close[-2]
            prev_bb_upper = self.bb_upper[-2]
            prev_bb_lower = self.bb_lower[-2]
            if np.isnan(prev_bb_upper) or np.isnan(prev_bb_lower) or prev_bb_upper == prev_bb_lower:
                prev_pct_b = 0.5
            else:
                prev_pct_b = (prev_close - prev_bb_lower) / (prev_bb_upper - prev_bb_lower)
            self.prev_mom = self.rsi[-2] * prev_pct_b
        else:
            return

        mom_rising = self.current_mom > self.prev_mom
        mom_falling = self.current_mom < self.prev_mom

        # Update confirmed swings
        self.update_swings()

        # Check exits if in position
        if self.position.size != 0:
            bars_in_trade = current_bar - self.entry_bar
            if bars_in_trade > self.max_bars:
                self.position.close()
                print(f"🌙 Time-based exit after {bars_in_trade} bars! 💤")
                self.reset_trade_vars()
                return

            entry_atr = self.entry_atr
            if self.is_long:
                profit = self.data.Close[-1] - self.entry_price
                sl_price = self.entry_price - self.sl_mult * entry_atr
                tp_price = self.entry_price + self.tp_mult * entry_atr

                # Initial SL/TP check
                if self.data.Low[-1] <= sl_price:
                    self.position.close()
                    print(f"🌙 Stop loss hit long at {self.data.Low[-1]}! 💥 Entry: {self.entry_price}")
                    self.reset_trade_vars()
                    return
                if self.data.High[-1] >= tp_price:
                    self.position.close()
                    print(f"🌙 Take profit hit long at {self.data.High[-1]}! 🎉 Entry: {self.entry_price}")
                    self.reset_trade_vars()
                    return

                # Reversal check - 🌙 Tightened mom threshold to <30 for faster long exits, and added EMA cross for better reversal detection
                if self.detect_bearish_div() or self.current_mom < 30 or self.data.Close[-1] < self.ema[-1]:
                    self.position.close()
                    print(f"🌙 Reversal signal exit long! Mom: {self.current_mom:.2f} 🚨")
                    self.reset_trade_vars()
                    return

                # Trailing logic
                if profit > self.profit_trail * self.atr[-1]:
                    if not self.trail_active:
                        self.trail_active = True
                        self.highest_since_entry = self.data.High[-1]
                        self.trail_stop = self.highest_since_entry - self.trail_mult * self.atr[-1]
                        print(f"🌙 Trailing activated for long! Trail stop: {self.trail_stop:.2f} ✨")
                    else:
                        self.highest_since_entry = max(self.highest_since_entry, self.data.High[-1])
                        new_trail = self.highest_since_entry - self.trail_mult * self.atr[-1]
                        self.trail_stop = max(self.trail_stop, new_trail)

                    if self.data.Low[-1] < self.trail_stop:
                        self.position.close()
                        print(f"🌙 Trailing stop hit long at {self.data.Low[-1]}! Trail: {self.trail_stop:.2f} 🚀")
                        self.reset_trade_vars()
                        return

            else:  # short
                profit = self.entry_price - self.data.Close[-1]
                sl_price = self.entry_price + self.sl_mult * entry_atr
                tp_price = self.entry_price - self.tp_mult * entry_atr

                # Initial SL/TP check
                if self.data.High[-1] >= sl_price:
                    self.position.close()
                    print(f"🌙 Stop loss hit short at {self.data.High[-1]}! 💥 Entry: {self.entry_price}")
                    self.reset_trade_vars()
                    return
                if self.data.Low[-1] <= tp_price:
                    self.position.close()
                    print(f"🌙 Take profit hit short at {self.data.Low[-1]}! 🎉 Entry: {self.entry_price}")
                    self.reset_trade_vars()
                    return

                # Reversal check - 🌙 Tightened mom threshold to >70 for faster short exits, and added EMA cross for better reversal detection
                if self.detect_bullish_div() or self.current_mom > 70 or self.data.Close[-1] > self.ema[-1]:
                    self.position.close()
                    print(f"🌙 Reversal signal exit short! Mom: {self.current_mom:.2f} 🚨")
                    self.reset_trade_vars()
                    return

                # Trailing logic
                if profit > self.profit_trail * self.atr[-1]:
                    if not self.trail_active:
                        self.trail_active = True
                        self.lowest_since_entry = self.data.Low[-1]
                        self.trail_stop = self.lowest_since_entry + self.trail_mult * self.atr[-1]
                        print(f"🌙 Trailing activated for short! Trail stop: {self.trail_stop:.2f} ✨")
                    else:
                        self.lowest_since_entry = min(self.lowest_since_entry, self.data.Low[-1])
                        new_trail = self.lowest_since_entry + self.trail_mult * self.atr[-1]
                        self.trail_stop = min(self.trail_stop, new_trail)

                    if self.data.High[-1] > self.trail_stop:
                        self.position.close()
                        print(f"🌙 Trailing stop hit short at {self.data.High[-1]}! Trail: {self.trail_stop:.2f} 🚀")
                        self.reset_trade_vars()
                        return

        # Entry logic if no position
        else:
            # 🌙 Tightened volatility filter to >0.5x average to focus on higher volatility periods, avoiding low-momentum ranges for better setups
            if np.isnan(self.atr[-1]) or np.isnan(self.atr_avg[-1]) or self.atr[-1] <= 0.5 * self.atr_avg[-1]:
                print(f"🌙 Low volatility filter: ATR {self.atr[-1]:.2f} <= 0.5*Avg {self.atr_avg[-1]:.2f} 😴")
                return

            above_ema = self.data.Close[-1] > self.ema[-1]
            below_ema = not above_ema
            above_ema_long = self.data.Close[-1] > self.ema_long[-1]  # 🌙 Added long EMA confirmation for longs to align with broader uptrend
            below_ema_long = self.data.Close[-1] < self.ema_long[-1]  # 🌙 Added long EMA confirmation for shorts to align with broader downtrend

            # 🌙 Strengthened ADX to >25 and volume to >1.2x SMA for higher-quality trends, filtering out weaker signals to improve win rate
            strong_trend = self.adx[-1] > 25
            strong_volume = self.data.Volume[-1] > 1.2 * self.vol_sma[-1]

            bullish_div = self.detect_bullish_div()
            bearish_div = self.detect_bearish_div()

            # Long entry
            if (bullish_div and self.current_mom > self.mom_long_thresh and mom_rising and above_ema and above_ema_long and strong_trend and strong_volume):
                equity = self._broker._cash + self.position.size * self.data.Close[-1]
                risk_amount = equity * self.risk_per_trade
                sl_distance = self.sl_mult * self.atr[-1]
                raw_size = risk_amount / sl_distance
                cash_size = self._broker._cash / self.data.Close[-1]
                vol_mult = 0.4 if self.atr[-1] > 1.5 * self.atr_avg[-1] else 1.0  # 🌙 Adjusted vol_mult to 0.4 in high vol for slightly looser but still controlled sizing
                size = min(cash_size, raw_size) * vol_mult  # 🌙 Removed int(round) for fractional sizing precision, improving capital efficiency
                self.buy(size=size)
                self.entry_price = self.data.Close[-1]
                self.entry_atr = self.atr[-1]
                self.is_long = True
                self.entry_bar = current_bar
                self.trail_active = False
                self.highest_since_entry = self.data.High[-1]
                print(f"🌙 Bullish divergence detected! Long entry at {self.entry_price:.2f}, size: {size}, Mom: {self.current_mom:.2f} 🚀 ATR: {self.atr[-1]:.2f} ADX: {self.adx[-1]:.2f}")

            # Short entry
            elif (bearish_div and self.current_mom < self.mom_short_thresh and mom_falling and below_ema and below_ema_long and strong_trend and strong_volume):
                equity = self._broker._cash + self.position.size * self.data.Close[-1]
                risk_amount = equity * self.risk_per_trade
                sl_distance = self.sl_mult * self.atr[-1]
                raw_size = risk_amount / sl_distance
                cash_size = self._broker._cash / self.data.Close[-1]
                vol_mult = 0.4 if self.atr[-1] > 1.5 * self.atr_avg[-1] else 1.0
                size = min(cash_size, raw_size) * vol_mult  # 🌙 Removed int(round) for fractional sizing precision
                self.sell(size=size)
                self.entry_price = self.data.Close[-1]
                self.entry_atr = self.atr[-1]
                self.is_long = False
                self.entry_bar = current_bar
                self.trail_active = False
                self.lowest_since_entry = self.data.Low[-1]
                print(f"🌙 Bearish divergence detected! Short entry at {self.entry_price:.2f}, size: {size}, Mom: {self.current_mom:.2f} ✨ ATR: {self.atr[-1]:.2f} ADX: {self.adx[-1]:.2f}")

    def update_swings(self):
        current_bar = self.bar_count
        pl = self.pivot_length
        for potential in range(self.last_checked + 1, current_bar - pl + 1):
            # Check low pivot
            is_low_pivot = True
            for k in range(max(0, potential - pl), min(current_bar + 1, potential + pl + 1)):
                if k != potential and self.data.Low[k] < self.data.Low[potential]:
                    is_low_pivot = False
                    break
            if is_low_pivot:
                rsi_val = self.rsi[potential]
                if not np.isnan(rsi_val):
                    self.confirmed_swing_lows.append((potential, self.data.Low[potential], rsi_val))
                    print(f"🌙 New swing low confirmed at bar {potential}, price {self.data.Low[potential]:.2f}, RSI {rsi_val:.2f} 📉")

            # Check high pivot
            is_high_pivot = True
            for k in range(max(0, potential - pl), min(current_bar + 1, potential + pl + 1)):
                if k != potential and self.data.High[k] > self.data.High[potential]:
                    is_high_pivot = False
                    break
            if is_high_pivot:
                rsi_val = self.rsi[potential]
                if not np.isnan(rsi_val):
                    self.confirmed_swing_highs.append((potential, self.data.High[potential], rsi_val))
                    print(f"🌙 New swing high confirmed at bar {potential}, price {self.data.High[potential]:.2f}, RSI {rsi_val:.2f} 📈")

        self.last_checked = current_bar - pl

    def detect_bullish_div(self):
        current_bar = self.bar_count
        if len(self.confirmed_swing_lows) < 2:
            return False
        last, prev = self.confirmed_swing_lows[-1], self.confirmed_swing_lows[-2]
        if current_bar - last[0] > 15:  # 🌙 Further reduced to 15 bars for ultra-fresh divergence signals, increasing timeliness and relevance
            return False
        return last[1] < prev[1] and last[2] > prev[2] + self.rsi_div_thresh

    def detect_bearish_div(self):
        current_bar = self.bar_count
        if len(self.confirmed_swing_highs) < 2:
            return False
        last, prev = self.confirmed_swing_highs[-1], self.confirmed_swing_highs[-2]
        if current_bar - last[0] > 15:  # 🌙 Further reduced to 15 bars for ultra-fresh divergence signals
            return False