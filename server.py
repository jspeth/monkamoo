#!/usr/bin/env python

import socket
import thread

import moo

class MonkaMOOServer(socket.socket):
    clients = []

    def __init__(self):
        socket.socket.__init__(self)
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind(('0.0.0.0', 8888))
        self.listen(5)

    def run(self):
        print 'Server started on port 8888'
        try:
            self.accept_clients()
        except Exception as ex:
            print ex
        finally:
            print 'Server Closed'
            for client in self.clients:
                client.close()
            self.close()

    def accept_clients(self):
        while 1:
            (conn, address) = self.accept()
            print 'Client Connected: ' + `address`
            self.clients.append(conn)
            thread.start_new_thread(self.run_shell, (conn,))

    def run_shell(self, conn):
        # run shell command loop
        client_file = conn.makefile()
        shell = moo.Shell(stdin=client_file, stdout=client_file)
        shell.cmdloop()
        # JGS - ctrl-d / quit not working
        # close connection
        self.clients.remove(conn)
        conn.close()
        thread.exit()
