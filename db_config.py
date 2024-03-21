import mysql.connector
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Function to create database connection
def create_connection():
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    return connection

# Function to execute a query that doesn't return data (e.g., INSERT, UPDATE, DELETE)
def execute_query(query, params=None):
    connection = create_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(query, params or ())
        connection.commit()
        print("Query executed successfully")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        connection.close()

# Function to execute a query and fetch its results (e.g., SELECT)
def fetch_query_results(query, params=None):
    connection = create_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(query, params or ())
        results = cursor.fetchall()
        return results
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    finally:
        cursor.close()
        connection.close()
