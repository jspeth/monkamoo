#!/usr/bin/env python

import socket
import thread

import moo

class MonkaMOOServer(socket.socket):
    clients = []

    def __init__(self):
        socket.socket.__init__(self)
        # silence address occupied
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
            print 'Server closed'
            for client in self.clients:
                client.close()
            self.close()

    def accept_clients(self):
        while 1:
            (clientsocket, address) = self.accept()
            # Adding client to clients list
            self.clients.append(clientsocket)
            # Client Connected
            self.on_open(clientsocket)
            # Receiving data from client
            thread.start_new_thread(self.receive, (clientsocket,))

    def receive(self, client):
        while 1:
            data = client.recv(1024)
            if data == '':
                break
            # Message Received
            self.on_message(client, data)
        # Removing client from clients list
        self.clients.remove(client)
        # Client Disconnected
        self.on_close(client)
        # Closing connection with client
        client.close()
        # Closing thread
        thread.exit()
        print self.clients

    def on_open(self, client):
        print 'Client Connected'
        self.file = client.makefile()
        self.shell = moo.Shell(stdin=self.file, stdout=self.file)
        self.shell.cmdloop()

    def on_close(self, client):
        print 'Client Disconnected'

    def on_message(self, client, message):
        print 'Client Sent Message: '' + `message` + '''
        if message[-1] == '\n':
            message = message[:-1]
        if message[-1] == '\r':
            message = message[:-1]
        args = message.split(' ')
        try:
            moo.cli.main(args, standalone_mode=False)
        except Exception as ex:
            print 'Error:', `ex`
