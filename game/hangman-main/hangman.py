import random
import time
import os
from hangman_art import logo
from hangman_words import categories  

LEADERBOARD_FILE = "top5_leaderboard.txt"

# ---------------- Leaderboard Functions ----------------
def load_leaderboard():
    leaderboard = []
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, "r") as file:
            for line in file:
                parts = line.strip().split(",")
                if len(parts) == 3:  # prevent crash from bad lines
                    name, word, time_sec = parts
                    leaderboard.append((name, word, int(time_sec)))
    return leaderboard


def save_leaderboard(leaderboard):
    with open(LEADERBOARD_FILE, "w") as file:
        for name, word, time_sec in leaderboard:
            file.write(f"{name},{word},{time_sec}\n")


def update_leaderboard(name, word, elapsed_time, leaderboard):
    leaderboard.append((name, word, elapsed_time))
    leaderboard = sorted(leaderboard, key=lambda x: x[2])[:5]
    save_leaderboard(leaderboard)
    return leaderboard


def display_leaderboard(leaderboard):
    if not leaderboard:
        print("\n🏆 No fastest wins yet!")
        return

    print("\n🏆 Top 5 Fastest Wins:")
    for i, (name, word, t) in enumerate(leaderboard, 1):
        print(f"{i}. {name} - {word} in {t} seconds")


# ---------------- Game Function ----------------
def play_game(total_score=0, leaderboard=None):

    if leaderboard is None:
        leaderboard = []

    all_words = []
    all_hints = []
    all_categories = []

    for cat_name, cat_data in categories.items():
        all_words += cat_data["words"]
        all_hints += cat_data["hints"]
        all_categories += [cat_name] * len(cat_data["words"])

    index = random.randint(0, len(all_words) - 1)
    chosen_word = all_words[index]
    chosen_category = all_categories[index]
    second_hint = all_hints[index]

    lives = 6
    score = total_score
    end_of_game = False
    display = ["_"] * len(chosen_word)
    guessed_letters = []

    print(logo)
    print("\nRules for this Game:")
    print("👉 You have 6 lives.")
    print("👉 Type a letter to guess.")
    print("👉 Type 'hint' for a hint (costs 1 point).")
    print("👉 Don't repeat letters!")
    print(chosen_word)

    start_time = time.time()
    player_name = input("Enter your name: ")

    hint_count = 0

    while not end_of_game:
        guess = input("\nGuess a letter (or type 'hint'): ").lower()

        # -------- HINT SYSTEM --------
        if guess == "hint":
            if hint_count == 0:
                print(f"Hint 1: Category is '{chosen_category}'")
            elif hint_count == 1:
                print(f"Hint 2: {second_hint}")
            else:
                print("No more hints available!")

            score -= 1
            hint_count += 1
            print(f"Score: {score}")
            continue

        if guess in guessed_letters:
            print(f"You've already guessed '{guess}'.")
            continue

        guessed_letters.append(guess)

        # -------- CHECK LETTER --------
        if guess in chosen_word:
            for i in range(len(chosen_word)):
                if chosen_word[i] == guess:
                    display[i] = guess
                    score += 1
        else:
            lives -= 1
            score -= 2
            print(f"You guessed '{guess}', that's not in the word. {'❤️ ' * lives} lives remaining.")

        print(f"{' '.join(display)}")
        print(f"Score: {score}")
        print(f"Used letters: {', '.join(guessed_letters)}")

        # -------- WIN CHECK --------
        if "_" not in display:
            end_of_game = True
            score += 5
            end_time = time.time()
            elapsed_time = int(end_time - start_time)

            print(f"\n🎉 You Won! Word: '{chosen_word}' | Score: {score}")
            print(f"⏱ Completed in {elapsed_time} seconds!")

            leaderboard = update_leaderboard(player_name, chosen_word, elapsed_time, leaderboard)

        # -------- LOSE CHECK --------
        if lives == 0:
            end_of_game = True
            end_time = time.time()
            elapsed_time = int(end_time - start_time)

            print(f"\n💀 You Lose! Word was '{chosen_word}' | Score: {score}")
            print(f"⏱ You played for {elapsed_time} seconds!")

    return score, leaderboard


# ---------------- Main Loop ----------------
total_score = 0
leaderboard = load_leaderboard()

while True:
    total_score, leaderboard = play_game(total_score, leaderboard)
    display_leaderboard(leaderboard)

    play_again = input("\nDo you want to play again? (y/n): ").lower()
    if play_again != 'y':
        print(f"\nThanks for playing! Your total accumulated score: {total_score}")
        break
