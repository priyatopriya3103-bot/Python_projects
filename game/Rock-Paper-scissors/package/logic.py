import random

def computer_choice():
    return random.choice(["rock", "paper", "scissors"])


def check_winner(user, computer):
    if user == computer:
        return "draw"
    elif (
        (user == "rock" and computer == "scissors") or
        (user == "paper" and computer == "rock") or
        (user == "scissors" and computer == "paper")
    ):
        return "win"
    else:
        return "lose"


class score:
    def __init__(self):
        self.user = 0
        self.computer = 0

    def update(self, result):
        if result == "win":
            self.user += 1
        elif result == "lose":
            self.computer += 1
