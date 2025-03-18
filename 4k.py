import socket
import threading
import json

# Server configuration
HOST = '127.0.0.1'  # Localhost for testing
PORT = 6464  # Super Mario 64 port
BUFFER_SIZE = 1024

# Imaginary Mega-Connector server
class MegaConnectorServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen()
        self.cartridge_data = {}  # Dictionary to store personalized data for each cartridge

        print(f"Mega-Connector server started on {HOST}:{PORT}")

    def handle_client(self, client_socket, address):
        print(f"New connection from {address}")

        try:
            while True:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break

                request = json.loads(data.decode())
                cartridge_id = request.get('cartridge_id')

                if not cartridge_id:
                  print("Invalid request: Missing cartridge ID")
                  continue # Skip to the next iteration

                if request['action'] == 'get_data':
                    self.send_cartridge_data(client_socket, cartridge_id)
                elif request['action'] == 'save_data':
                    self.save_cartridge_data(cartridge_id, request['data'])
                else:
                    print("Invalid request action")
                    
        except json.JSONDecodeError:
            print(f"Invalid JSON data received from {address}")

        finally:
            print(f"Connection closed with {address}")
            client_socket.close()


    def send_cartridge_data(self, client_socket, cartridge_id):
        data = self.cartridge_data.get(cartridge_id, {})
        response = {'data': data}
        client_socket.sendall(json.dumps(response).encode())


    def save_cartridge_data(self, cartridge_id, data):
        self.cartridge_data[cartridge_id] = data
        print(f"Saved data for cartridge {cartridge_id}")


    def start(self):
        while True:
            client_socket, address = self.server_socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
            client_thread.start()


if __name__ == "__main__":
    server = MegaConnectorServer()
    server.start()
