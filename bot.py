import telebot
import config
import requests
import json
from functools import reduce
import lxml.html
from urllib.request import urlretrieve
import sqlite3
from yandex_money.api import Wallet, ExternalPayment
import threading
import decimal
import datetime

class Bot(telebot.TeleBot):
    def __init__(self, queue):
        telebot.TeleBot.__init__(self, config.token)

        self.q = []
        self.to_number = 0
        self.amount = 0

        # main keyboard
        main_kbd = telebot.types.ReplyKeyboardMarkup(True)
        main_kbd.row('\U0001F4B8 Перевод денег', '\U00002139 Информация')
        main_kbd.row('\U0001F4CB Услуги','\U0001F4E2 Почему Яндекс.Деньги?')

        #service keyboard
        ser_kbd = telebot.types.ReplyKeyboardMarkup(True)
        ser_kbd.row('\U0001F694 Проверка штрафов ГИБДД', '\U0001F6CD Акции партнеров')

        #info keyboard
        info_kbd = telebot.types.ReplyKeyboardMarkup(True)
        info_kbd.row('\U0001F916 Информация о боте', '\U0001F4B0 Информация о балансе')
        info_kbd.row('\U0001F4B1 Курсы валют', 'Меню')

        # yes/no keyboard
        yn_kbd = telebot.types.ReplyKeyboardMarkup(True)
        yn_kbd.row('да', 'нет')

        # 300 keyboard
        amount_kbd = telebot.types.ReplyKeyboardMarkup(True)
        amount_kbd.row('100', '300')
        amount_kbd.row('500', '1000')

        # '/start' and '/help' commands handler
        @self.message_handler(commands=['start', 'help'])
        def handle_start_help(message):
            txt = message.text
            print('Получено сообщение: \'', txt, '\' от пользователя ', message.from_user.first_name, '(', message.from_user.id, ')')
            if txt == '/help':
                ans = """Я умею:
<b>Переводить деньги</b> на кошельки
Укажите кошелек,телефон или email. Можете отправить контакт из адресной книжки и мы переведем деньги на кошелек по этому номеру.
<b>Узнавать штрафы ГИБДД</b>
Нужен только номер водительского удотоверения
Сообщать об <b>акциях и предложениях</b> в Яндекс.Деньгах
Покажу весь список со ссылками
Узнавать ваш <b>баланс</b> и рассказывать про <b>курс валют</b>
Только актуальные данные!
А еще Вы можете пройти <b>опрос</b> и узнать о выгодах от использования лично для Вас.
\n
Полезные команды:
чтобы перейти в главное меню введите точку '.'
/help информация о боте
/start начало работы
"""
            if txt == '/start':
                ans = "Выберите действие"
            self.send_message(message.from_user.id, ans, reply_markup=main_kbd, parse_mode='HTML')
            print('Отправлено сообщение: \'', ans, '\' пользователю ', message.from_user.first_name, '(', message.from_user.id, ')')

        # answer to contact
        @self.message_handler(content_types=['contact'])
        def handle_contact(message):
            self.to_number = message.contact.phone_number
            ans = 'Введите сумму к получению'
            kbd = telebot.types.ReplyKeyboardHide(selective=False)
            send_message(message.from_user.id, ans, kbd)
            self.q.append('amount')
        # answer to text
        @self.message_handler(content_types=['text'])
        def handle_text(message):
            #DB connection
            con = sqlite3.connect('/home/user/bot/users.sqlite')
            txt = message.text
            print('Получено сообщение: \'', txt, '\' от пользователя ', message.from_user.first_name, '(', message.from_user.id, ')')
            # if menu stack is empty:
            kbd = main_kbd
            if txt == '.':
                self.q = []
                send_message(message.from_user.id, 'Выберите действие', main_kbd)
                return
            if not self.q:
                if txt == '\U0001F4B8 Перевод денег':
                    ans = 'Введите номер кошелька или номер телефона или e-mail получателя'
                    kbd = telebot.types.ReplyKeyboardHide(selective=False)
                    send_message(message.from_user.id, ans, kbd)
                    self.q.append('to_number')
                elif txt == '\U00002139 Информация':
                    ans = 'О чем Вы хотите узнать?'
                    send_message(message.from_user.id, ans, info_kbd)
                elif txt == '\U0001F4CB Услуги':
                    ans = 'Пожалуйста, выберите услугу'
                    kbd = ser_kbd
                    send_message(message.from_user.id, ans, kbd)
                elif txt == '\U0001F4E2 Почему Яндекс.Деньги?':
                    ans = 'Пройдите наш мини-опрос и узнайте, чем может быть полезен сервис Яндекс.Деньги именно Вам\n\nЧасто ли у Вас возникает чувство, что Вы забыли заплатить за интернет или телефон?'
                    kbd = yn_kbd
                    send_message(message.from_user.id, ans, kbd)
                    self.q.append('q1')
                elif txt == '\U0001F694 Проверка штрафов ГИБДД':
                    ans = 'Введите номер водительского удостоверения'
                    kbd = telebot.types.ReplyKeyboardHide(selective=False)
                    self.q.append('check_penalty')
                    send_message(message.from_user.id, ans, kbd)

                elif txt == '\U0001F6CD Акции партнеров':
                    title_path = '/html/body/div[2]/div[2]/div/div[<i>]/div[<j>]/div/div[1]'
                    img_path = '/html/body/div[2]/div[2]/div/div[<i>]/div[<j>]/a/div/img'
                    url_path = '/html/body/div[2]/div[2]/div/div[<i>]/div[<j>]/a'
                    promo_titles = []
                    promo_img = []
                    promo_url = []
                    r = requests.get('https://money.yandex.ru/promo')
                    for j in range(1,2+1):
                        for i in range(1,3+1):
                            ht = lxml.html.fromstring(r.text)
                            l = ht.xpath(title_path.replace('<i>', str(i)).replace('<j>', str(j)))
                            p = ht.xpath(img_path.replace('<i>', str(i)).replace('<j>', str(j)))
                            url = ht.xpath(url_path.replace('<i>', str(i)).replace('<j>', str(j)))
                            promo_url.append(url[0].values()[4])
                            if promo_url[-1].startswith('http'):
                                ans = l[0].text.replace('\xa0', ' ') + '\n' + url[0].values()[4]
                            else:
                                ans = l[0].text.replace('\xa0', ' ') + '\nhttp://money.yandex.ru' + url[0].values()[4]
                            send_message(message.from_user.id, ans, kbd)
                elif txt == '\U0001F916 Информация о боте':
                    ans = """Я умею:
<b>Переводить деньги</b> на кошельки
Укажите кошелек,телефон или email. Можете отправить контакт из адресной книжки и мы переведем деньги на кошелек по этому номеру.
<b>Узнавать штрафы ГИБДД</b>
Нужен только номер водительского удотоверения
Сообщать об <b>акциях и предложениях</b> в Яндекс.Деньгах
Покажу весь список со ссылками
Узнавать ваш <b>баланс</b> и рассказывать про <b>курс валют</b>
Только актуальные данные!
А еще Вы можете пройти <b>опрос</b> и узнать о выгодах от использования лично для Вас.
\n
Полезные команды:
чтобы перейти в главное меню введите точку '.'
/help информация о боте
/start начало работы
"""
                    kbd = main_kbd
                    send_message(message.from_user.id, ans, kbd)
                elif txt == '\U0001F4B1 Курсы валют':
                    ans = '\U0001F4C5 Данные актуальны на 13.03.2016 ' + str(datetime.datetime.now().time())[:8] + '\n\U0001F4B5 Доллар США\n70,3067 RUB\n\U0001F4B6 Евро\n77.9700 RUB'
                    cur = con.cursor()
                    cur.execute('SELECT token FROM `users` WHERE cid=' + str(message.from_user.id))
                    con.commit()
                    sql_result = cur.fetchall()
                    if sql_result:
                        token = sql_result[0][0]
                        wallet = Wallet(token)
                        b = wallet.account_info()['balance_details']['available']
                        ans += '\nНа имеющиеся на вашем счете ' + str(b) + ' руб. Вы можете купить:\n· ' + str(round(b/70.3067, 2)) + ' долларов США\n· ' + str(round(b/77.97, 2)) + ' евро'
                    send_message(message.from_user.id, ans, info_kbd)
                elif txt == 'Меню':
                    self.q = []
                    send_message(message.from_user.id, 'Выберите действие', main_kbd)
                elif txt == '\U0001F4B0 Информация о балансе':
                    ai = str(account_info(message, con))
                    print('ai = ', ai)
                    print('ai.startswith(\'http\')', ai.startswith('http'))
                    if ai.startswith('Для'):
                        ans = ai
                    else:
                        ans = 'Баланс: ' + ai + ' руб.'
                    kbd = info_kbd
                    send_message(message.from_user.id, ans, kbd)
                else:
                    ans = 'Я не понял, попробуйте что-нибудь другое'
                    send_message(message.from_user.id, ans, kbd)
            else:
                if self.q:
                    cmenu = self.q.pop()
                    if cmenu == 'check_penalty':
                        ans = check_penalty(message)
                        send_message(message.from_user.id, ans, kbd)
                    elif cmenu == 'to_number':
                        self.to_number = message.text
                        ans = 'Введите сумму к получению в рублях'
                        kbd = amount_kbd
                        send_message(message.from_user.id, ans, kbd)
                        self.q.append('amount')
                    elif cmenu == 'q1':
                        if message.text == 'да':
                            ans = 'Вы оплачиваете ЖКУ сами лично?'
                            kbd = yn_kbd
                            send_message(message.from_user.id, ans, kbd)
                            self.q.append('q2')
                        else:
                            ans = 'У Вас есть свой веб-сайт?'
                            kbd = yn_kbd
                            send_message(message.from_user.id, ans, kbd)
                            self.q.append('q3')
                    elif cmenu == 'q3':
                        if message.text == 'да':
                            ans = 'Скорее всего, Вы выглядите как-то так...'
                            kbd = main_kbd
                            send_message(message.from_user.id, ans, kbd)
                            self.send_photo(message.from_user.id, open('/home/user/bot/img/bm.jpg','rb'))
                            ans = '\nВы можете принимать платежи на вашем сайте через <a href="https://kassa.yandex.ru/">Яндекс.Кассу</a>'
                            send_message(message.from_user.id, ans, kbd)
                        else:
                            ans = 'Вы оплачиваете ЖКУ сами лично?'
                            kbd = yn_kbd
                            send_message(message.from_user.id, ans, kbd)
                            self.q.append('q2')
                    elif cmenu == 'q2':
                        if message.text == 'да':
                            ans = 'У Вас есть карта "Тройка"?'
                            kbd = yn_kbd
                            send_message(message.from_user.id, ans, kbd)
                            self.q.append('q4')
                        else:
                            ans = 'У Вас мало времени на досуг?'
                            kbd = yn_kbd
                            send_message(message.from_user.id, ans, kbd)
                            self.q.append('q5')
                    elif cmenu == 'q5':
                        if message.text == 'да':
                            ans = 'Скорее всего, Вы выглядите как-то так...'
                            kbd = main_kbd
                            send_message(message.from_user.id, ans, kbd)
                            self.send_photo(message.from_user.id, open('/home/user/bot/img/work.jpg','rb'))
                            ans = '\nМы понимаем, что у Вас не хватает времени на себя. Именно поэтому, чтобы помочь вам выкроить немного свободного времени, предлагаем удобно оплачивать штрафы ГИБДД, билеты в театр и прочие заказы в несколько кликов'
                            send_message(message.from_user.id, ans, kbd)
                        else:
                            ans = 'Вы когда-либо покупали технику в инетрнет-магазине?'
                            kbd = yn_kbd
                            send_message(message.from_user.id, ans, kbd)
                            self.q.append('q8')
                    elif cmenu == 'q4':
                        if message.text == 'да':
                            ans = 'Вы когда-либо покупали одежду в интернет-магазине?'
                            kbd = yn_kbd
                            send_message(message.from_user.id, ans, kbd)
                            self.q.append('q7')
                        else:
                            ans = 'У Вас есть личное авто?'
                            kbd = yn_kbd
                            send_message(message.from_user.id, ans, kbd)
                            self.q.append('q6')
                    elif cmenu == 'q6':
                        if message.text == 'да':
                            ans = 'У Вас мало времени на досуг?'
                            kbd = yn_kbd
                            send_message(message.from_user.id, ans, kbd)
                            self.q.append('q5')
                        else:
                            ans = 'Вы когда-либо покупали одежду в интернет-магазине?'
                            kbd = yn_kbd
                            send_message(message.from_user.id, ans, kbd)
                            self.q.append('q7')
                    elif cmenu == 'q7' or cmenu == 'q5':
                        if message.text == 'нет':
                            ans = 'Вы когда-либо покупали технику в интернет-магазине?'
                            kbd = yn_kbd
                            send_message(message.from_user.id, ans, kbd)
                            self.q.append('q8')
                    elif cmenu == 'q8':
                        if message.text == 'да':
                            ans = 'Скорее всего, Вы выглядите как-то так...'
                            kbd = main_kbd
                            send_message(message.from_user.id, ans, kbd)
                            self.send_photo(message.from_user.id, open('/home/user/bot/img/student.jpg','rb'))
                            ans = '\nВы молоды и энергичны. Не стоит понапрасну терять время - оплачивайте покупки без отрыва от вашей насыщенной жизни прямо сейчас'
                            send_message(message.from_user.id, ans, kbd)
                        else:
                            ans = 'Скорее всего, Вы выглядите как-то так...'
                            kbd = main_kbd
                            send_message(message.from_user.id, ans, kbd)
                            self.send_photo(message.from_user.id, open('/home/user/bot/img/hw.jpg','rb'))
                            ans = '\nВы явно заботитесь о домашнем очаге. Чтобы принести в дом еще больше уюта, платите легко и узнавайте скидки на <ahref="https://money.yandex.ru/promo/">сайте</a>' 
                            send_message(message.from_user.id, ans, kbd)
                    elif cmenu == 'q7':
                        if message.text == 'нет':
                            ans = 'Скорее всего, Вы выглядите как-то так...'
                            kbd = main_kbd
                            send_message(message.from_user.id, ans, kbd)
                            self.send_photo(message.from_user.id, open('/home/user/bot/img/hw.jpg','rb'))
                            ans = '\nВы явно заботитесь о домашнем очаге. Чтобы принести в дом еще больше уюта, платите легко и узнавайте скидки на <a href="https://money.yandex.ru/promo/">сайте</a>'
                            send_message(message.from_user.id, ans, kbd)
                        else:
                            ans = 'Скорее всего, Вы выглядите как-то так...'
                            kbd = main_kbd
                            send_message(message.from_user.id, ans, kbd)
                            self.send_photo(message.from_user.id, open('/home/user/bot/img/student.jpg','rb'))
                            ans  = '\nВы молоды и энергичны. Не стоит понапрасну терять время - оплачивайте покупки без отрыва от вашей насыщенной жизни прямо сейчас' 
                            send_message(message.from_user.id, ans, kbd)
                    elif cmenu == 'amount':
                        self.amount = round(decimal.Decimal(message.text.replace(',','.')), 2)
                        amount_ = self.amount
                        amount_ = round(decimal.Decimal(message.text.replace(',','.')), 2)
                        total_amount = str(amount_ * decimal.Decimal('1.005'))
                        print(total_amount)
                        if total_amount[total_amount.index('.') + 2] == '5' or total_amount[total_amount.index('.') + 2] == '0':
                            if int(total_amount[total_amount.index('.') + 3]) > 4:
                                amount_ = float(total_amount[:(total_amount.index('.') + 3)]) + 0.01
                                print(1)
                            else:
                                 amount_ = float(total_amount[:(total_amount.index('.') + 3)])
                                 print(0)
                        else:
                            amount_ = round(decimal.Decimal(total_amount), 2)
                            print(2)
                        ans = 'Сумма к оплате с учетом комиссии:' + str(amount_) + '\nПереводим?'
                        kbd = yn_kbd
                        send_message(message.from_user.id, ans, kbd)
                        self.q.append('send')
                    elif cmenu == 'send':
                        if message.text.lower() == 'да':
                            # print('to_number = ', to_number)
                            ans = pay(message, self.to_number, self.amount, con)
                            kbd = main_kbd
                            send_message(message.from_user.id, ans, kbd)
                        else:
                            ans = 'Очень жаль, что Вы не хотите =('
                            kbd = main_kbd
                            send_message(message.from_user.id, ans, kbd)

        def send_message(uid, ans, kbd):
            self.send_message(uid, ans, reply_markup=kbd, parse_mode='HTML')
            print('Отправлено сообщение: \'', ans, '\' пользователю ', uid)

        def account_info(message, con):
            cur = con.cursor()
            cur.execute('SELECT token FROM `users` WHERE cid=' + str(message.from_user.id))
            con.commit()
            sql_result = cur.fetchall()
            if sql_result:
                token = sql_result[0][0]
            else:
                # no user in DB
                return 'Для продолжения перейдите по <a href="http://95.163.114.6/?cid=' + str(message.from_user.id) + '&b=1">ссылке</a>'

            wallet = Wallet(token)
            return wallet.account_info()['balance_details']['available']

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
                    ans = 'Спите спокойно, штрафов нет \U0001F605'
                else:
                    ans = 'Найдено штрафов: ' + str(p_num)
                    for pn, penalty in enumerate(rp):
                        ans += '\n\n' + reduce(lambda x, y: x.replace(y, big_digits[y]), big_digits, str(pn + 1)) + ' информация о штрафе:\n\U0001F4C5 постановление: ' + penalty['BillDate'] + '\n\U0001F4B5 сумма: ' + penalty['TotalAmount'] + ' руб.\n\U0001F556 оплатить до ' + penalty['PayUntil'][:10]
            return ans

        def pay(message, to, amount, con):
            cur = con.cursor()
            cur.execute('SELECT token FROM `users` WHERE cid=' + str(message.from_user.id))
            con.commit()

            sql_result = cur.fetchall()
            if sql_result:
                token = sql_result[0][0]
            else:
                # no user in DB
                return 'Перейдите по <a href="http://95.163.114.6/?cid=' + str(message.from_user.id) + '&to=' + str(self.to_number) + '&amount=' + str(self.amount) + '">ссылке</a>'

            request_options = {"pattern_id": "p2p", "to": self.to_number, "amount_due": self.amount, "comment": "переведено через бота", "message": "переведено через бота", "label": "testPayment"}
            wallet = Wallet(token)
            request_result = wallet.request_payment(request_options)
            print(request_result)
            if 'error' in request_result:
                return 'Произошла ошибка\nВозможно, неверно введен номер или пользователю невозможно отправить перевод'
            else:
                # check status
                process_payment = wallet.process_payment({"request_id": request_result['request_id'],})
                # check result
                if process_payment['status'] == "success":
                    return 'Ваш платеж успешно проведен!'
                else:
                    return 'К сожалению, что-то пошло не так =(\n Платеж не проведен\nМожете попробовать еще раз'

        def check_queue():
            while True:
                if queue:
                    last = queue.get()
                    if 'b' in last:
                        send_message(int(last['cid']), 'Баланс: ' + str(last['b']) + ' руб.', main_kbd)
                    else:
                        if last['result'] == '+':
                            send_message(int(last['cid']), 'Ваш платеж успешно проведен!', main_kbd)
                        else:
                            send_message(int(last['cid']), 'К сожалению, что-то пошло не так =(\n Платеж не проведен\nМожете попробовать еще раз', main_kbd)

        print(self.get_me().username, ' is running!')
        check_queue_thread = threading.Thread(target=check_queue)
        check_queue_thread.daemon = True
        check_queue_thread.start()
        self.polling(none_stop=True, interval=0)

