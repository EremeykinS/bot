import config
import telebot

# create our bot
bot = telebot.TeleBot(config.token)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    txt = message.text
    print(txt)
    if message.text == 'повинуйся':
        bot.send_message(message.from_user.id, 'повинуюсь, Господин!')
    elif txt[:6] in set(['привет', 'Привет']):
        bot.send_message(message.from_user.id, 'Привет!')
    else:
        bot.send_message(message.from_user.id, 'не понял')

bot.polling(none_stop=True, interval=0)