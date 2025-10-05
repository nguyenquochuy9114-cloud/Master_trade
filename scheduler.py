import apscheduler.schedulers.background
from apscheduler.triggers.interval import IntervalTrigger
from data_fetcher import get_top_coins_by_category, fetch_ohlcv
from analyzer import check_volatility, analyze_coin
from database import get_subscribed_users
from bot import bot, logger

scheduler = apscheduler.schedulers.background.BackgroundScheduler()

def hourly_update():
    categories = ['top', 'meme', 'defi', 'ai']
    for cat in categories:
        coins = get_top_coins_by_category(cat, 10)  # Giảm xuống 10 để tránh overload
        for coin in coins:
            try:
                symbol = coin['symbol'].upper() + 'USDT'
                fetch_ohlcv(symbol)
            except Exception as e:
                logger.error(f"Hourly update error for {symbol}: {e}")

def check_alerts():
    users = get_subscribed_users()
    if not users:
        return
    coins_to_track = ['BTCUSDT', 'ETHUSDT']  # Có thể mở rộng từ DB
    for coin in coins_to_track:
        try:
            df_new = fetch_ohlcv(coin)
            if check_volatility([], df_new):  # Placeholder, cần lưu df_old
                analysis = analyze_coin(df_new, coin)
                msg = format_analysis_msg(analysis, coin)
                for user_id in users:
                    bot.send_message(user_id, f"🚨 **Cảnh báo {coin}: Biến động mạnh >5%!**\n{msg}", parse_mode='Markdown')
                    if analysis.get('chart'):
                        with open(analysis['chart'], 'rb') as photo:
                            bot.send_photo(user_id, photo)
                        os.remove(analysis['chart'])
        except Exception as e:
            logger.error(f"Alert check error for {coin}: {e}")

scheduler.add_job(hourly_update, IntervalTrigger(hours=1))
scheduler.add_job(check_alerts, IntervalTrigger(hours=1))
