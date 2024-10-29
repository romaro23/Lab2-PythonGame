import socket
import threading


class GameServer:
    def __init__(self, host='127.0.0.1', port=12345):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen()
        print(f"Server started on {host}:{port}")

        self.clients = []
        self.scores = {}  # Зберігання рахунків гравців

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr}")
            self.clients.append(client_socket)
            print("Додано гравця")
            self.scores[client_socket] = 0  # Ініціалізація рахунку гравця
            threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()

    def handle_client(self, client_socket, addr):
        while True:
            try:
                data = client_socket.recv(1024)

                if not data:
                    break
                message = data.decode()
                if message == "GAME_OVER":
                    print(f"Game Over signal received from {addr}.")
                    client_socket.send(b"Thank you for playing!")  # Відправка відповіді
                    break  # Вихід з циклу для завершення гри
                else:
                    print(f"Received: {message} from {addr}")
                    # Оновлення рахунку гравця
                    self.scores[client_socket] += 1
                    self.broadcast_scores()  # Відправка всім рахунків

            except Exception as e:
                print(f"Error: {e}")
                break

        # Закриваємо сокет тільки після завершення циклу
        self.clients.remove(client_socket)
        del self.scores[client_socket]  # Видалення рахунку гравця
        client_socket.close()
        print(f"Connection closed for {addr}")

    def broadcast_scores(self):
        for client in self.clients:
            try:
                score_message = f"Other player's score: {self.scores[client]}"
                client.send(score_message.encode())
            except Exception as e:
                print(f"Error sending to client: {e}")


if __name__ == "__main__":
    GameServer()
