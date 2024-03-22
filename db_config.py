import mysql.connector
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Function to create database connection
def create_connection():
    connection = mysql.connector.connect(
        host='mysql.labthreesixfive.com',
        user='hwu35',
        password=os.getenv('DB_PASSWORD'),
        database='hwu35',
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
    cursor = connection.cursor(dictionary=True)
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