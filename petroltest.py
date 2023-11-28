import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup

bot = telebot.TeleBot('6948116626:AAG79Y8Akq2_wwU-4Fb6NaB8aHuRF_yKRoM')

# Переменные для хранения логина и пароля
login = None
password = None

# Переменные для хранения ID последнего сообщения о ценах
last_prices_message_id = None

# Функция для получения цен на бензин с сайта
def get_gas_prices():
    url = 'https://www.autostrada.uz/benzin/'
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table')
        rows = table.find_all('tr')

        gas_prices = []

        # Получаем заголовки (названия компаний)
        header_row = rows[0].find_all('th')
        headers = [header.text.strip() for header in header_row]

        gas_prices.append(headers)

        # Получаем цены на бензин
        for row in rows[1:]:
            cols = row.find_all('td')
            cols = [col.text.strip() for col in cols]
            gas_prices.append(cols)

        return gas_prices
    else:
        return None

# Обработка команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Привет! Я бот. Для получения цен на бензин используй /auth для входа.')

# Обработка команды /reset
@bot.message_handler(commands=['reset'])
def reset(message):
    global login, password, last_prices_message_id
    login = None
    password = None
    if last_prices_message_id:
        bot.delete_message(message.chat.id, last_prices_message_id)
    bot.reply_to(message, 'Состояние сброшено.')

# Обработка команды /auth
@bot.message_handler(commands=['auth'])
def auth(message):
    global login, password
    command_args = message.text.split()
    if len(command_args) != 3:
        bot.reply_to(message, 'Неверный формат команды. Используйте /auth логин пароль.')
        return

    provided_login = command_args[1]
    provided_password = command_args[2]

    # Проверка логина и пароля
    if provided_login == 'admin' and provided_password == 'thegreatestpassword':
        login = provided_login
        password = provided_password
        bot.reply_to(message, 'Аутентификация успешна. Теперь вы можете использовать команду /gas_prices.')
    else:
        bot.reply_to(message, 'Неправильный логин или пароль.')

# Обработка команды /gas_prices
@bot.message_handler(commands=['gas_prices'])
def send_gas_prices(message):
    global login, password, last_prices_message_id

    # Проверка наличия аутентификации
    if login != 'admin' or password != 'thegreatestpassword':
        bot.reply_to(message, 'Необходимо пройти аутентификацию. Используйте команду /auth для входа.')
        return

    markup = types.ReplyKeyboardMarkup(row_width=2)
    buttons = []

    # Получаем виды топлива
    prices = get_gas_prices()
    fuel_types = prices[0][1:]

    # Пропускаем метан
    fuel_types = [fuel_type for fuel_type in fuel_types if fuel_type != 'Метан']

    for fuel_type in fuel_types:
        buttons.append(types.KeyboardButton(fuel_type))

    markup.add(*buttons)

    bot.send_message(message.chat.id, "Выберите вид топлива:", reply_markup=markup)

# Обработка нажатий на кнопки с видами топлива
@bot.message_handler(func=lambda message: True)
def handle_fuel_types(message):
    global login, password, last_prices_message_id

    # Проверка наличия аутентификации
    if login != 'admin' or password != 'thegreatestpassword':
        bot.reply_to(message, 'Необходимо пройти аутентификацию. Используйте команду /auth для входа.')
        return

    prices = get_gas_prices()
    fuel_types = prices[0][1:]

    # Пропускаем метан
    fuel_types = [fuel_type for fuel_type in fuel_types if fuel_type != 'Метан']

    if message.text in fuel_types:
        index = fuel_types.index(message.text) + 1
        response = f"<b>Цены на {message.text}:</b>\n"

        for row in prices[1:]:
            response += f"<code>{row[0]} - {row[index]}</code>\n"

        if last_prices_message_id:
            bot.delete_message(message.chat.id, last_prices_message_id)

        sent_message = bot.send_message(message.chat.id, response, parse_mode='HTML')
        last_prices_message_id = sent_message.message_id

# Запуск бота
bot.polling()
