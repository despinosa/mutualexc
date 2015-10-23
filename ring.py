#! -*- coding: UTF-8 -*-

from socket import AF_INET, SO_REUSEADDR, SOCK_STREAM, SOL_SOCKET, \
gethostname, socket
from sys import argv, getsizeof
from threading import Lock, Thread

TOKEN = 'tok'

class Process(Thread):
    """Proceso del sistema distribuido. Al ejecutarse, transmite el
    token conforme al algoritmo de anillo. A la vez, pregunta
    constantemente si se requiere el acceso a la región crítica.
    De requerirse, bloquea el token la próxima vez que lo tenga hasta
    que termine.

    """

    def __init__(self, next_addr, port, has_token=False):
        super(Process, self).__init__()
        if not has_token:
            self.next = socket(AF_INET, SOCK_STREAM)
            self.next.connect(next_addr)
            print 'conectado a siguiente en {}'.format(next_addr)
        server = socket(AF_INET, SOCK_STREAM)
        server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        server.bind((gethostname(), port))
        server.listen(0)
        self.previous, previous_addr = server.accept()
        print 'anterior conectado desde {}'.format(previous_addr)
        self.lock = Lock()
        self.lock.acquire(False)
        if has_token:
            raw_input('enter para conectar ')
            self.next = socket(AF_INET, SOCK_STREAM)
            self.next.connect(next_addr)
            print 'conectado a siguiente en {}'.format(next_addr)
            self.lock.release()
        self.stopped = False

    def work(self):
        while not self.stopped:
            answer = raw_input('¿necesito región crítica? (y/n/x) ')
            if answer in 'yYsS':
                with self.lock:
                    raw_input('enter para liberar ')
            elif answer in 'xX':
                self.stopped = True

    def algorithm(self):
        while not self.stopped:
            if not self.lock.acquire(False):
                token = self.previous.recv(getsizeof(TOKEN))
                assert token == TOKEN
            self.lock.release()
            self.lock.acquire()
            self.next.send(TOKEN)

    def run(self):
        work_thread = Thread(target=self.work)
        algorithm_thread = Thread(target=self.algorithm)
        work_thread.start()
        algorithm_thread.start()
        work_thread.join()
        algorithm_thread.join()
        self.next.close()
        self.previous.close()


if __name__ == '__main__':
    next_addr = argv[2].split(':', 1)
    next_addr[1] = int(next_addr[1])
    if len(argv) > 3:
        p = Process(tuple(next_addr), int(argv[1]), True)
    else:
        p = Process(tuple(next_addr), int(argv[1]))
    p.start()
    p.join()
