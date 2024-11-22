import socket
import time
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from random import randint
import threading
import time


class GameClient:
    def __init__(self):
        self.timer_event = None
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
        self.is_running = False
        self.is_tournament = False
        self.tournament_score = []
        self.tournament_other_player_score = []
        self.summary = 0
        self.is_other_ready = False
        self.tour_number = 0
        self.check_thread = threading.Thread(target=self.check, daemon=True)
        self.check_thread.start()
        self.setup_gui()

    def setup_gui(self):
        self.root = tk.Tk()
        time.sleep(1)
        self.root.title(f"Player {self.player_id}")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(self.root, width=800, height=400)
        self.canvas.grid(row=0, column=0, columnspan=3, padx=5, pady=5)
        self.timer_label = tk.Label(self.root, text=f"Time left: {self.time_left}", font=("Arial", 24))
        self.timer_label.grid(row=1, column=1, pady=5)
        self.score_label = tk.Label(self.root, text=f"Your score: {self.score}", font=("Arial", 24))
        self.score_label.grid(row=1, column=0, padx=5, pady=5)
        self.other_player_score_label = tk.Label(
            self.root, text=f"Other player's score: {self.other_player_score}", font=("Arial", 24)
        )
        self.other_player_score_label.grid(row=2, column=0, padx=5, pady=5)
        self.spinbox = tk.Spinbox(self.root, from_=2, to=100)
        self.spinbox.grid(row=2, column=1, padx=5, pady=5)
        if self.player_id != 1:
            self.spinbox.config(state="disabled")
        self.start_button = tk.Button(self.root, text="Start Game", command=self.send_ready)
        self.start_button.grid(row=1, column=2, padx=5, pady=5)
        self.tournament_button = tk.Button(self.root, text="Start tournament", command=self.start_tournament)
        self.tournament_button.grid(row=2, column=2, padx=5, pady=5)
        self.restart_button = tk.Button(self.root, text="Restart", command=self.restart)
        self.restart_button.grid(row=3, column=2, padx=5, pady=5)
        self.canvas.bind('<Motion>', self.check_mouse_position)
        self.root.mainloop()

    def send_ready(self):
        message = f"Player {self.player_id} ready"
        self.client_socket.send(message.encode())
        self.send_circles()

    def send_ready_round(self):
        message = f"Player ready for round"
        self.client_socket.send(message.encode())

    def send_ready_tour(self):
        message = f"Player {self.player_id} ready for tournament"
        self.client_socket.send(message.encode())
        self.send_circles()

    def send_score(self):
        score_message = self.score.__str__()
        self.client_socket.send(score_message.encode())

    def send_summary(self):
        message = f"Summary of PLAYER{self.player_id}: " + self.summary.__str__()
        self.client_socket.send(message.encode())

    def send_circles(self):
        if self.player_id == 1:
            message = f"Circles: {self.spinbox.get()}"
            self.client_socket.send(message.encode())

    def generate_circles(self):
        n = int(self.spinbox.get())
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        for _ in range(n):
            x, y = randint(20, canvas_width - 20), randint(20, canvas_height - 20)
            circle = self.canvas.create_oval(x - 20, y - 20, x + 20, y + 20, fill='blue')
            self.active_circles.append(circle)

    def clear_circles(self):
        for _ in range(len(self.active_circles)):
            self.canvas.delete(self.active_circles.pop())

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
                    if self.score == len(self.active_circles):
                        if not self.is_tournament:
                            self.stop_timer()
                            print("You've won")
                            self.client_socket.send(b"PLAYER_WON")
                            messagebox.showinfo("", "You have won")
                            self.is_running = False
                        else:
                            self.end_game()

    def check(self):
        while True:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                message = data.decode()
                if message == "StartGame":
                    if not self.is_running:
                        self.start_game()
                if message == "StartTournament":
                    if not self.is_tournament:
                        self.is_tournament = True
                        self.show_table_messagebox()
                if message == "PLAYER_WON" or message == "You've lost":
                    if not self.is_tournament and self.is_running:
                        print("You've lost")
                        self.stop_timer()
                        self.is_running = False
                        messagebox.showinfo("", "You have lost")
                        break
                if not self.is_tournament and message == "You've won" and self.is_running:
                    messagebox.showinfo("", "You have won")
                    self.is_running = False
                    break
                if not self.is_tournament and message == "Draw" and self.is_running:
                    messagebox.showinfo("", "It is draw. There is no winner")
                    self.is_running = False
                    break
                if message.startswith("PLAYER_ID:"):
                    self.player_id = int(message.split(":")[1])
                    print(f"Assigned Player ID: {self.player_id}")
                if message == "Other player ready":
                    self.is_other_ready = True
                if message.startswith("Player "):
                    player_id, score = message.split(" ")[1], message.split(": ")[1]
                    if int(player_id) != self.player_id:
                        self.other_player_score = int(score)
                        self.other_player_score_label.config(
                            text=f"Other player's score: {self.other_player_score}")
                if message.startswith("Circles"):
                    circles = message.split(":")[1]
                    self.spinbox.config(state="normal")
                    self.spinbox.delete(0, "end")
                    self.spinbox.insert(0, circles)
                    self.spinbox.config(state="disabled")
                if self.is_tournament:
                    if message == "You've won":
                        messagebox.showinfo("", "You have won the tournament")
                        self.is_tournament = False
                        break
                    if message == "You've lost":
                        messagebox.showinfo("", "You have lost the tournament")
                        self.is_tournament = False
                        break
                    if message == "Draw":
                        messagebox.showinfo("", "It is draw. There is no winner")
                        self.is_tournament = False
                        break


            except Exception as e:
                print(f"Помилка: {e}")
                break

    def show_table_messagebox(self):
        table_window = tk.Toplevel()
        table_window.title("Results")
        table_window.geometry("300x150")

        table = ttk.Treeview(table_window, columns=("Your score", "Other player's score"), show="headings", height=3)
        table.heading("Your score", text="Your score")
        table.heading("Other player's score", text="Other player's score")
        table.column("Your score", width=120, anchor="center")
        table.column("Other player's score", width=120, anchor="center")
        table.pack(padx=10, pady=10)

        def update_table():
            for row in table.get_children():
                table.delete(row)
            for p1, p2 in zip(self.tournament_score, self.tournament_other_player_score):
                table.insert("", "end", values=(p1, p2))

        update_table()

        timer_label = tk.Label(table_window, text="Закроется через 5 секунд")
        timer_label.pack(pady=5)

        def update_timer(seconds_left):
            if self.is_tournament:
                if seconds_left > 0:
                    timer_label.config(text=f"Time to game: {seconds_left}")
                    table_window.after(1000, update_timer, seconds_left - 1)
                else:
                    if self.tour_number != 3:
                        self.start_game()
                        table_window.destroy()
            else:
                timer_label.pack_forget()

        update_timer(5)

    def start_timer(self):
        if self.time_left > 0:
            self.timer_label.config(text=f"Time left: {self.time_left}")
            self.time_left -= 1
            self.timer_event = self.root.after(1000, self.start_timer)
        else:
            if not self.is_tournament:
                self.stop_timer()
                self.summary = self.score
                self.send_summary()
                self.summary = 0
            else:
                self.end_game()

    def stop_timer(self):
        if hasattr(self, 'timer_event'):
            self.root.after_cancel(self.timer_event)
            del self.timer_event

    def start_tournament(self):
        self.send_ready_tour()
        self.spinbox.config(state="disabled")
        self.start_button.config(state="disabled")
        self.tournament_button.config(state="disabled")

    def start_game(self):
        self.is_running = True
        self.time_left = int(int(self.spinbox.get()) * 0.6)
        self.generate_circles()
        self.start_timer()
        self.spinbox.config(state="disabled")
        self.start_button.config(state="disabled")
        self.tournament_button.config(state="disabled")

    def wait_for_other_player_ready(self):
        if self.is_other_ready:
            self.handle_tournament_round()
        else:
            self.root.after(1000, self.wait_for_other_player_ready)

    def handle_tournament_round(self):
        if self.tour_number < 3:
            self.tournament_score.append(self.score)
            self.tournament_other_player_score.append(self.other_player_score)
            self.show_table_messagebox()
            self.clear_circles()
            self.score = 0
            self.other_player_score = 0
            self.tour_number += 1
            self.is_other_ready = False

    def end_game(self):
        self.stop_timer()
        if self.is_tournament and self.tour_number < 2:
            self.send_ready_round()
            self.wait_for_other_player_ready()
        else:
            self.handle_tournament_round()
            for s in self.tournament_score:
                self.summary += s
            self.send_summary()
            self.summary = 0
        self.is_running = False
        # if self.client_socket:
        #     self.client_socket.send(b"GAME_OVER")
        # if self.client_socket:
        #     self.client_socket.close()

    def restart(self):
        if self.player_id == 1:
            self.spinbox.config(state="normal")
        self.start_button.config(state="normal")
        self.tournament_button.config(state="normal")
        self.clear_circles()
        self.score = 0
        self.other_player_score = 0
        self.stop_timer()
        self.tour_number = 0
        self.tournament_score.clear()
        self.tournament_other_player_score.clear()
        self.is_other_ready = False
        self.check_thread = threading.Thread(target=self.check, daemon=True)
        self.check_thread.start()


if __name__ == "__main__":
    client = GameClient()