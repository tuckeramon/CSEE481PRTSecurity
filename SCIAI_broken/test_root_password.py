"""
Test if MySQL root password is set to 'root'

This is a quick verification script to test if the MySQL password reset was successful.
Run this after resetting the MySQL root password.

Usage: python test_root_password.py
"""
import mysql.connector

try:
    # Attempt to connect to MySQL with root/root credentials
    print("Testing MySQL connection with root/root...")
    conn = mysql.connector.connect(
        host='localhost',      # Connect to local MySQL server
        user='root',          # Using root user
        password='root'       # Password should be 'root'
    )
    print("SUCCESS! Password is set to 'root'")
    conn.close()
except Exception as e:
    # If connection fails, show the error
    print(f"FAILED: {e}")
