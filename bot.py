import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import os
from dotenv import load_dotenv
import flask
from flask import request
import apscheduler.schedulers.background
from apscheduler.triggers.interval import IntervalTrigger
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = flask.Flask(__name__)

# Import other modules (assume in same directory)
from data_fetcher import fetch_ohlcv, get_top_coins_by_category
from analyzer import analyze_coin
from utils import format_analysis_msg
from database import add_user, set_subscribed, get_subscribed_users
from scheduler import hourly_update, check_alerts

# Pagination state
page_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.from_user.id)
    markup = InlineKeyboardMarkup(row_width=2)
    btn_top = InlineKeyboardButton("🟩 Top Coin", callback_data="cat_top_0")
    btn_meme = InlineKeyboardButton("😂 Meme", callback_data="cat_meme_0")
    btn_defi = InlineKeyboardButton("🏦 DeFi", callback_data="cat_defi_0")
    btn_ai = InlineKeyboardButton("🤖 Trend/AI", callback_data="cat_ai_0")
    btn_sub = InlineKeyboardButton("🔔 Đăng ký Alert", callback_data="sub_toggle")
    markup.add(btn_top, btn_meme, btn_defi, btn_ai, btn_sub)
    bot.send_message(message.chat.id, "Chào mừng đến **Master Trader**! Chọn danh mục:", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['search'])
def search(message):
    query = message.text.split(' ', 1)[1] if len(message.text.split()) > 1 else ''
    if not query:
        bot.reply_to(message, "Sử dụng: /search <coin> (vd: /search BTC)")
        return
    try:
        symbol = query.upper() + 'USDT'
        df = fetch_ohlcv(symbol)
        analysis = analyze_coin(df, symbol)
        msg = format_analysis_msg(analysis, query.upper())
        bot.reply_to(message, msg, parse_mode='Markdown')
        if analysis.get('chart'):
            with open(analysis['chart'], 'rb') as photo:
                bot.send_photo(message.chat.id, photo)
            os.remove(analysis['chart'])
    except Exception as e:
        logger.error(f"Search error: {e}")
        bot.reply_to(message, f"Lỗi: Không tìm thấy {query}. Thử BTC, ETH...")

@bot.callback_query_handler(func=lambda call: call.data.startswith('cat_'))
def handle_category(call: CallbackQuery):
    _, cat, page_str = call.data.split('_')
    page = int(page_str)
    user_id = call.from_user.id

    if user_id not in page_data:
        page_data[user_id] = {'cat': cat, 'page': 0, 'coins': []}
    data = page_data[user_id]
    data['page'] = page

    if not data['coins']:
        data['coins'] = get_top_coins_by_category(cat, 50)

    start_idx = page * 10
    end_idx = min(start_idx + 10, 50)
    coins_slice = data['coins'][start_idx:end_idx]

    msg = f"**Danh mục {cat.upper()}: Trang {page+1}/5**\n"
    for coin in coins_slice:
        msg += f"• {coin['name']} ({coin['symbol']}): ${coin['current_price']:.4f} | MC: ${coin['market_cap']:.0f}\n"

    markup = InlineKeyboardMarkup()
    if page > 0:
        markup.add(InlineKeyboardButton("⬅️ Trước", callback_data=f"cat_{cat}_{page-1}"))
    if end_idx < 50:
        markup.add(InlineKeyboardButton("➡️ Sau", callback_data=f"cat_{cat}_{page+1}"))
    markup.add(InlineKeyboardButton("🔍 Phân tích coin", callback_data=f"analyze_{coins_slice[0]['id']}"))
    markup.add(InlineKeyboardButton("🔙 Menu", callback_data="menu"))

    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith('analyze_'))
def handle_analyze(call: CallbackQuery):
    coin_id = call.data.split('_')[1]
    try:
        symbol = coin_id.upper() + 'USDT'
        df = fetch_ohlcv(symbol, coin_id=coin_id)
        analysis = analyze_coin(df, coin_id)
        msg = format_analysis_msg(analysis, coin_id.upper())
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        if analysis.get('chart'):
            with open(analysis['chart'], 'rb') as photo:
                bot.send_photo(call.message.chat.id, photo)
            os.remove(analysis['chart'])
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        bot.answer_callback_query(call.id, "Lỗi phân tích!")

@bot.callback_query_handler(func=lambda call: call.data == 'sub_toggle')
def toggle_sub(call: CallbackQuery):
    user_id = call.from_user.id
    subscribed = not get_subscribed_users().__contains__(user_id)
    set_subscribed(user_id, subscribed)
    status = "Đã đăng ký" if subscribed else "Đã hủy"
    bot.answer_callback_query(call.id, f"🔔 {status} alert mỗi giờ!")

@bot.callback_query_handler(func=lambda call: call.data == 'menu')
def menu(call: CallbackQuery):
    start(call.message)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'OK', 200

@app.route('/health')
def health():
    return 'Bot OK'

def set_webhook(url):
    bot.remove_webhook()
    bot.set_webhook(url)

if __name__ == '__main__':
    logger.info("Bot starting...")
    scheduler.start()
    webhook_url = 'https://master-trade-bot.onrender.com'  # Thay bằng URL Render sau deploy
    set_webhook(webhook_url)
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
