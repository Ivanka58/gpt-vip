import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
CHAT_GPT_API_KEY = os.getenv('CHAT_GPT_API_KEY')
ADMIN_ID = int(os.getenv('ADMIN_TELEGRAM_ID'))
BOT_ID = int(os.getenv('TELEGRAM_BOT_ID'))

# Создаем объект бота и диспетчер
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Список пользователей с VIP-доступом
vip_users = set()

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer("Привет! Этот чат GPT только для избранных.\n\n"
                         "Если ты попал сюда, значит ты особенный,\n"
                         "Но чтобы я знал, что ты попал сюда не случайно,\n"
                         "напиши @Ivanka58 для получения доступа.")

@dp.message_handler(commands=['VIP'], user_id=ADMIN_ID)
async def grant_vip_access(message: types.Message):
    if len(message.text.split()) > 1:
        username = message.text.split()[1]
        # Проверяем наличие пользователя по юзернейму
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton(text="Да", callback_data=f'grant:{username}'),
            InlineKeyboardButton(text="Нет", callback_data='cancel')
        )
        await message.reply(f"Вы хотите выдать VIP доступ пользователю {username}?",
                           reply_markup=markup)
    else:
        await message.reply("Неверный формат команды!\nИспользуйте: /VIP @username")

@dp.callback_query_handler(lambda call: True)
async def process_callback(call: types.CallbackQuery):
    action, *args = call.data.split(':')
    if action == 'grant':
        username = args[0].strip('@')  # Убираем символ '@'
        user_id = None
        async for chat_member in bot.get_chat_members(chat_id=BOT_ID):
            if chat_member.user.username == username:
                user_id = chat_member.user.id
                break
        
        if user_id is not None:
            vip_users.add(user_id)
            await bot.send_message(user_id,
                                  f"Администратор выдал вам VIP доступ!!\nТеперь вы можете пользоваться ботом без ограничений.")
            await call.message.edit_text(f"VIP доступ успешно выдан пользователю {username}.")
        else:
            await call.message.edit_text(f"Пользователь {username} не найден!")
    
    elif action == 'cancel':
        await call.message.edit_text("Действие отменено.")

@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def handle_message(message: types.Message):
    if message.from_user.id in vip_users or message.from_user.id == ADMIN_ID:
        # Отправляем запрос в ChatGPT через API
        response = await send_to_gpt_api(message.text)
        await message.answer(response)
    else:
        await message.answer("У вас нет доступа к этому боту(\nОбратитесь к администратору @Ivanka58")

async def send_to_gpt_api(prompt):
    headers = {
        "Authorization": f"Bearer {CHAT_GPT_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {"prompt": prompt}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.gigachat.ru/v1/completions", json=data, headers=headers) as resp:
                result = await resp.json()
                return result['choices'][0]['text']
    except Exception as e:
        print(e)
        return "Ошибка обработки запроса."

if name == 'main':
    from aiogram.utils.executor import start_webhook
    PORT = int(os.environ.get('PORT', 8080))
    WEBHOOK_URL = f"https://your-render-domain.herokuapp.com/{API_TOKEN}"
    start_webhook(dispatcher=dp, webhook_path=f"/{API_TOKEN}", on_startup=None, port=PORT, host='0.0.0.0', skip_updates=True)
