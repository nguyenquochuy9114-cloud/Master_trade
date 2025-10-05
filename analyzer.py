import talib
import numpy as np
import pandas as pd
from utils import plot_candlestick
from data_fetcher import get_long_short_ratio

def analyze_coin(df, symbol):
    if len(df) < 30:
        return "Dữ liệu không đủ để phân tích."

    close = df['close'].values
    high = df['high'].values
    low = df['low'].values

    ema12 = talib.EMA(close, timeperiod=12)[-1]
    ema26 = talib.EMA(close, timeperiod=26)[-1]
    rsi = talib.RSI(close, timeperiod=14)[-1]

    recent_high = np.max(high[-20:])
    recent_low = np.min(low[-20:])
    fib_levels = {
        '23.6%': recent_high - 0.236 * (recent_high - recent_low),
        '38.2%': recent_high - 0.382 * (recent_high - recent_low),
        '50%': recent_high - 0.5 * (recent_high - recent_low),
        '61.8%': recent_high - 0.618 * (recent_high - recent_low)
    }

    ratio = get_long_short_ratio(symbol.replace('-', '') + 'USDT')
    current_price = close[-1]
    sl_long = current_price * 0.99
    tp_long = current_price * 1.04
    rr_long = (tp_long - current_price) / (current_price - sl_long)

    trend = "Tăng" if ema12 > ema26 else "Giảm"
    signal = "MUA" if (rsi < 30 and ema12 > ema26) else "BÁN" if (rsi > 70 and ema12 < ema26) else "GIỮ"
    reason = f"EMA12 ({ema12:.4f}) {'trên' if ema12 > ema26 else 'dưới'} EMA26 ({ema26:.4f}), RSI {rsi:.2f} ({'Oversold' if rsi<30 else 'Overbought' if rsi>70 else 'Neutral'}). Long/Short: {ratio:.2f}x."

    chart_path = plot_candlestick(df, symbol, ema12, ema26)

    return {
        'price': current_price,
        'ema12': ema12, 'ema26': ema26,
        'rsi': rsi,
        'fib': fib_levels,
        'long_short': ratio,
        'tp_long': tp_long, 'sl_long': sl_long, 'rr': rr_long * 100,
        'trend': trend,
        'recommend': signal,
        'reason': reason,
        'chart': chart_path
    }

def check_volatility(df_old, df_new, threshold=5.0):
    if len(df_old) == 0 or len(df_new) == 0:
        return False
    old_price = df_old['close'].iloc[-1]
    new_price = df_new['close'].iloc[-1]
    change = abs((new_price - old_price) / old_price * 100)
    return change > threshold
