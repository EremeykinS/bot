import telebot
import config


class Bot(telebot.TeleBot):
    def __init__(self):
        telebot.TeleBot.__init__(self, config.token)
        self.run()

    def run(self):
        # keyboard markup
        markup = telebot.types.ReplyKeyboardMarkup()
        markup.row('/start', '/help')
        markup.row('Привет!', 'Повинуйся!')

        # '/start' and '/help' commands handler
        @self.message_handler(commands=['start', 'help'])
        def handle_start_help(message):
            txt = message.text
            print('Получено сообщение: \'', txt, '\' от пользователя ', message.from_user.first_name, '(', message.from_user.id, ')')
            if txt == '/start':
                ans = "They call me GodMoneyBot, I will help you to blow your money.\nNow the bot is running on the " + str(config.machine) + ".\nThis commands can help us:\n/help - get a manual about me\n/something - get something from me"
            if txt == '/help':
                ans = "Here is no manual! Who need boring manuals?"
            self.send_message(message.from_user.id, ans, reply_markup=markup)
            print('Отправлено сообщение: \'', ans, '\' пользователю ', message.from_user.first_name, '(', message.from_user.id, ')')

        # answer
        @self.message_handler(content_types=['text'])
        def handle_text(message):
            txt = message.text
            print('Получено сообщение: \'', txt, '\' от пользователя ', message.from_user.first_name, '(', message.from_user.id, ')')
            if txt[:9].lower() == 'повинуйся':
                ans = 'повинуюсь тебе, ' + message.from_user.first_name + '!'
            elif 'пошел' in txt.lower().split() or 'пошёл' in txt.lower().split() or 'иди' in txt.lower().split():
                ans = 'Очень по-взрослому, посылать бота...'
            elif txt[:6].lower() == 'привет':
                ans = 'Привет!'
            else:
                ans = 'не понял'
            self.send_message(message.from_user.id, ans, reply_markup=markup)
            print('Отправлено сообщение: \'', ans, '\' пользователю ', message.from_user.first_name, '(', message.from_user.id, ')')
        print(self.get_me().username, ' is running!')
        self.polling(none_stop=True, interval=0)
