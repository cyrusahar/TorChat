import socket
import threading
import binascii

HOST = input('Enter Host (default: 127.0.0.1): ')
if not HOST.strip():
    HOST = "127.0.0.1"

PORT = input('(default: 8080) PORT: ')
if not PORT.strip():
    PORT = 8080
else:
    PORT = int(PORT)

MAX_CLIENTS = input('How many can join (default: 10): ')
if not MAX_CLIENTS.strip():
    MAX_CLIENTS = 10
else:
    MAX_CLIENTS = int(MAX_CLIENTS)

BUFFER_SIZE = 1024


class ChatServer:
    '''
    Class for chat server
    '''
    def __init__(self, host, port):
        print("Initializing server...")
        self.all_users = []
        # Create socket and listen for new connections
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen(MAX_CLIENTS)
        print("Server: OK")
        print("Started")

    def run(self):
        '''
        Function for receiving new connections
        and creating threads to handle clients.
        '''
        while True:
            conn, addr = self.sock.accept()
            tr = threading.Thread(
                target=self.client_handler,
                args=(conn,)
            )
            tr.daemon = True
            tr.start()

    def client_handler(self, conn):
        '''
        Function for handling new connections
        '''
        try:
            # First message is client name
            name = conn.recv(BUFFER_SIZE)
            try:
                name = binascii.a2b_uu(name).decode()
            except binascii.Error:
                print("Invalid name received, decoding as plain text")
                name = name.decode('utf-8', errors='replace')
            
            print(f"{name} joined")
            hello_string = f"Hello, {name}. Users online: {len(self.all_users)}"
            conn.sendall(binascii.b2a_uu(hello_string.encode()))
            self.all_users.append((conn, name))
            self.send_message_to_others((conn, name), f"{name} entered the chat!")

            # Infinite loop for receiving messages from client
            while True:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    break
                try:
                    data = binascii.a2b_uu(data).decode()
                except binascii.Error:
                    print("Invalid message received, decoding as plain text")
                    data = data.decode('utf-8', errors='replace')
                self.send_message_to_others((conn, name), data)

            # Client left the chat
            conn.sendall(b'Bye')
            self.send_message_to_others((conn, name), f"{name} left the chat!")
            self.delete_user(conn)
        except Exception as e:
            print(f"Error in client handler: {e}")
        finally:
            conn.close()

    def delete_user(self, del_user):
        '''
        Function for deleting a client from the list of all_users
        '''
        self.all_users = [user for user in self.all_users if user[0] != del_user]

    def send_message_to_others(self, from_user, message):
        '''
        Function for sending a message to all clients except the sender
        '''
        if len(self.all_users) > 1:
            for user in self.all_users:
                if user[0] != from_user[0]:
                    msg = f"{from_user[1]}: {message}"
                    try:
                        user[0].sendall(binascii.b2a_uu(msg.encode()))
                    except Exception as e:
                        print(f"Error sending message: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, tb):
        print("Server is going down.")
        self.sock.close()


with ChatServer(HOST, PORT) as chat:
    chat.run()
