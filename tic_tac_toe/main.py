import tkinter as tk
from tkinter import messagebox

# ---------- PROGRAM ----------
def reset_game():
    """Reset the board for a new game"""
    global current_player, winner
    for button in buttons:
        button.config(text="", bg="SystemButtonFace")
    current_player = "X"
    winner = False
    label.config(text=f"Player {current_player}'s turn")

def check_winner():
    """Check if a player has won or if it's a tie"""
    global winner
    winning_combinations = [
        (0,1,2), (3,4,5), (6,7,8),
        (0,3,6), (1,4,7), (2,5,8),
        (0,4,8), (2,4,6)
    ]
    

    for combo in winning_combinations:
        if buttons[combo[0]]["text"] == buttons[combo[1]]["text"] == buttons[combo[2]]["text"] != "":
            buttons[combo[0]].config(bg="green")
            buttons[combo[1]].config(bg="green")
            buttons[combo[2]].config(bg="green")
            winner = True
            replay = messagebox.askyesno(
                "Tic-Tac-Toe", 
                f"Player {buttons[combo[0]]['text']} wins!\nDo you want to play again?"
            )
            if replay:
                reset_game()
            return

    

    if all(button["text"] != "" for button in buttons) and not winner:
        winner = True
        replay = messagebox.askyesno("Tic-Tac-Toe", "It's a tie!\nDo you want to play again?")
        if replay:
            reset_game()


def button_click(index):
    """Handle a button click"""
    if buttons[index]["text"] == "" and not winner:
        buttons[index]["text"] = current_player
        check_winner()
        toggle_player()


def toggle_player():
    """Switch turns between X and O"""
    global current_player
    current_player = "O" if current_player == "X" else "X"
    label.config(text=f"Player {current_player}'s turn")


root = tk.Tk()
root.title("Tic-Tac-Toe")

current_player = "X"
winner = False


buttons = [
    tk.Button(root, text="", font=("normal", 25), width=6, height=2, 
              command=lambda i=i: button_click(i)) for i in range(9)
]


for i, button in enumerate(buttons):
    button.grid(row=i//3, column=i%3)


label = tk.Label(root, text=f"Player {current_player}'s turn", font=("normal",16))
label.grid(row=3, column=0, columnspan=3)


root.mainloop()
