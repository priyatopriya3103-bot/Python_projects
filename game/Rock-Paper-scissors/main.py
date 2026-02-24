from package import computer_choice, check_winner, score

#--------------------------------for logging--------------------------------------
import time
import logging
logging.basicConfig(level = logging.INFO, filename = "log.log", filemode = "w",
                    format="%(asctime)s - %(levelname)s - %(message)s" )
#---------------------------------------------------------------------------------
answer = ""
def play_game():
    logging.info("Game initalized")
    s = score()
    choices = ["rock", "paper", "scissors", "exit"]

    print("\n------------ Welcome ------------")
    print("------ Rock Paper Scissors ------")
    while True:
        user = input("\nType rock, paper, scissors or exit: ").lower()

        if user == "exit":
            logging.info("User Exit from the game")
            print("\nFinal Score")
            print("You:", s.user)
            print("Computer:", s.computer)
            print("Thanks for playing 👋")
            break

        if user not in choices:
            logging.error("Inalid input error!")
            print("Invalid input! Try again.")
            continue

        computer = "rock"
        answer=computer
        print(answer)
        print("Computer chose:", computer)

        result = check_winner(user, computer)

        if result == "win":
            logging.info("User wins🎉")
            print("🎉 You win!")
        elif result == "lose":
            logging.info("Computer wins 🎉")
            print("😢 You lose!")
        else:
            logging.info("Draw occured!")
            print("🤝 It's a draw!")
        answer = ""
        s.update(result)

print(answer)
if __name__ == "__main__":
    logging.info("Game called")
    
    play_game()
