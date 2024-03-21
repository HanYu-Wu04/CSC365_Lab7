from db_config import create_connection
from db_config import fetch_query_results

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
    conn = create_connection()
    if conn is not None:
        cursor = conn.cursor()
        query = """
        SELECT r.RoomCode, r.RoomName, r.Beds, r.bedType, r.maxOcc, r.basePrice, r.decor,
               (SELECT COUNT(*) FROM lab7_reservations WHERE Room = r.RoomCode AND Checkout > CURDATE() - INTERVAL 180 DAY) / 180.0 AS popularity,
               (SELECT MIN(CheckIn) FROM lab7_reservations WHERE Room = r.RoomCode AND CheckIn > CURDATE()) AS next_available,
               (SELECT Checkout FROM lab7_reservations WHERE Room = r.RoomCode ORDER BY Checkout DESC LIMIT 1) AS last_checkout
        FROM lab7_rooms r
        ORDER BY popularity DESC;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        cursor.close()
        conn.close()

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