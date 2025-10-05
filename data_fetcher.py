import requests
import pandas as pd
import time
from database import cache_data, get_cached_data, is_cache_fresh

def fetch_ohlcv(coin_symbol, interval='1h', limit=100, source_priority=['binance', 'okx', 'coingecko']):
    coin_id = coin_symbol.lower()
    if is_cache_fresh(coin_id):
        cached = get_cached_data(coin_id)
        if cached:
            return pd.DataFrame(cached)
    for source in source_priority:
        try:
            if source == 'binance':
                url = f"https://api.binance.com/api/v3/klines?symbol={coin_symbol}&interval={interval}&limit={limit}"
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', '_', '_', '_', '_', '_', '_'])
                    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].astype(float)
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    cache_data(coin_id, df.to_dict('records'))
                    return df
            elif source == 'okx':
                url = f"https://www.okx.com/api/v5/market/candles?instId={coin_symbol}&bar={interval}&limit={limit}"
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()['data']
                    if data:
                        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', '_'])
                        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].astype(float)
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                        df = df[::-1]
                        cache_data(coin_id, df.to_dict('records'))
                        return df
            elif source == 'coingecko':
                coin_id = coin_symbol.lower().replace('usdt', '')
                url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc?vs_currency=usd&days=30"
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
                    df['volume'] = 0
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df = df.sort_values('timestamp')
                    cache_data(coin_id, df.to_dict('records'))
                    return df
        except Exception as e:
            print(f"Error with {source}: {e}")
            continue
    raise ValueError(f"Không lấy được dữ liệu cho {coin_symbol}")

def get_top_coins_by_category(category, per_page=50):
    categories_map = {
        'top': 'all',
        'meme': 'meme-token',
        'defi': 'decentralized-finance-defi',
        'ai': 'ai-agents'
    }
    cat_id = categories_map.get(category, 'all')
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&category={cat_id}&order=market_cap_desc&per_page={per_page}&page=1&sparkline=false"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 200:
        return resp.json()
    return []

def get_long_short_ratio(symbol):
    try:
        url = f"https://fapi.binance.com/fapi/v1/globalLongShortAccountRatio?symbol={symbol}&period=5m&limit=1"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()[0]
            return float(data['longShortRatio'])
    except:
        pass
    return 1.0
