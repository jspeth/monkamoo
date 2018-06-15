#!/usr/bin/env python

import moo
import socketserver

class MonkaMOOServer(socketserver.SocketServer):

    def __init__(self):
        super(MonkaMOOServer, self).__init__()

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

    def on_open(self, client):
        print 'Client Connected'
        self.file = client.makefile()
        self.shell = moo.Shell(stdin=self.file, stdout=self.file)
        self.shell.cmdloop()

    def on_close(self, client):
        print 'Client Disconnected'

def main():
    server = MonkaMOOServer()
    server.run()

if __name__ == '__main__':
    main()
