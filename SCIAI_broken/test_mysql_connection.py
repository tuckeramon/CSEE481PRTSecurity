"""
MySQL Connection Test Script

This script tests the MySQL server connection and lists all available databases.
Run this after installing MySQL to verify it's working properly.

Usage: python test_mysql_connection.py
"""
import mysql.connector

# MySQL connection configuration
config = {
    'host': 'localhost',   # Connect to local MySQL server
    'user': 'root',        # MySQL user (root is the admin user)
    'password': 'root',    # Change this if you used a different password during MySQL setup
}

try:
    # Attempt to connect to MySQL server
    print("Attempting to connect to MySQL...")
    connection = mysql.connector.connect(**config)
    print("✓ Successfully connected to MySQL!")

    # Query to show all databases
    cursor = connection.cursor()
    cursor.execute("SHOW DATABASES;")
    databases = cursor.fetchall()

    # Display all databases found
    print("\nExisting databases:")
    for db in databases:
        print(f"  - {db[0]}")

    # Clean up database connection
    cursor.close()
    connection.close()
    print("\n✓ Connection test successful!")

except mysql.connector.Error as err:
    # If connection fails, provide helpful error information
    print(f"✗ MySQL connection failed: {err}")
    print("\nPossible fixes:")
    print("1. Make sure MySQL is installed and running")
    print("2. Check that the password matches what you set during installation")
    print("3. Update the password in this script if needed")
