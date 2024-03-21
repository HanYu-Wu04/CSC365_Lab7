# main.py
from operations import fr1_list_rooms_and_rates, fr2_make_reservation, fr3_cancel_reservation, fr4_detailed_reservation_info, show_tables, describe_table

def main():
    while True:
        print("""
        1. List Rooms and Rates
        2. Make a Reservation
        3. Cancel a Reservation
        4. Detailed Reservation Information
        5. Show Database Tables
        6. Describe a Table
        7. Exit
        """)
        choice = input("Select an option: ")
        if choice == "1":
            fr1_list_rooms_and_rates()
        elif choice == "2":
            fr2_make_reservation()
        # Add other cases as previously
        elif choice == "5":
            show_tables()
        elif choice == "6":
            table_name = input("Enter table name to describe: ")
            describe_table(table_name)
        elif choice == "7":
            break
        else:
            print("Invalid choice. Please select again.")

if __name__ == "__main__":
    main()
