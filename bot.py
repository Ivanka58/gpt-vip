import os
import telebot
from threading import Thread
from requests import post
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler, HTTPServer
import certifi  # Добавляем для поддержки TLS
import urllib3  # Для обработки соединений

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Загрузка переменных окружения
load_dotenv()
API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
CHAT_GPT_API_KEY = os.getenv('CHAT_GPT_API_KEY')
ADMIN_ID = int(os.getenv('ADMIN_TELEGRAM_ID'))  # Ваше собственное ID администратора

# Создание объектов
bot = telebot.TeleBot(API_TOKEN)

# Список пользователей с VIP-доступом
vip_users = set()

# Функция отправки запроса в GigaChat через API
def gigachat_request(prompt):
    headers = {
        "Authorization": f"Bearer {CHAT_GPT_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"prompt": prompt}
    timeout_seconds = 15  # Таймаут увеличен до 15 секунд
    try:
        # Используйте современный SSL-контекст
        response = post("https://api.gigachat.ru/v1/completions", json=payload, headers=headers, verify=certifi.where(), timeout=timeout_seconds)
        if response.status_code == 200:
            return response.json()['choices'][0]['text'].strip()
        else:
            return "Ошибка обработки запроса."
    except Exception as e:
        return str(e)

# Команда "/start"
@bot.message_handler(commands=["start"])
def start_command(message):
    bot.reply_to(message, "Привет! Этот чат GPT только для избранных.\n\n"
                          "Если ты попал сюда, значит ты особенный,\n"
                          "Но чтобы я знал, что ты попал сюда не случайно,\n"
                          "напиши @Ivanka58 для получения доступа.")

# Команда выдачи VIP-доступа
@bot.message_handler(commands=["VIP"], func=lambda m: m.chat.id == ADMIN_ID)
def grant_vip_access(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        bot.reply_to(message, "Формат неверный!\nИспользуйте: `/VIP <UserID>`")
        return

    user_id = parts[1].strip()  # Чистый UserID
    try:
        user_id = int(user_id)  # Конвертировать в целое число
        vip_users.add(user_id)
        bot.reply_to(message, f"Выполнено! Пользователю с ID {user_id} предоставлен VIP-доступ.")
        bot.send_message(user_id, "Администратор выдал Вам VIP-доступ!\nТеперь Вы можете пользоваться ботом без ограничений.")
    except ValueError:
        bot.reply_to(message, "Некорректный ID пользователя. Используйте целые числа.")

# Обработка обычных сообщений
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if message.from_user.id in vip_users or message.from_user.id == ADMIN_ID:
        # Показываем статус ожидания
        msg = bot.reply_to(message, "AI думает...")
        # Отправляем запрос в GigaChat через API
        response = gigachat_request(message.text)
        # Отвечаем и удаляем временное сообщение
        bot.delete_message(msg.chat.id, msg.message_id)
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "У Вас нет доступа к этому боту.\nОбратитесь к администратору @Ivanka58.")

# Простой фиктивный сервер для удовлетворения требований Render
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()

def run_server():
    PORT = int(os.environ.get('PORT', 8080))
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    httpd.serve_forever()

# Запуск фиктивного сервера в отдельном потоке
Thread(target=run_server, daemon=True).start()

# Включаем Long Polling
if __name__ == "__main__":
    bot.polling(none_stop=True)
