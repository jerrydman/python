import random
import pyttsx3
from prettytable import PrettyTable

# Initialize the text-to-speech engine
engine = pyttsx3.init()

def speak(text):
    """Function to read out text."""
    engine.say(text)
    engine.runAndWait()

def generate_bingo_numbers():
    # Bingo columns: B (1-15), I (16-30), N (31-45), G (46-60), O (61-75)
    bingo_columns = {
        'B': list(range(1, 16)),
        'I': list(range(16, 31)),
        'N': list(range(31, 46)),
        'G': list(range(46, 61)),
        'O': list(range(61, 76))
    }

    # Combine all numbers into one list
    all_numbers = []
    for column in bingo_columns.values():
        all_numbers.extend(column)

    # Shuffle the list of numbers
    random.shuffle(all_numbers)

    return all_numbers

def update_table(called_numbers):
    """Function to display the Bingo numbers in a table format."""
    # Create a PrettyTable object
    table = PrettyTable()
    table.field_names = ['B', 'I', 'N', 'G', 'O']

    # Create a grid for called numbers based on columns
    columns = {
        'B': [num if num in called_numbers else '' for num in range(1, 16)],
        'I': [num if num in called_numbers else '' for num in range(16, 31)],
        'N': [num if num in called_numbers else '' for num in range(31, 46)],
        'G': [num if num in called_numbers else '' for num in range(46, 61)],
        'O': [num if num in called_numbers else '' for num in range(61, 76)]
    }
    
    # Transpose the columns to rows for table display
    for i in range(15):
        table.add_row([columns['B'][i], columns['I'][i], columns['N'][i], columns['G'][i], columns['O'][i]])

    # Print the table
    print(table)

def call_bingo_numbers():
    while True:
        numbers = generate_bingo_numbers()
        called_numbers = []
        
        print("Welcome to Bingo! Press Enter to call the next number.")
        print("If you have a Bingo, press 'b' to reset the game.")
        
        while numbers:
            input("Press Enter to get the next number...")
            number = numbers.pop()
            called_numbers.append(number)
            column = ['B', 'I', 'N', 'G', 'O'][(number - 1) // 15]
            announcement = f"Next number: {column}{number}"
            print(announcement)
            
            # Read out the Bingo number
            speak(announcement)

            # Display the updated Bingo table
            update_table(called_numbers)
            
            # Check for Bingo
            bingo_input = input("Do you have a Bingo? (Press 'b' to reset or Enter to continue calling): ").strip().lower()
            if bingo_input == 'b':
                print("\nBingo! Starting a new game...\n")
                break

        # After all numbers are called, ask if the user wants to play again
        play_again = input("Do you want to play again? (y/n): ").strip().lower()
        if play_again != 'y':
            print("Thanks for playing Bingo! Goodbye.")
            break

if __name__ == "__main__":
    call_bingo_numbers()

