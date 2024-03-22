from mysql.connector import Error
from db_config import create_connection
from db_config import fetch_query_results
from prettytable import PrettyTable
from datetime import datetime, timedelta, date
from collections import defaultdict
from decimal import Decimal
import mysql.connector
import random
from dotenv import load_dotenv
import os

load_dotenv

def show_tables():
    query = "SHOW TABLES"
    tables = fetch_query_results(query)
    print("Tables in the database:")
    for table in tables:
        print(table[0])  # Adjust based on your fetchall() structure

def describe_table(table_name):
    query = f"DESCRIBE {table_name}"
    description = fetch_query_results(query)
    print(f"Structure of {table_name}:")
    for col in description:
        print(col)  # Adjust based on your fetchall() structure

def fr1_list_rooms_and_rates():
    query = """
    SELECT r.RoomCode, r.RoomName, r.Beds, r.bedType, r.maxOcc, r.basePrice, r.decor,
           COALESCE((SELECT ROUND(SUM(
                 GREATEST(0, DATEDIFF(
                   LEAST(Checkout, CURDATE()),
                   GREATEST(CheckIn, CURDATE() - INTERVAL 180 DAY)
                 ))
               ) / 180, 2)
         FROM lab7_reservations
         WHERE Room = r.RoomCode
         AND Checkout > CURDATE() - INTERVAL 180 DAY
         AND CheckIn < CURDATE()), 0) AS popularity_score,
           (SELECT MIN(Checkout)
            FROM lab7_reservations
            WHERE Room = r.RoomCode AND Checkout > CURDATE()) + INTERVAL 1 DAY AS next_available_checkin,
           (SELECT DATEDIFF(Checkout, CheckIn)
            FROM lab7_reservations
            WHERE Room = r.RoomCode
            AND Checkout <= CURDATE()
            ORDER BY Checkout DESC
            LIMIT 1) AS last_stay_length,
           (SELECT Checkout
            FROM lab7_reservations
            WHERE Room = r.RoomCode
            AND Checkout <= CURDATE()
            ORDER BY Checkout DESC
            LIMIT 1) AS last_checkout_date
    FROM lab7_rooms r
    ORDER BY popularity_score DESC;
    """
    results = fetch_query_results(query)
    if results:
        table = PrettyTable()
        table.field_names = ["Room Code", "Room Name", "Beds", "Bed Type", "Max Occupancy", "Base Price", "Decor", "Popularity Score", "Next Available Check-In", "Last Stay Length", "Last Checkout Date"]
        for row in results:
            # Formatting dates or handling N/A if date is None
            next_available = row['next_available_checkin'].strftime('%Y-%m-%d') if row.get('next_available_checkin') else 'N/A'
            last_checkout_date = row['last_checkout_date'].strftime('%Y-%m-%d') if row.get('last_checkout_date') else 'N/A'
            table.add_row([
                row['RoomCode'], row['RoomName'], row['Beds'], row['bedType'],
                row['maxOcc'], row['basePrice'], row['decor'], row['popularity_score'],
                next_available, row['last_stay_length'], last_checkout_date
            ])
        print(table)
    else:
        print("No rooms found.")

def fr2_make_reservation():
    reservation_details = get_reservation_details()
    occupancy = reservation_details['adults'] + reservation_details['kids']
    handle_room_selection_and_booking(reservation_details)

def get_reservation_details():
    print("Please enter your reservation details:")
    details = {
        'first_name': input("First name: "),
        'last_name': input("Last name: "),
        'room_code': input("Room code (or 'Any' for no preference): "),
        'bed_type': input("Bed type desired (or 'Any' for no preference): "),
        'check_in': input("Begin date of stay (YYYY-MM-DD): "),
        'check_out': input("End date of stay (YYYY-MM-DD): "),
        'kids': int(input("Number of children: ")),
        'adults': int(input("Number of adult: ")),
    }
    return details

def find_rooms_matching_criteria(details):
    occupancy = details['adults'] + details['kids']
    desired_check_in = details['check_in']
    desired_check_out = details['check_out']
    interval_days = (datetime.strptime(desired_check_out, '%Y-%m-%d') - datetime.strptime(desired_check_in, '%Y-%m-%d')).days

    # Start with the most specific query, gradually relaxing constraints
    queries = [
        # Exact match or "Any" preference
        {
            "query": """
                SELECT r.RoomCode, r.RoomName, r.Beds, r.bedType, r.maxOcc, r.basePrice, r.decor
                FROM lab7_rooms r
                WHERE (r.RoomCode = %s OR %s = 'Any')
                AND (r.bedType = %s OR %s = 'Any')
                AND r.maxOcc >= %s
                AND r.RoomCode NOT IN (
                    SELECT res.Room
                    FROM lab7_reservations res
                    WHERE res.Room = r.RoomCode
                    AND (res.CheckIn < %s AND res.Checkout > %s)
                )
                ORDER BY r.maxOcc DESC, r.basePrice
            """,
            "params": (details['room_code'], details['room_code'], details['bed_type'], details['bed_type'], occupancy, details['check_out'], details['check_in'])
        },
        # Similar room suggestions ignoring room code
        {
            "query": """
                SELECT RoomCode, RoomName, Beds, bedType, maxOcc, basePrice, decor 
                FROM lab7_rooms 
                WHERE (bedType = %s OR %s = 'Any')
                AND maxOcc >= %s
                AND RoomCode NOT IN (
                    SELECT Room FROM lab7_reservations 
                    WHERE (CheckIn < %s AND Checkout > %s)
                )
                ORDER BY maxOcc DESC, basePrice
            """,
            "params": (details['bed_type'], details['bed_type'], occupancy, details['check_out'], details['check_in'])
        },
        # Similar room suggestions ignoring bed_type
        {
            "query": """
                SELECT RoomCode, RoomName, Beds, bedType, maxOcc, basePrice, decor 
                FROM lab7_rooms 
                WHERE maxOcc >= %s
                AND RoomCode NOT IN (
                    SELECT Room FROM lab7_reservations 
                    WHERE (CheckIn < %s AND Checkout > %s)
                )
                ORDER BY maxOcc DESC, basePrice
            """,
            "params": (occupancy, details['check_out'], details['check_in'])
        },
        # Similar room suggestion nearby dates
        {
            "query": """
               SELECT DISTINCT 
                    ro.RoomCode, 
                    ro.RoomName, 
                    ro.Beds, 
                    ro.bedType, 
                    ro.maxOcc, 
                    ro.basePrice, 
                    ro.decor, 
                    r1.CheckOut AS StartDate
                FROM 
                    lab7_reservations r1
                JOIN 
                    lab7_rooms ro ON r1.Room = ro.RoomCode
                WHERE 
                    r1.CheckOut >= CURDATE()  -- Looking for dates starting from today or the specified start date
                AND NOT EXISTS (
                    -- Ensure there's no reservation starting on the checkout date of the current reservation
                    SELECT 1
                    FROM lab7_reservations r3
                    WHERE r3.Room = r1.Room
                    AND r3.CheckIn = r1.CheckOut
                )
                ORDER BY 
                    r1.CheckOut
            """,
            "params": (details['check_in'], interval_days)
        }
    ]

    num_run=0
    results = []
    for query_info in queries:
        query = fetch_query_results(query_info['query'], query_info['params'])
        if query != None:
            results += query
        num_run += 1
        if results and num_run==1:
            return results
        elif num_run == 4:
            print(num_run)
            return results[:5]
    return []

def handle_room_selection_and_booking(details):
    rooms_suggestions = find_rooms_matching_criteria(details)
    if not rooms_suggestions:
        print("No suitable rooms are available based on your criteria.")
        return

    table = PrettyTable()
    table.field_names = ["#", "Room Name", "Room Code", "Beds", "Type", "Max Occupancy", "Base Price", "Decor", "Suggested Check-In", "Suggested Check-Out"]

    desired_interval = datetime.strptime(details['check_out'], '%Y-%m-%d') - datetime.strptime(details['check_in'], '%Y-%m-%d')

    for i, room in enumerate(rooms_suggestions, 1):
        base_price = "${:,.2f}".format(room['basePrice']) if isinstance(room['basePrice'], Decimal) else "Unknown"
        
        # For rooms with an alternative check-in date
        if 'StartDate' in room:
            alternative_check_in = room['StartDate'].strftime('%Y-%m-%d')
            # Calculate the alternative check-out based on the desired interval
            alternative_check_out = (room['StartDate'] + desired_interval).strftime('%Y-%m-%d')
        else:
            alternative_check_in = "N/A"
            alternative_check_out = "N/A"

        table.add_row([i, room.get('RoomName', 'Unknown'), room.get('RoomCode', 'N/A'), room.get('Beds', 'N/A'), room.get('bedType', 'N/A'), 
                       room.get('maxOcc', 'N/A'), base_price, room.get('decor', 'N/A'), 
                       alternative_check_in, alternative_check_out])

    print("\nAvailable rooms and/or alternative dates:")
    print(table)

    choice = input("Enter the option number to book, or type 'cancel' to return to the main menu: ")
    if choice.lower() == 'cancel':
        return

    try:
        selected_option = int(choice) - 1
        if 0 <= selected_option < len(rooms_suggestions):
            selected_room = rooms_suggestions[selected_option]
            confirm_and_book_reservation(details, selected_room)
        else:
            print("Invalid selection. Please try again.")
    except ValueError:
        print("Please enter a valid option number.")

def confirm_and_book_reservation(details, selected_room):
    # Adjusting check-in date based on selected room or alternative suggestion
    if 'StartDate' in selected_room and isinstance(selected_room['StartDate'], date):
        check_in_date = selected_room['StartDate'].strftime('%Y-%m-%d')
        # Calculate the check-out date based on the desired interval
        desired_interval_days = (datetime.strptime(details['check_out'], '%Y-%m-%d') - datetime.strptime(details['check_in'], '%Y-%m-%d')).days
        check_out_date = (selected_room['StartDate'] + timedelta(days=desired_interval_days)).strftime('%Y-%m-%d')
    else:
        check_in_date = details['check_in']
        check_out_date = details['check_out']


    check_in = datetime.strptime(check_in_date, '%Y-%m-%d')
    check_out = datetime.strptime(check_out_date, '%Y-%m-%d')
    
    total_days = (check_out - check_in).days
    weekend_days = sum(1 for i in range(total_days) if (check_in + timedelta(days=i)).weekday() >= 5)
    weekday_days = total_days - weekend_days

    base_rate = float(selected_room['basePrice'])  # Assuming basePrice is a Decimal
    total_cost = (weekday_days * base_rate) + (weekend_days * base_rate * 1.1)

    # PrettyTable for displaying booking confirmation details
    confirmation_table = PrettyTable()
    confirmation_table.field_names = ["Detail", "Information"]
    confirmation_details = [
        ["First Name", details['first_name']],
        ["Last Name", details['last_name']],
        ["Room Code", selected_room.get('RoomCode', 'N/A')],  # Adjusted based on your provided dictionary structure
        ["Room Name", selected_room.get('RoomName', 'Unknown')],
        ["Bed Type", selected_room.get('bedType', 'N/A')],
        ["Begin Date of Stay", check_in_date],
        ["End Date of Stay", check_out_date],
        ["Number of Adults", str(details['adults'])],  # Ensuring numeric values are converted to strings for PrettyTable
        ["Number of Children", str(details['kids'])],
        ["Total Cost of Stay", f"${round(total_cost, 2)}"]
    ]
    
    for detail in confirmation_details:
        confirmation_table.add_row(detail)
    
    print("\nReservation Confirmation:")
    print(confirmation_table)
    book_room(details, selected_room)

def book_room(details, selected_room):
    # Generate a unique reservation code (for demonstration purposes)
    # This example uses the current datetime and a random number

    check_in_date = details['check_in'] if 'StartDate' not in selected_room else selected_room['StartDate'].strftime('%Y-%m-%d')
    desired_interval_days = (datetime.strptime(details['check_out'], '%Y-%m-%d') - datetime.strptime(details['check_in'], '%Y-%m-%d')).days
    check_out_date = details['check_out'] if 'CheckOut' not in selected_room else (selected_room['StartDate'] + timedelta(days=desired_interval_days)).strftime('%Y-%m-%d')
    connection = None

    try:
        connection = mysql.connector.connect(host='mysql.labthreesixfive.com',
                                             database='hwu35',
                                             user='hwu35',
                                             password=os.getenv('DB_PASSWORD'))
        if connection.is_connected():
            cursor = connection.cursor()
            reservation_code = random.randint(10000, 99999)
            query = "SELECT * FROM lab7_reservations WHERE CODE = %s"
            cursor.execute(query, (reservation_code,))
            existing_reservation = cursor.fetchone()

            while existing_reservation:
                reservation_code = random.randint(10000, 99999)
                cursor.execute(query, (reservation_code,))
                existing_reservation = cursor.fetchone()

            insert_query = """
            INSERT INTO lab7_reservations (CODE, Room, CheckIn, Checkout, Rate, LastName, FirstName, Adults, Kids)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(insert_query, (reservation_code, selected_room['RoomCode'], check_in_date, check_out_date, selected_room['basePrice'],
                                          details['last_name'], details['first_name'],
                                          details['adults'], details['kids']))

            connection.commit()
            print("Reservation successfully booked with code:", reservation_code)
    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

def fr3_cancel_reservation():
    # Prompt user to enter reservation code
    reservation_code = input("Enter the reservation code you wish to cancel: ")

    # Call cancel_reservation function with the entered reservation code
    cancel_reservation(reservation_code)

def cancel_reservation(reservation_code):
    try:
        conn = create_connection()
        cursor = conn.cursor()

        # Fetch reservation details
        query = "SELECT * FROM lab7_reservations WHERE CODE = %s"
        cursor.execute(query, (reservation_code,))
        reservation = cursor.fetchone()

        if reservation:
            print("Reservation details:")
            print("Reservation Code:", reservation[0])
            print("Room Code:", reservation[1])
            print("Check-in Date:", reservation[2])
            print("Checkout Date:", reservation[3])
            # Display other reservation details as needed

            # Confirm cancellation
            confirm = input("Are you sure you want to cancel this reservation? (yes/no): ").lower()
            if confirm == "yes":
                # Delete reservation record
                delete_query = "DELETE FROM lab7_reservations WHERE CODE = %s"
                cursor.execute(delete_query, (reservation_code,))
                conn.commit()  # Commit changes
                print("Reservation canceled successfully.")
            else:
                print("Reservation cancellation aborted.")
        else:
            print("Reservation not found.")
        
    except mysql.connector.Error as error:
        print("Error:", error)

    finally:
        # Close cursor and connection
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def fr4_detailed_reservation_info():
    print("Enter search criteria (leave blank for 'Any'):")
    first_name = input("First name: ").strip() or '%'
    last_name = input("Last name: ").strip() or '%'
    date_range_start = input("Start date (YYYY-MM-DD, leave blank for 'Any'): ").strip() or '1900-01-01'
    date_range_end = input("End date (YYYY-MM-DD, leave blank for 'Any'): ").strip() or '9999-12-31'
    room_code = input("Room code: ").strip() or '%'
    reservation_code = input("Reservation code (leave blank for 'Any'): ").strip() or '%'

    # Construct the query with adjusted conditions for actual overlap
    query = """
    SELECT r.CODE, r.Room, r.CheckIn, r.Checkout, r.Rate, r.LastName, r.FirstName, r.Adults, r.Kids, rm.RoomName
    FROM lab7_reservations r
    LEFT JOIN lab7_rooms rm ON r.Room = rm.RoomCode
    WHERE r.FirstName LIKE %s AND r.LastName LIKE %s
    AND r.CheckIn < %s AND r.Checkout > %s
    AND r.Room LIKE %s AND r.CODE LIKE %s
    ORDER BY r.CheckIn;
    """

    connection = create_connection()

    try:
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(query, (first_name, last_name, date_range_end, date_range_start, room_code, reservation_code))
            
            results = cursor.fetchall()
            if results:
                table = PrettyTable()
                table.field_names = ["Code", "Room", "Check-in", "Check-out", "Rate", "Last Name", "First Name", "Adults", "Kids", "Room Name"]
                for row in results:
                    table.add_row(row)
                print(table)
            else:
                print("No reservations found matching the criteria.")
    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def fr5_revenue_current_year():
    query = """
    SELECT
        r.RoomCode,
        r.RoomName,
        res.CheckIn,
        res.Checkout,
        res.Rate
    FROM
        lab7_rooms r
    LEFT JOIN
        lab7_reservations res ON r.RoomCode = res.Room
    WHERE
        res.Checkout >= CONCAT(YEAR(CURDATE()), '-01-01') AND
        res.CheckIn <= CONCAT(YEAR(CURDATE()), '-12-31');
    """
    reservations = fetch_query_results(query)
    if not reservations:
        print("No reservations found for the current year.")
        return

    # Convert fetched data into a list of dicts, if not already in that format
    reservations = [dict(row) for row in reservations]

    revenue_by_room = calculate_revenue_per_room(reservations)
    display_revenue(revenue_by_room)

def calculate_revenue_per_room(reservations):
    revenue_by_room = defaultdict(lambda: {"RoomName": "", "Revenue": defaultdict(float)})
    for res in reservations:
        start_date = max(res['CheckIn'], date(datetime.now().year, 1, 1))
        end_date = min(res['Checkout'], date(datetime.now().year, 12, 31))
        
        current_date = start_date
        while current_date < end_date:
            # Check if the current date is a weekend
            if current_date.weekday() in [5, 6]:  # Saturday or Sunday
                daily_rate = float(res['Rate']) * 1.1
            else:
                daily_rate = float(res['Rate'])
            
            month_key = current_date.strftime('%Y-%m')
            revenue_by_room[res['RoomCode']]["Revenue"][month_key] += daily_rate
            revenue_by_room[res['RoomCode']]["RoomName"] = res['RoomName']
            current_date += timedelta(days=1)
    
    return revenue_by_room

def display_revenue(revenue_by_room):
    table = PrettyTable()
    months = [f"{datetime.now().year}-{str(m).zfill(2)}" for m in range(1, 13)]
    table.field_names = ["Room Code", "Room Name"] + months + ["Total Revenue"]
    
    for room_code, data in revenue_by_room.items():
        row = [room_code, data["RoomName"]]
        total_revenue = 0
        for month in months:
            month_revenue = data["Revenue"].get(month, 0)
            row.append(round(month_revenue))
            total_revenue += month_revenue
        row.append(round(total_revenue))
        table.add_row(row)
    
    print(table)