from flask import Flask
import threading
import time
import requests
import urllib.parse
import re
import os
# ==== НАСТРОЙКИ ====

app = Flask(__name__)
SKINS_TO_MONITOR = [
    {"name": "AWP | Pit Viper (Field-Tested)", "threshold": 60},
    {"name": "Desert Eagle | Bronze Deco (Factory New)", "threshold": 85},
    {"name": "Tec-9 | Sandstorm (Field-Tested)", "threshold": 100},
    {"name": "SG 553 | Cyrex (Battle-Scarred)","threshold": 450},
]

CURRENCY = 5  # 5 = рубли
CHECK_INTERVAL = 20 * 60  # каждые 20 минут
FULL_INTERVAL = 4 * 60 * 60 #каждые 4 часа


# Telegram
TELEGRAM_BOT_TOKEN = "7791511329:AAESunuCTW_K05TwIbRSjEhDseV63lrkM68"
TELEGRAM_CHAT_ID = "1608718134"

# ===================

def send_telegram_message(message: str):
   
    url = (
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        f"?chat_id={TELEGRAM_CHAT_ID}&text={urllib.parse.quote(message)}"
    )
    try:
        requests.get(url)
    except Exception as e:
        print("Ошибка отправки сообщения:", e)

def get_lowest_price(skin_name: str, currency: int = 5):
    encoded_name = urllib.parse.quote(skin_name)
    url = (
        f"https://steamcommunity.com/market/priceoverview/?country=RU&currency={currency}"
        f"&appid=730&market_hash_name={encoded_name}"
    )
    try:
        response = requests.get(url)
        data = response.json()
        if "lowest_price" in data and data["lowest_price"]:
            price_str = data["lowest_price"]

            # Заменяем запятые на точки (для 1 234,56)
            price_str = price_str.replace(",", ".")

            # Удаляем всё, кроме цифр и точек
            price_str = re.sub(r"[^\d.]", "", price_str)

            # Если точек больше одной — оставляем только первую
            if price_str.count('.') > 1:
                parts = price_str.split('.')
                price_str = parts[0] + '.' + ''.join(parts[1:])

            # Удаляем точку в конце, если осталась
            if price_str.endswith('.'):
                price_str = price_str[:-1]

            return float(price_str)
    except Exception as e:
        print(f"[!] Ошибка при получении цены для {skin_name}: {e}")
    return None

@app.route("/")
def home():
    return "Скрипт мониторинга скинов работает!"



def monitor_prices():
    print("?? Запущен мониторинг нескольких скинов...")
    send_telegram_message("? Тест: бот успешно подключён!")
    last_report_time = time.time()

    while True:
        now = time.time()
        for skin in SKINS_TO_MONITOR:
            name = skin["name"]
            threshold = skin["threshold"]
            price = get_lowest_price(name, CURRENCY)
            if price:
                print(f"[+] {name} — текущая цена: {price} руб.")
                if price > threshold:
                    msg = f"?? Цена на '{name}' выше порога!\nТекущая цена: {price} руб. (порог: {threshold} руб.)"
                    send_telegram_message(msg)
            else:
                print(f"[-] Не удалось получить цену для: {name}")
        

        if now - last_report_time >= FULL_INTERVAL:
            report_lines = ["?? Текущие цены на скины:"]
            for skin in SKINS_TO_MONITOR:
                price = get_lowest_price(skin["name"], CURRENCY)
                if price is not None:
                    report_lines.append(f"{skin['name']}: {price} руб.")
                else:
                    report_lines.append(f"{skin['name']}: не удалось получить цену")
            send_telegram_message("\n".join(report_lines))
            last_report_time = now

        print(f"? Ожидание {CHECK_INTERVAL // 60} минут до следующей проверки...\n")
        time.sleep(CHECK_INTERVAL)

def run_monitor():
    thread = threading.Thread(target=monitor_prices)
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    run_monitor()
    app.run(host="0.0.0.0", port=8000)





