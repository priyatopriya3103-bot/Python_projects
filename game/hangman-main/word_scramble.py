import random
from hangman_words import word_list

while True:
    original_word = random.choice(word_list)

    scrambled = list(original_word)
    random.shuffle(scrambled)
    scrambled_word = "".join(scrambled)
    score = 0
    tries = 3

    print("\n Scrambled word: ", scrambled_word)

    while tries > 0:
        print("❤️ "*tries)
        guess = input("Gues the word : ").lower()

        if guess ==  original_word:
            print("Correct 🎉!")
            score = score + 1
            break
        else:
            tries -= 1
            print("Wrong guess! Try again")
    if tries == 0:
        print("\n💔 Out of tries1")
        print("Coreect word was:", original_word)

    print("\n⭐ Current Score:", score)

    play_again = input("Play again? (yes/no): ").lower()
    if play_again != "yes":
        print("\nFinal score: ",score)
        print("Thanks for playing ❤️")
        break
