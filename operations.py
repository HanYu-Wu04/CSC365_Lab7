from db_config import create_connection
from db_config import fetch_query_results
from prettytable import PrettyTable

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
           (SELECT MIN(CheckIn)
            FROM lab7_reservations
            WHERE Room = r.RoomCode
            AND CheckIn >= CURDATE()) AS next_available_checkin,
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
            # Directly using row[] for simplicity, adjust based on actual result format
            table.add_row([
                row['RoomCode'], row['RoomName'], row['Beds'], row['bedType'],
                row['maxOcc'], row['basePrice'], row['decor'], row['popularity_score'],
                row['next_available_checkin'], row['last_stay_length'], row['last_checkout_date']
            ])
        print(table)
    else:
        print("No rooms found.")


def fr2_make_reservation(room_code, check_in, check_out, last_name, first_name, adults, kids):
    conn = create_connection()
    if conn is not None:
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO lab7_reservations (Room, CheckIn, Checkout, LastName, FirstName, Adults, Kids)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (room_code, check_in, check_out, last_name, first_name, adults, kids))
        conn.commit()
        print("Reservation successfully made.")
        cursor.close()
        conn.close()

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