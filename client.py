import socket
import tkinter as tk
from random import randint
import threading

class GameClient:
    def __init__(self, host='127.0.0.1', port=12345):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        self.score = 0
        self.active_circles = []
        self.time_left = 40
        self.other_player_score = 0
        self.is_running = False  # Додайте цей атрибут
        self.receive_thread = threading.Thread(target=self.receive_scores, daemon=True)
        self.receive_thread.start()
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
        self.start_button = tk.Button(self.root, text="Start Game", command=self.start_game)
        self.start_button.pack()
        self.other_player_score_label.pack()
        self.score_label.pack()
        self.canvas.bind('<Motion>', self.check_mouse_position)


        self.root.mainloop()

    def start_game(self):
        self.is_running = True
        self.generate_circles()
        self.start_timer()
        self.client_socket.send(b"PLAYER_READY")

    def generate_circles(self):
        for _ in range(70):
            x, y = randint(50, 750), randint(50, 550)
            circle = self.canvas.create_oval(x-20, y-20, x+20, y+20, fill='blue')
            self.active_circles.append(circle)

    def check_mouse_position(self, event):
        if not self.is_running:
            return
        for circle in self.active_circles:
            coords = self.canvas.coords(circle)
            if coords[0] < event.x < coords[2] and coords[1] < event.y < coords[3]:
                if self.canvas.itemcget(circle, "fill") == "blue":
                    self.canvas.itemconfig(circle, fill="green")
                    self.score_label.config(text=f"Your score: {self.score}")
                    self.score += 1
                    self.send_score()

    def send_score(self):
        score_message = f"Other player's score: {self.score}"
        self.client_socket.send(score_message.encode())

    def receive_scores(self):
        while True:
            try:
                data = self.client_socket.recv(1024)
                if data:
                    decoded_data = data.decode()
                    print(f"Результат іншого гравця: {decoded_data}")
                    if decoded_data.startswith("Other player's score:"):
                        score = decoded_data.split(": ")[1]
                        self.other_player_score = int(score)
                        self.other_player_score_label.config(text=f"Other player's score: {self.other_player_score}")
                    elif decoded_data == "START_GAME":
                        self.is_running = True  # Гра починається, змінюємо статус
                        self.generate_circles()  # Генерація кіл
                        self.start_timer()  # Запуск таймера
                else:
                    break
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
        self.root.quit()
        if self.client_socket:
            self.client_socket.close()

if __name__ == "__main__":
    client = GameClient()
