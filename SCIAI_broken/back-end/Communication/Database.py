# CHANGE: Migrated from mysql.connector to pymysql
# Reason: Standardize on pymysql library across entire codebase (frontend already uses it)
# Benefits: Pure Python implementation, better error messages, consistent with frontend
import pymysql
import pymysql.cursors

class Database:
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, config):
        """
        Initialize database connection with pymysql

        config: dict with keys - host, user, password, database

        CHANGE: Now uses pymysql instead of mysql.connector
        CHANGE: Added DictCursor to return rows as dictionaries instead of tuples
        Benefit: Easier to access columns by name (row['barcode'] vs row[0])
        """
        self.connection = None
        self.connection = pymysql.connect(
            **config,
            cursorclass=pymysql.cursors.DictCursor  # Returns dict rows: {'id': 1, 'barcode': '0001'}
        )

    def query(self, sql, args):
        cursor = self.connection.cursor()
        cursor.execute(sql, args)
        return cursor

    def insert(self, sql, args):
        cursor = self.connection.cursor()
        cursor.executemany(sql, args)
        rowcount = cursor.rowcount
        self.connection.commit()
        cursor.close()
        return rowcount

    def update(self, sql, args):
        cursor = self.query(sql, args)
        rowcount = cursor.rowcount
        self.connection.commit()
        cursor.close()
        return rowcount

    def fetch(self, sql, args):
        """
        Fetch all rows from a SELECT query

        CHANGE: cursor.with_rows → cursor.description
        Reason: pymysql uses cursor.description to check if query returned data
        (mysql.connector used cursor.with_rows property)
        """
        rows = []
        cursor = self.query(sql, args)
        if cursor.description:  # Check if query returned results (None for INSERT/UPDATE)
            rows = cursor.fetchall()
        cursor.close()
        return rows

    def fetchone(self, sql, args):
        """
        Fetch single row from a SELECT query

        CHANGE: cursor.with_rows → cursor.description
        Reason: pymysql uses cursor.description to check if query returned data
        """
        row = None
        cursor = self.query(sql, args)
        if cursor.description:  # Check if query returned results (None for INSERT/UPDATE)
            row = cursor.fetchone()
        cursor.close()
        return row

    def __del__(self):
        if self.connection != None:
            self.connection.close()
