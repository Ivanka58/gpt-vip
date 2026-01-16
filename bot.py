import os
import telebot
from flask import Flask, request
from requests import post
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
CHAT_GPT_API_KEY = os.getenv('CHAT_GPT_API_KEY')
ADMIN_ID = int(os.getenv('ADMIN_TELEGRAM_ID'))
BOT_ID = int(os.getenv('TELEGRAM_BOT_ID'))

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
    response = post("https://api.gigachat.ru/v1/completions", json=payload, headers=headers)
    return response.json()['choices'][0]['text'] if response.status_code == 200 else "Ошибка обработки запроса."

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
    if len(message.text.split()) > 1:
        username = message.text.split()[1].lstrip("@")  # Удаляем символ "@"
        # Поиск пользователя по имени
        users = bot.get_chat_members(BOT_ID)
        target_user = next((member for member in users if member.user.username == username), None)
        if target_user:
            vip_users.add(target_user.user.id)
            bot.reply_to(message, f"Выполнено! Пользователь {target_user.user.first_name} получил VIP-доступ.")
            bot.send_message(target_user.user.id, "Администратор выдал Вам VIP-доступ!\nТеперь Вы можете пользоваться ботом без ограничений.")
        else:
            bot.reply_to(message, f"Пользователь '{username}' не найден.")
    else:
        bot.reply_to(message, "Формат неверный!\nИспользуйте: /VIP @username")

# Обработка обычных сообщений
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if message.from_user.id in vip_users or message.from_user.id == ADMIN_ID:
        # Отправляем запрос в GigaChat через API
        response = gigachat_request(message.text)
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "У Вас нет доступа к этому боту.\nОбратитесь к администратору @Ivanka58.")

# Настройки веб-хука для Heroku/Render
server = Flask(name)
WEBHOOK_PORT = int(os.environ.get('PORT', 8080))  # Порт для вебхуков
WEBHOOK_URL_BASE = f"https://{os.getenv('RENDER_DOMAIN_NAME')}"  # Доменное имя Render
WEBHOOK_URL_PATH = f"/webhook/{API_TOKEN}/"

# Регистрация хука
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)

# Маршрутизация запросов
@server.route('/' + WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return '', 200

# Запуск сервера
if name == "main":
    server.run(host='0.0.0.0', port=WEBHOOK_PORT)
