import os
import telebot
from requests import post
from dotenv import load_dotenv

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
        users = bot.get_chat_members_count(message.chat.id)
        for i in range(users):
            user = bot.get_chat_member(message.chat.id, i)
            if user.user.username == username:
                vip_users.add(user.user.id)
                bot.reply_to(message, f"Выполнено! Пользователь {user.user.first_name} получил VIP-доступ.")
                bot.send_message(user.user.id, "Администратор выдал Вам VIP-доступ!\nТеперь Вы можете пользоваться ботом без ограничений.")
                return
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

# Полностью отключаем Webhook и включаем Long Polling
if __name__ == "__main__":
    bot.polling(none_stop=True)
