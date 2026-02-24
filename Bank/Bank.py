import logging
import random
from datetime import datetime

# -----------------------------
# Logging Configuration
# -----------------------------
logging.basicConfig(
    level=logging.DEBUG,
    filename="bank_log.log",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# -----------------------------
# Bank System Class
# -----------------------------
class PriyaBank:
    def __init__(self):
        self.accounts = []         
        self.citizens = []         
        self.balances = []         
        self.account_numbers = []  
        self.pins = []             
        self.deposit_count = []    
        self.manager_pin = 3103
        self.loans = []           

    # Generate unique account number
    def gen_account_number(self):
        while True:
            number = random.randint(1000, 9999)
            if number not in self.account_numbers:
                self.account_numbers.append(number)
                logging.info(f"🆕 Account number generated: {number}")
                return number

    # Open new account
    def open_account(self):
        try:
            
            while True:
                name = input("Enter your Full Name: ").strip()
                if name.isalpha():
                    break
                logging.warning("Invalid name input ❌")
                print("Invalid name! Please enter letters only.\n")

            
            while True:
                citizen = input("Enter your Citizenship Number: ")
                if citizen.isdigit():
                    citizen = int(citizen)
                    if citizen not in self.citizens:
                        break
                    else:
                        print("Citizenship number must be unique!\n")
                logging.warning("Invalid citizenship input ❌")
                print("Invalid input! Please enter digits only.\n")

            
            while True:
                deposit = input("Deposit initial amount: ₹")
                if deposit.isdigit() and int(deposit) > 0:
                    deposit = int(deposit)
                    break
                logging.warning("Invalid deposit amount ❌")
                print("Invalid input! Please enter a positive number.\n")

            
            while True:
                pin = input("Create a 4-digit PIN: ")
                if pin.isdigit() and len(pin) == 4:
                    pin = int(pin)
                    break
                logging.warning("Invalid PIN input ❌")
                print("PIN must be 4 digits!\n")

            
            self.accounts.append(name)
            self.citizens.append(citizen)
            self.balances.append(deposit)
            self.pins.append(pin)
            self.deposit_count.append(1)
            account_number = self.gen_account_number()

            logging.info(f"✅ Account created for {name} | Account No: {account_number} | Initial Deposit: ₹{deposit}")
            print(f"\nAccount Created Successfully ✅\nName: {name}\nAccount Number: {account_number}\nBalance: ₹{deposit}\n")
        except Exception as e:
            logging.error(f"Account creation failed ❌: {e}")

    # Delete account
    def delete_account(self):
        try:
            name = input("Enter account name to delete: ")
            if name in self.accounts:
                index = self.accounts.index(name)
                pin = int(input("Enter Manager PIN: "))
                if pin == self.manager_pin:
                    logging.info(f"🗑️ Account deleted: {name}")
                    print(f"Account {name} deleted successfully ✅")
                    
                    for lst in [self.accounts, self.citizens, self.balances, self.pins, self.deposit_count, self.account_numbers]:
                        lst.pop(index)
                else:
                    logging.warning("Manager PIN incorrect ❌")
                    print("Wrong Manager PIN!")
            else:
                logging.warning("Attempt to delete non-existing account ❌")
                print("Account not found!")
        except Exception as e:
            logging.error(f"Account deletion failed ❌: {e}")

    # Deposit money
    def deposit(self):
        try:
            name = input("Enter account name: ")
            if name in self.accounts:
                index = self.accounts.index(name)
                amount = input("Enter amount to deposit: ₹")
                if amount.isdigit() and int(amount) > 0:
                    amount = int(amount)
                    self.balances[index] += amount
                    self.deposit_count[index] += 1
                    logging.info(f"💰 ₹{amount} deposited to {name} | New Balance: ₹{self.balances[index]}")
                    print(f"₹{amount} deposited successfully ✅ | Current Balance: ₹{self.balances[index]}")
                else:
                    logging.warning("Invalid deposit amount ❌")
                    print("Invalid amount!")
            else:
                logging.warning("Deposit to non-existing account ❌")
                print("Account not found!")
        except Exception as e:
            logging.error(f"Deposit failed ❌: {e}")

    # Withdraw money
    def withdraw(self):
        try:
            name = input("Enter account name: ")
            if name in self.accounts:
                index = self.accounts.index(name)
                if self.balances[index] <= 300:
                    print("❌ Withdrawals not allowed below ₹300 balance")
                    return
                pin = int(input("Enter your 4-digit PIN: "))
                if pin == self.pins[index]:
                    amount = int(input("Enter amount to withdraw: ₹"))
                    if 0 < amount <= self.balances[index]:
                        self.balances[index] -= amount
                        logging.info(f"💸 ₹{amount} withdrawn from {name} | Remaining Balance: ₹{self.balances[index]}")
                        print(f"₹{amount} withdrawn successfully ✅ | Remaining Balance: ₹{self.balances[index]}")
                    else:
                        logging.warning("Withdrawal failed due to insufficient funds ❌")
                        print("Insufficient balance or invalid amount!")
                else:
                    logging.warning("Incorrect PIN ❌")
                    print("Wrong PIN!")
            else:
                logging.warning("Withdrawal attempt on non-existing account ❌")
                print("Account not found!")
        except Exception as e:
            logging.error(f"Withdrawal failed ❌: {e}")

    # Check balance
    def check_balance(self):
        try:
            name = input("Enter account name: ")
            if name in self.accounts:
                index = self.accounts.index(name)
                pin = int(input("Enter your 4-digit PIN: "))
                if pin == self.pins[index]:
                    logging.info(f"🔎 Balance checked for {name} | Balance: ₹{self.balances[index]}")
                    print(f"Account Name: {name}\nBalance: ₹{self.balances[index]}")
                else:
                    logging.warning("Incorrect PIN ❌")
                    print("Wrong PIN!")
            else:
                logging.warning("Balance check for non-existing account ❌")
                print("Account not found!")
        except Exception as e:
            logging.error(f"Balance check failed ❌: {e}")

    # Apply for loan
    def apply_loan(self):
        try:
            name = input("Enter account name: ")
            if name in self.accounts:
                index = self.accounts.index(name)
                if self.deposit_count[index] < 10:
                    print("❌ Loans allowed only after at least 10 deposits")
                    return
                amount = int(input("Enter loan amount (Max ₹5,00,000): ₹"))
                if 0 < amount <= 500000:
                    self.loans.append(amount)
                    logging.info(f"🏦 Loan approved for {name} | Amount: ₹{amount}")
                    print(f"Loan of ₹{amount} approved ✅")
                else:
                    logging.warning("Loan application exceeds limit ❌")
                    print("Loan amount exceeds maximum limit!")
            else:
                logging.warning("Loan application for non-existing account ❌")
                print("Account not found!")
        except Exception as e:
            logging.error(f"Loan application failed ❌: {e}")

    def change_pin (self):
        try:
            name = input("Enter account name : ")
            if name in self.accounts :
                index = self.accounts.index(name)
                pin = int(input("Enter manager pin : "))
                if pin == self.manager_pin:
                    new = input("Enter new pin : ")
                    if new.isdigit() and len(new) == 4:
                        new = int(new)
                        self.pins[index] = new
                        print("Pin change successfully✅")
                        logging.info(f"Pin changed for aacount: {name}")
                    else:
                        print("Please enter valid pin!")
                else: 
                    print("Wrong❌ manager pin!")
            else:
                print("Account not found❌")
        except Exception as e:
            logging.error("Changing of pin is failed")
            print(f"Something went wrong❌: {e}")


            


bank = PriyaBank()

menu_options = {
    "1": bank.open_account,
    "2": bank.delete_account,
    "3": bank.deposit,
    "4": bank.withdraw,
    "5": bank.apply_loan,
    "6": bank.check_balance,
    "7": bank.change_pin,
    "8": exit
}

print("💳 _ _ _ Priya Bank Limited _ _ _ 💳")

while True:
    print("\n1. Open Account")
    print("2. Delete Account")
    print("3. Deposit Amount")
    print("4. Withdraw Amount")
    print("5. Loan Application")
    print("6. Check Bank Balance")
    print("7. Change pin password")
    print("8. Exit\n")

    choice = input("Enter your choice: ")
    if choice in menu_options:
        menu_options[choice]()
    else:
        print("❌ Invalid choice! Please select from 1-8")
