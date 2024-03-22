from operations import *

def main():
    while True:
        print("""
        1. List Rooms and Rates
        2. Make a Reservation
        3. Cancel a Reservation
        4. Detailed Reservation Information
        5. Revenue by Month
        6. Exit
        """)
        choice = input("Select an option: ")
        if choice == "1":
            fr1_list_rooms_and_rates()
        elif choice == "2":
            fr2_make_reservation()
        elif choice == "3":
            fr3_cancel_reservation()
        elif choice == "4":
            fr4_detailed_reservation_info()
        elif choice == "5":
            fr5_revenue_current_year()
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please select again.")

if __name__ == "__main__":
    main()