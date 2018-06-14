import socket
import thread

class SocketServer(socket.socket):
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

    def broadcast(self, message):
        # Sending message to all clients
        for client in self.clients:
            client.send(message)

    def on_open(self, client):
        pass

    def on_message(self, client, message):
        pass

    def on_close(self, client):
        pass
