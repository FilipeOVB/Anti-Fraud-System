import pandas as pd
from datetime import datetime

from src.antifraud import analyzes_transaction


def menu():
    while True:
        print("=====================================================")
        print("1. Process the stored transaction")
        print("2. Process new transaction")
        print("3. Exit")

        choice = input("\nChoose an option: ")

        if choice == "1":
            return 1
        elif choice == "2":
            return 2
        elif choice == "3":
            return 3
        else:
            print("Invalid option. Please try again.")

def process_transaction():

    historical = pd.read_csv("./data/transactional-result.csv", parse_dates=["transaction_date"])

    choice = menu()
    transaction = {}

    #---------------------------------------------------------------------------------------------------------#
    if choice == 1:
        transaction = {
            "transaction_id" : 2342357,
            "merchant_id" : 29744,
            "user_id" : 97051,
            "card_number" : "434505******9116",
            "transaction_date" : "2019-11-30T23:16:32.812632",
            "transaction_amount" : 373,
            "device_id" : 285475
        }
    #---------------------------------------------------------------------------------------------------------#
    if choice == 2:
        transaction["transaction_id"] = int(input("\ntransaction_id: "))
        transaction["merchant_id"] = int(input("merchant_id: "))
        transaction["user_id"] = int(input("user_id: "))
        transaction["card_number"] = (input("card_number: "))
        
        date_str = input("transaction_date: ").strip()
        while True:
            if date_str:
                try:
                    # tenta converter para datetime
                    transaction["transaction_date"] = datetime.fromisoformat(date_str)
                    transaction["transaction_date"] = pd.to_datetime(transaction["transaction_date"], errors="coerce")
                    break
                except ValueError:
                    print("Invalid format. Try again")

        transaction["transaction_amount"] = float(input("transaction_amount: "))
        transaction["device_id"] = int(input("device_id: "))

    #---------------------------------------------------------------------------------------------------------#

    transaction["transaction_date"] = pd.to_datetime(transaction["transaction_date"], errors="coerce")
    transaction = pd.Series(transaction)

    # Classifies a transaction based on history
    status = analyzes_transaction(transaction, historical)

    # status == 0 -> transaction approved
    # status != 0 -> in some cases the transaction was declined
    if status != 0:
        recommendation = "deny"
    else:
        recommendation = "approve"

    transaction["recommendation"] = recommendation

    print(f"\n{transaction}\n")