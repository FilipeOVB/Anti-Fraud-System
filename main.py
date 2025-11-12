from src.antifraud import process_database
from src.plot_graph import plot
from src.payload import process_transaction

def main():
    while True:
        print("=====================================================")
        print("1. Process transaction history")
        print("2. Generate statistical graphs")
        print("3. Test new transaction (process the history before)")
        print("4. Exit")

        choice = input("\nChoose an option: ")

        if choice == "1":
            process_database()
        elif choice == "2":
            plot()
        elif choice == "3":
            process_transaction()
        elif choice == "4":
            print("Closing...")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()