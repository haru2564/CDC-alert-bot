import pandas as pd
import pandas_ta as ta
import requests
import time

# ================= ตั้งค่าข้อมูลส่วนตัว =================
TELEGRAM_TOKEN = ''
CHAT_ID = ''
SYMBOL = 'PAXGBTC'  # คู่เทรดบน Binance
TIMEFRAME = '1d'    # '1d' = รายวัน, '4h' = 4 ชั่วโมง
# ===================================================

def get_binance_data(symbol, interval):
    """ ดึงข้อมูลราคาย้อนหลัง 100 แท่งจาก Binance """
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # แปลงข้อมูลเป็น DataFrame
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 
            'close_time', 'q_av', 'num_trades', 'taker_base', 'taker_quote', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def send_telegram(message):
    """ ส่งข้อความเข้า Telegram """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": message, 
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending Telegram: {e}")

def main():
    print(f"--- กำลังตรวจสอบราคา {SYMBOL} ({TIMEFRAME}) ---")
    
    # 1. ดึงข้อมูล
    df = get_binance_data(SYMBOL, TIMEFRAME)
    if df is None: return

    # 2. คำนวณ EMA สำหรับ CDC Action Zone
    # ใช้ pandas_ta คำนวณ EMA 12 และ 26
    ema12 = ta.ema(df['close'], length=12)
    ema26 = ta.ema(df['close'], length=26)

    # ดึงค่าล่าสุด (แท่งปัจจุบัน)
    current_price = df['close'].iloc[-1]
    current_ema12 = ema12.iloc[-1]
    current_ema26 = ema26.iloc[-1]
    
    # ดึงค่าแท่งก่อนหน้า (เพื่อเช็คจุดตัด)
    prev_ema12 = ema12.iloc[-2]
    prev_ema26 = ema26.iloc[-2]

    # 3. ตัดสินใจตามเงื่อนไข CDC Action Zone
    # เขียว = EMA12 อยู่เหนือ EMA26
    if current_ema12 > current_ema26:
        status = "🟢 *สีเขียว (Bullish)*"
    else:
        status = "🔴 *สีแดง (Bearish)*"

    # เช็คว่าเพิ่งเปลี่ยนสีวันนี้วันแรกหรือไม่ (จุดตัด)
    signal_note = ""
    if prev_ema12 <= prev_ema26 and current_ema12 > current_ema26:
        signal_note = "\n✨ *BUY SIGNAL (เพิ่งเปลี่ยนเป็นสีเขียว)*"
    elif prev_ema12 >= prev_ema26 and current_ema12 < current_ema26:
        signal_note = "\n⚠️ *SELL SIGNAL (เพิ่งเปลี่ยนเป็นสีแดง)*"

    # 4. สร้างข้อความและส่ง
    message = (
        f"📊 *CDC Action Zone Report*\n"
        f"Symbol: `{SYMBOL}`\n"
        f"Timeframe: `{TIMEFRAME}`\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Status: {status}\n"
        f"Price: `{current_price:.8f}` BTC\n"
        f"{signal_note}"
    )

    print(message)
    send_telegram(message)
    print("--- ส่งการแจ้งเตือนเรียบร้อยแล้ว ---")

if __name__ == '__main__':

    main()
