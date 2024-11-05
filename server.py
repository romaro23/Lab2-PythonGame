import socket
import threading
from traceback import print_tb


class GameServer:
    def __init__(self):
        try:
            host = input("Введіть IP-адресу сервера (наприклад, 127.0.0.1): ")
            port = int(input("Введіть порт сервера (наприклад, 12345): "))
        except:
            host = "127.0.0.1"
            port = 12345
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen()
        self.PLAYER1 = False
        self.PLAYER2 = False
        print(f"Server started on {host}:{port}")
        self.clients = {}  # Зберігаємо клієнтів та їхні рахунки

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr}")
            player_id = len(self.clients) + 1  # Присвоюємо кожному клієнту унікальний ID
            self.clients[client_socket] = {'score': 0, 'id': player_id}
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()
            threading.Thread(target=self.start_game).start()
    def start_game(self):
        a = True
        while a:
            if self.PLAYER1 and self.PLAYER2:
                print("Starting game...")
                a = False
                for client_socket in self.clients:
                    client_socket.send("StartGame".encode())

    def handle_client(self, client_socket):
        player_id = self.clients[client_socket]['id']
        client_socket.send(f"PLAYER_ID:{player_id}".encode())  # Відправляємо ID гравцю

        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                message = data.decode()

                if message == "GAME_OVER":
                    print(f"Game Over signal received from Player {player_id}.")
                    client_socket.send(b"Thank you for playing!")  # Відправка відповіді
                    break  # Вихід з циклу для завершення гри
                elif message.isdigit():
                    # Оновлюємо рахунок гравця на сервері
                    self.clients[client_socket]['score'] = int(message)
                    self.broadcast_scores(client_socket)
                elif message == "PLAYER1_READY":
                    self.PLAYER1 = True
                elif message == "PLAYER2_READY":
                    self.PLAYER2 = True
                else:
                    print(f"Received unknown message from Player {player_id}: {message}")

            except Exception as e:
                print(f"Error with Player {player_id}: {e}")
                break

        client_socket.close()
        del self.clients[client_socket]  # Видаляємо клієнта зі списку
        print(f"Connection closed for Player {player_id}")

    def broadcast_scores(self, sender_socket):
        sender_id = self.clients[sender_socket]['id']
        sender_score = self.clients[sender_socket]['score']
        for client_socket in self.clients:
            if client_socket != sender_socket:
                message = f"Player {sender_id} score: {sender_score}"
                client_socket.send(message.encode())  # Відправляємо рахунок іншому гравцю

if __name__ == "__main__":
    GameServer()
