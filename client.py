import socket
import tkinter as tk
from random import randint
import threading


class GameClient:
    def __init__(self):
        try:
            host = input("Введіть IP-адресу сервера (наприклад, 127.0.0.1): ")
            port = int(input("Введіть порт сервера (наприклад, 12345): "))
        except:
            host = "127.0.0.1"
            port = 12345
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        self.score = 0
        self.player_id = None
        self.active_circles = []
        self.time_left = 0
        self.other_player_score = 0
        self.is_running = False  # Додайте цей атрибут
        self.receive_thread = threading.Thread(target=self.receive_scores, daemon=True)
        self.check_thread = threading.Thread(target=self.check_start, daemon=True)
        self.receive_thread.start()
        self.check_thread.start()
        self.setup_gui()

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Game Client")

        self.canvas = tk.Canvas(self.root, width=800, height=600)
        self.canvas.pack()
        self.timer_label = tk.Label(self.root, text=f"Time left: {self.time_left}", font=("Arial", 24))
        self.timer_label.pack()
        self.score_label = tk.Label(self.root, text=f"Your score: {self.score}",
                                    font=("Arial", 24))
        self.other_player_score_label = tk.Label(self.root, text=f"Other player's score: {self.other_player_score}",
                                                 font=("Arial", 24))
        self.spinbox = tk.Spinbox(self.root, from_=2, to=100)
        self.spinbox.pack()
        self.start_button = tk.Button(self.root, text="Start Game", command=self.send_ready)
        self.start_button.pack()
        self.other_player_score_label.pack()
        self.score_label.pack()
        self.canvas.bind('<Motion>', self.check_mouse_position)

        self.root.mainloop()
    def send_ready(self):
        self.client_socket.send(b"PLAYER1_READY")
    def start_game(self):
        self.is_running = True
        self.time_left = int(int(self.spinbox.get()) * 0.6)
        self.generate_circles()
        self.start_timer()

    def generate_circles(self):
        n = int(self.spinbox.get())
        for _ in range(n):
            x, y = randint(50, 750), randint(50, 550)
            circle = self.canvas.create_oval(x - 20, y - 20, x + 20, y + 20, fill='blue')
            self.active_circles.append(circle)

    def check_mouse_position(self, event):
        if not self.is_running:
            return
        for circle in self.active_circles:
            coords = self.canvas.coords(circle)
            if coords[0] < event.x < coords[2] and coords[1] < event.y < coords[3]:
                if self.canvas.itemcget(circle, "fill") == "blue":
                    self.canvas.itemconfig(circle, fill="green")
                    self.score += 1
                    self.score_label.config(text=f"Your score: {self.score}")
                    self.send_score()

    def send_score(self):
        score_message = self.score.__str__()
        self.client_socket.send(score_message.encode())

    def check_start(self):
        a = True
        while a:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                message = data.decode()
                if message == "StartGame":
                    if not self.is_running:
                        print("Starting game...")
                        a = False
                        self.start_game()
            except Exception as e:
                print(f"Помилка: {e}")
                break

    def receive_scores(self):
        while True:
            try:
                data = self.client_socket.recv(1024).decode()
                if data.startswith("PLAYER_ID:"):
                    self.player_id = int(data.split(":")[1])
                    print(f"Assigned Player ID: {self.player_id}")
                elif data.startswith("Player "):
                    player_id, score = data.split(" ")[1], data.split(": ")[1]
                    if int(player_id) != self.player_id:
                        self.other_player_score = int(score)
                        self.other_player_score_label.config(
                            text=f"Other player's score: {self.other_player_score}")

            except Exception as e:
                print(f"Помилка: {e}")
                break

    def start_timer(self):
        if self.time_left > 0:
            self.timer_label.config(text=f"Time left: {self.time_left}")
            self.time_left -= 1
            self.root.after(1000, self.start_timer)
        else:
            self.end_game()

    def end_game(self):
        self.is_running = False  # Завершення гри
        if self.client_socket:
            self.client_socket.send(b"GAME_OVER")
        if self.client_socket:
            self.client_socket.close()


if __name__ == "__main__":
    client = GameClient()