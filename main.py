import multiprocessing
from bot import Bot
from server import Server

if __name__ == '__main__':
    q = multiprocessing.JoinableQueue()
    bot_process = multiprocessing.Process(target=Bot, args=(q,), name='BOT')
    server_process = multiprocessing.Process(target=Server, args=(q,), name='SERVER')
    bot_process.start()
    server_process.start()
    q.join()

