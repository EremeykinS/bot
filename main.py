import multiprocessing
from bot import Bot
from server import Server

if __name__ == '__main__':
    bot_process = multiprocessing.Process(target=Bot, name='BOT')
    server_process = multiprocessing.Process(target=Server, name='SERVER')
    bot_process.start()
    server_process.start()
