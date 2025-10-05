import matplotlib.pyplot as plt
import mplfinance as mpf
import os
import tempfile

def plot_candlestick(df, symbol, ema12, ema26):
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        path = tmp.name

    df_plot = df.copy()
    df_plot['EMA12'] = talib.EMA(df['close'], 12)
    df_plot['EMA26'] = talib.EMA(df['close'], 26)
    df_plot = df_plot.set_index('timestamp')

    mpf.plot(df_plot, type='candle', mav=(12,26), volume=True, title=f'{symbol} Chart', style='charles',
             savefig=dict(fname=path, bbox_inches='tight'))
    return path

def format_analysis_msg(analysis, symbol):
    msg = f"""
📈 **Phân tích {symbol.upper()}**
💰 Giá hiện tại: ${analysis['price']:.4f}

📊 **Indicators:**
• EMA12: {analysis['ema12']:.4f} | EMA26: {analysis['ema26']:.4f}
• RSI: {analysis['rsi']:.2f}

🌀 **Fibonacci Levels (Retracement):**
• 23.6%: ${analysis['fib']['23.6%']:.4f}
• 38.2%: ${analysis['fib']['38.2%']:.4f}
• 50%: ${analysis['fib']['50%']:.4f}
• 61.8%: ${analysis['fib']['61.8%']:.4f}

⚖️ **Long/Short Ratio:** {analysis['long_short']:.2f}x
🎯 **Gợi ý Long:** TP: ${analysis['tp_long']:.4f} | SL: ${analysis['sl_long']:.4f} | RR: {analysis['rr']:.1f}%

🔮 **Xu hướng:** {analysis['trend']} | **Khuyến nghị:** {analysis['recommend']}
📝 **Lý do:** {analysis['reason']}

⚠️ **Cảnh báo:** Nếu RSI >70, bán khẩn! Nếu <30, mua dip.
    """
    return msg
