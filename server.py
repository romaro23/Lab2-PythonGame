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
        self.PLAYER1_TOUR = False
        self.PLAYER2_TOUR = False
        self.PLAYER1_SUM = False
        self.PLAYER2_SUM = False
        self.SUM1 = 0
        self.SUM2 = 0
        print(f"Server started on {host}:{port}")
        self.clients = {}

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr}")
            player_id = len(self.clients) + 1
            self.clients[client_socket] = {'score': 0, 'id': player_id}
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()
            threading.Thread(target=self.start_game).start()
            threading.Thread(target=self.start_tournament).start()
            threading.Thread(target=self.end_tournament).start()

    def start_game(self):
        while True:
            if self.PLAYER1 and self.PLAYER2:
                for client_socket in self.clients:
                    client_socket.send("StartGame".encode())
                    self.PLAYER1 = False
                    self.PLAYER2 = False

    def end_tournament(self):
        while True:
            if self.PLAYER1_SUM and self.PLAYER2_SUM:
                self.choose_tournament_winner()
                self.PLAYER1_SUM = False
                self.PLAYER2_SUM = False

    def start_tournament(self):
        while True:
            if self.PLAYER1_TOUR and self.PLAYER2_TOUR:
                for client_socket in self.clients:
                    client_socket.send("StartTournament".encode())
                    self.PLAYER1_TOUR = False
                    self.PLAYER2_TOUR = False

    def handle_client(self, client_socket):
        player_id = self.clients[client_socket]['id']
        client_socket.send(f"PLAYER_ID:{player_id}".encode())
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                message = data.decode()
                if message == "PLAYER_WON":
                    self.choose_winner(client_socket)
                elif message.isdigit():
                    self.clients[client_socket]['score'] = int(message)
                    self.broadcast_scores(client_socket)
                elif message == "Player 1 ready":
                    self.PLAYER1 = True
                elif message == "Player 2 ready":
                    self.PLAYER2 = True
                elif message == "Player 1 ready for tournament":
                    self.PLAYER1_TOUR = True
                elif message == "Player 2 ready for tournament":
                    self.PLAYER2_TOUR = True
                elif message == "Player ready for round":
                    self.other_ready(client_socket)
                elif message.startswith("Summary of PLAYER1"):
                    self.SUM1 = message.split(":")[1]
                    self.PLAYER1_SUM = True
                elif message.startswith("Summary of PLAYER2"):
                    self.SUM2 = message.split(":")[1]
                    self.PLAYER2_SUM = True
                elif message.startswith("Circles"):
                    circles = message.split(":")[1]
                    self.send_circles(client_socket, circles)
                else:
                    print(f"Received unknown message from Player {player_id}: {message}")

            except Exception as e:
                print(f"Error with Player {player_id}: {e}")
                break

        # client_socket.close()
        # del self.clients[client_socket]  # Видаляємо клієнта зі списку
        # print(f"Connection closed for Player {player_id}")

    def choose_winner(self, sender_socket):
        for client_socket in self.clients:
            if client_socket != sender_socket:
                message = "PLAYER_WON"
                client_socket.send(message.encode())

    def choose_tournament_winner(self):
        if self.SUM1 > self.SUM2:
            winner_id = 1
        elif self.SUM2 > self.SUM1:
            winner_id = 2
        else:
            winner_id = None
        print("Some")
        if winner_id is not None:
            for client_socket, client_info in self.clients.items():
                if client_info['id'] == winner_id:
                    message = "You've won"
                    client_socket.send(message.encode())
                else:
                    message = "You've lost"
                    client_socket.send(message.encode())
        else:
            for client_socket in self.clients:
                client_socket.send("Draw".encode())
    def other_ready(self, sender_socket):
        for client_socket in self.clients:
            if client_socket != sender_socket:
                message = "Other player ready"
                client_socket.send(message.encode())

    def send_circles(self, sender_socket, circles):
        for client_socket in self.clients:
            if client_socket != sender_socket:
                message = f"Circles: {circles}"
                client_socket.send(message.encode())

    def broadcast_scores(self, sender_socket):
        sender_id = self.clients[sender_socket]['id']
        sender_score = self.clients[sender_socket]['score']
        for client_socket in self.clients:
            if client_socket != sender_socket:
                message = f"Player {sender_id} score: {sender_score}"
                client_socket.send(message.encode())


if __name__ == "__main__":
    GameServer()
