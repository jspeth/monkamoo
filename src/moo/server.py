import socket
import threading

from . import shell

class MonkaMOOServer(socket.socket):
    clients = []

    def __init__(self, world):
        socket.socket.__init__(self)
        self.world = world
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind(('0.0.0.0', 8888))
        self.listen(5)

    def run(self):
        print('Server started on port 8888')
        try:
            self.accept_clients()
        except Exception as ex:
            print(ex)
        finally:
            print('Server Closed')
            for client in self.clients:
                client.close()
            self.close()

    def accept_clients(self):
        while 1:
            (conn, address) = self.accept()
            print('Client Connected: ' + repr(address))
            self.clients.append(conn)
            threading.Thread(target=self.run_shell, args=(conn,)).start()

    def run_shell(self, conn):
        # run shell command loop
        client_file = conn.makefile(mode='rw')
        client_shell = shell.Shell(self.world, stdin=client_file, stdout=client_file)
        client_shell.cmdloop()
        # JGS - ctrl-d / quit not working
        # close connection
        self.clients.remove(conn)
        conn.close()
        threading.Thread.exit()
