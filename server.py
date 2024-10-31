import socket
import threading

class GameServer:
    def __init__(self, host='127.0.0.1', port=12345):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen()
        print(f"Server started on {host}:{port}")
        self.clients = []
        self.lock = threading.Lock()  # Додаткова блокування для синхронізації доступу

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr}")
            with self.lock:
                self.clients.append(client_socket)
                if len(self.clients) == 2:
                    self.start_game()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def start_game(self):
        for client in self.clients:
            client.send(b"START_GAME")  # Повідомлення для старту гри

    def handle_client(self, client_socket):
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                message = data.decode()
                if message == "GAME_OVER":
                    print(f"Game Over signal received from {client_socket.getpeername()}.")
                    break
                else:
                    print(f"Received: {message}")
                    self.broadcast_score(message)
            except Exception as e:
                print(f"Error: {e}")
                break
        client_socket.close()
        print(f"Connection closed for {client_socket.getpeername()}")

    def broadcast_score(self, score_message):
        if len(self.clients) == 2:
            for client in self.clients:
                client.send(score_message.encode())

if __name__ == "__main__":
    GameServer()
