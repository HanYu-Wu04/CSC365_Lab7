from db_config import create_connection
from db_config import fetch_query_results
from prettytable import PrettyTable
from datetime import datetime, timedelta, date
from collections import defaultdict
from decimal import Decimal

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
        'adults': int(input("Number of adults: "))
    }
    return details

def find_rooms_matching_criteria(details):
    # This is a simplified query. You'll need to extend it based on your exact logic for checking availability and preferences.
    occupancy = details['adults'] + details['kids']
    query = """
    SELECT RoomCode, RoomName, Beds, bedType, maxOcc, basePrice, decor 
    FROM lab7_rooms 
    WHERE (RoomCode = %s OR %s = 'Any')
    AND (bedType = %s OR %s = 'Any')
    AND maxOcc >= %s
    AND NOT EXISTS (
        SELECT 1 FROM lab7_reservations 
        WHERE Room = RoomCode 
        AND ((CheckIn <= %s AND Checkout >= %s) OR (CheckIn < %s AND Checkout >= %s))
    )
    ORDER BY maxOcc, basePrice DESC
    LIMIT 5;
    """
    params = (details['room_code'], details['room_code'], details['bed_type'], details['bed_type'], occupancy, details['check_in'], details['check_out'], details['check_in'], details['check_out'])
    return fetch_query_results(query, params)

def handle_room_selection_and_booking(details):
    available_rooms = find_rooms_matching_criteria(details)
    if not available_rooms:
        print("No suitable rooms are available based on your criteria.")
        return

    print("Available rooms:")
    for i, room in enumerate(available_rooms, 1):
        print(f"{i}. {room['RoomName']} ({room['RoomCode']}) - Beds: {room['Beds']}, Type: {room['bedType']}, Max Occupancy: {room['maxOcc']}, Base Price: ${room['basePrice']}")

    choice = input("Enter the option number to book or type 'cancel' to return to the main menu: ")
    if choice.lower() == 'cancel':
        return
    else:
        selected_room = available_rooms[int(choice) - 1]
        confirm_and_book_reservation(details, selected_room)

def confirm_and_book_reservation(details, selected_room):
    # Simplify date handling and total cost calculation
    check_in = datetime.strptime(details['check_in'], '%Y-%m-%d')
    check_out = datetime.strptime(details['check_out'], '%Y-%m-%d')
    total_days = (check_out - check_in).days
    weekend_days = sum(1 for i in range(total_days) if (check_in + timedelta(i)).weekday() >= 5)
    weekday_days = total_days - weekend_days
    total_cost = (weekday_days * selected_room['basePrice']) + (weekend_days * selected_room['basePrice'] * 1.1)
    
    # Assuming function to insert booking into database here

    print(f"Reservation confirmed for {details['first_name']} {details['last_name']} in {selected_room['RoomName']}.")
    print(f"Total cost for the stay: ${round(total_cost, 2)}")

def fr3_cancel_reservation(reservation_code):
    conn = create_connection()
    if conn is not None:
        cursor = conn.cursor()
        delete_query = "DELETE FROM lab7_reservations WHERE CODE = %s;"
        cursor.execute(delete_query, (reservation_code,))
        conn.commit()
        print(f"Reservation {reservation_code} cancelled.")
        cursor.close()
        conn.close()

def fr4_detailed_reservation_info(last_name='', first_name='', room_code=''):
    conn = create_connection()
    if conn is not None:
        cursor = conn.cursor()
        query = """
        SELECT * FROM lab7_reservations
        WHERE LastName LIKE %s AND FirstName LIKE %s AND Room LIKE %s;
        """
        cursor.execute(query, (f"%{last_name}%", f"%{first_name}%", f"%{room_code}%"))
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        cursor.close()
        conn.close()

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