import telebot
import config
import requests
import json
from functools import reduce


class Bot(telebot.TeleBot):
    def __init__(self, queue):
        telebot.TeleBot.__init__(self, config.token)

        self.q = []

        # main keyboard
        main_kbd = telebot.types.ReplyKeyboardMarkup()
        # markup.row('/start', '/help')
        main_kbd.row('\U0001F4B8 перевести деньги', '\U00000030\U000020E3 что-нибудь еще')
        main_kbd.row('\U0001F694 проверить штрафы', '\U0001F6CD посмотреть акции')

        # '/start' and '/help' commands handler
        @self.message_handler(commands=['start', 'help'])
        def handle_start_help(message):
            txt = message.text
            print('Получено сообщение: \'', txt, '\' от пользователя ', message.from_user.first_name, '(', message.from_user.id, ')')
            if txt == '/help':
                ans = "Пока бот умеет\n\U0001F694 проверять штрафы\nБот работает на " + str(config.machine) + ".\n"
            if txt == '/start':
                ans = "Бот готов поработать для тебя, " + message.from_user.first_name + '! Выбири действие...'
            self.send_message(message.from_user.id, ans, reply_markup=main_kbd)
            print('Отправлено сообщение: \'', ans, '\' пользователю ', message.from_user.first_name, '(', message.from_user.id, ')')

        # wait for POST
        @self.message_handler(commands=['post'])
        def wait_POST(message):
            queue.put(message.from_user.id)
            self.send_message(message.from_user.id, 'Waiting for POST...')
            item = queue.get()
            self.send_message(message.from_user.id, 'We received it:\'' + str(item) + '\'!')

        # answer
        @self.message_handler(content_types=['text'])
        def handle_text(message):
            txt = message.text
            print('Получено сообщение: \'', txt, '\' от пользователя ', message.from_user.first_name, '(', message.from_user.id, ')')
            # if stack is empty:
            kbd = main_kbd
            if not self.q:
                if txt[:9].lower() == 'повинуйся':
                    ans = 'повинуюсь тебе, ' + message.from_user.first_name + '!'
                elif 'пошел' in txt.lower().split() or 'пошёл' in txt.lower().split() or 'иди' in txt.lower().split():
                    ans = 'Очень по-взрослому, посылать бота...'
                elif txt[:6].lower() == 'привет':
                    ans = 'Привет!'
                elif txt == '\U0001F4B8 перевести деньги':
                    ans = 'Эту функцию делает Даша!'
                elif txt == '\U0001F467 что-нибудь еще':
                    ans = 'Это только для VIP-пользователей!'
                elif txt == '\U0001F694 проверить штрафы':
                    ans = 'Введите номер водительского удостоверения'
                    kbd = telebot.types.ReplyKeyboardHide(selective=False)
                    self.q.append('check_penalty')
                elif txt == '\U0001F6CD посмотреть акции':
                    ans = 'Эту функцию делает Паша!'
                else:
                    ans = 'Бот не гений. Он не понял.'
            elif self.q.pop() == 'check_penalty':
                ans = check_penalty(message)
            self.send_message(message.from_user.id, ans, reply_markup=kbd)
            print('Отправлено сообщение: \'', ans, '\' пользователю ', message.from_user.first_name, '(', message.from_user.id, ')')

        def check_penalty(message):
            txt = message.text
            big_digits = {str(i): str(i)+'\U000020E3' for i in range(10)}
            data = {'action': 'checkDebts', 'driverLicense': txt}
            r = requests.post('https://money.yandex.ru/debts/index.xml', data)
            rp = json.loads(r.text)
            if rp['status'] == 'error':
                ans = '\U000026A0 Произошла ошибка. Возможно, Вы ввели неверный номер.'
            else:
                p_num = len(rp['data'])
                rp = rp['data']
                if p_num == 0:
                    ans = 'Спи спокойно, штрафов нет \U0001F605'
                else:
                    ans = 'Найдено штрафов: ' + str(p_num)
                    for pn, penalty in enumerate(rp):
                        ans += '\n\n' + reduce(lambda x, y: x.replace(y, big_digits[y]), big_digits, str(pn + 1)) + ' информация о штрафе:\n\U0001F4C5 постановление: ' + penalty['BillDate'] + '\n\U0001F4B5 сумма: ' + penalty['TotalAmount'] + ' руб.\n\U0001F556 оплатить до ' + penalty['PayUntil'][:10]
            return ans

        print(self.get_me().username, ' is running!')
        self.polling(none_stop=True, interval=0)
