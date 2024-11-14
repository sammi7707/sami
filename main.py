import requests
import time
from telegram import Bot
from flask import Flask, jsonify

# إعدادات التوكن ومعرف القناة لتيلجرام
TELEGRAM_API_TOKEN = '7981996529:AAEHLneABT3QTuDdp3e4rdqgaxb6Tnqe6iE'  # استبدل بـ توكن البوت من BotFather
CHANNEL_ID = '@sami09_chart'  # استبدل بـ معرف قناتك مثل: @mychannel

# رابط API للحصول على بيانات التداول من Binance
BINANCE_API_URL = 'https://api.binance.com/api/v3/ticker/24hr'

# تهيئة البوت باستخدام التوكن
bot = Bot(token=TELEGRAM_API_TOKEN)

# دالة للحصول على بيانات حجم التداول للأزواج مقابل USDT
def get_usdt_pairs(retries=3, wait=5, rate_limit_per_second=1):
    """
    جلب بيانات التداول للأزواج مقابل USDT من Binance API.
    retries: عدد المحاولات في حالة فشل الاتصال
    wait: مدة الانتظار بالثواني بين المحاولات
    rate_limit_per_second: معدل الطلبات المسموح به لكل ثانية (مثال: 1 طلب في الثانية)
    """
    last_request_time = time.time() 
    attempt = 0
    while attempt < retries:
        try:
            # تأخير الطلب لضمان عدم تجاوز معدل الطلبات
            current_time = time.time()
            if current_time - last_request_time < 1 / rate_limit_per_second:
                time.sleep(1 / rate_limit_per_second - (current_time - last_request_time))

            # انتظار قبل كل محاولة 
            time.sleep(10)  # الانتظار لمدة 10 ثوانٍ قبل كل محاولة

            response = requests.get(BINANCE_API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()

            # تصفية الأزواج التي تنتهي بـ USDT فقط
            usdt_pairs = {
                item['symbol']: float(item['volume'])
                for item in data if item['symbol'].endswith('USDT')
            }
            return usdt_pairs

        except requests.RequestException as e:
            print(f"Error fetching data (Attempt {attempt + 1} of {retries}): {e}")
            attempt += 1
            time.sleep(wait)

    print("Failed to fetch data after multiple attempts.")
    return {}

# دالة لإرسال التنبيه إلى تيلجرام
def send_alert(coin, volume, multiplier):
    """
    إرسال رسالة تنبيه إلى تيلجرام عند تضاعف حجم التداول.
    coin: اسم العملة
    volume: حجم التداول الحالي
    multiplier: عدد مرات التضاعف
    """
    message = f"🚨 حجم التداول لـ {coin} تضاعف {multiplier} مرات! الحجم الحالي: {volume} USDT"
    bot.send_message(chat_id=CHANNEL_ID, text=message)

# دالة لمراقبة حجم التداول وإرسال التنبيهات عند التضاعف
def monitor_volume():
    """
    مراقبة التغيرات في حجم التداول كل 5 دقائق، وإرسال تنبيه عند تضاعف الحجم.
    """
    # الحصول على بيانات الحجم الأولية
    previous_volumes = get_usdt_pairs()

    # التحقق من البيانات كل 5 دقائق
    while True:
        # جلب بيانات الحجم الحالية
        current_volumes = get_usdt_pairs()

        # التحقق من أن البيانات غير فارغة
        if not current_volumes:
            print("No data available. Retrying in 5 minutes.")
            time.sleep(300)
            continue

        # مقارنة البيانات الحالية بالبيانات السابقة
        for coin, new_volume in current_volumes.items():
            old_volume = previous_volumes.get(coin, 0)

            # التحقق إذا تضاعف الحجم
            if old_volume > 0 and new_volume >= 2 * old_volume:
                multiplier = new_volume // old_volume
                send_alert(coin, new_volume, multiplier)

            # تحديث حجم التداول السابق
            previous_volumes[coin] = new_volume

        # الانتظار لمدة 5 دقائق قبل الدورة التالية
        time.sleep(300)

# بدء تشغيل البوت
if __name__ == "__main__":
    monitor_volume()

# ... بقية الكود ...

app = Flask(__name__)

@app.route('/get_usdt_pairs')
def get_usdt_pairs_api():
    """
    دالة API للحصول على بيانات حجم التداول للأزواج مقابل USDT.
    """
    usdt_pairs = get_usdt_pairs()  # استدعاء الدالة الحالية للحصول على البيانات
    return jsonify(usdt_pairs)  # تحويل البيانات إلى صيغة JSON

if __name__ == "__main__":
    app.run(debug=True)