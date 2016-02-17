import config
import telebot

# create our bot
bot = telebot.TeleBot(config.token)

# '/start' and '/help' commands handler
@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    txt = message.text
    print('Получено сообщение: \'', txt,'\' от пользователя ', message.from_user.id)
    if txt == '/start':

        ans = """
        They call me GodMoneyBot, I will help you to blow your money.

        This commands can help us:

        /help - get a manual about me
        /something - get something from me
        """
    if txt == '/help':
        ans ="""
        Here is no manual!
        Who needs boring manuals?
        """
    bot.send_message(message.from_user.id, ans)
    print('Отправлено сообщение: \'', ans, '\' пользователю ', message.from_user.id)


# answer
@bot.message_handler(content_types=['text'])
def handle_text(message):
    txt = message.text
    print('Получено сообщение: \'', txt,'\' от пользователя ', message.from_user.id)
    if txt[:9].lower() =='повинуйся':
        ans = 'повинуюсь, Господин!'
    elif txt[:6].lower() == 'привет':
        ans = 'Привет!'
    else:
        ans = 'не понял'
    bot.send_message(message.from_user.id, ans)
    print('Отправлено сообщение: \'', ans, '\' пользователю ', message.from_user.id)

# run forever
bot.polling(none_stop=True, interval=0)