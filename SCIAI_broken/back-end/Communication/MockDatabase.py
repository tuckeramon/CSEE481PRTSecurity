"""
Mock Database for testing without MySQL server.
Stores data in memory using Python dictionaries and lists.
"""
from datetime import datetime


class MockDatabase:
    """Mock database that simulates MySQL functionality without requiring a server."""

    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, config):
        """
        config: host, user, password, database (ignored for mock)
        """
        # Initialize in-memory storage tables
        if not hasattr(self, 'initialized'):
            self.connection = True  # Mock connection
            self.tables = {
                'PRTSorterRequest': [],
                'PRTSorterResponse': [],
                'PRTSorterReport': [],
                'PRTCarts': [],
                'PRTRemoveCart': []
            }
            self.auto_increment_ids = {
                'PRTSorterRequest': 1,
                'PRTSorterResponse': 1,
                'PRTSorterReport': 1,
                'PRTCarts': 1,
                'PRTRemoveCart': 1
            }
            self.initialized = True
            print("[MockDatabase] Initialized mock database (no MySQL required)")

    def query(self, sql, args):
        """Mock query execution - returns a mock cursor."""
        return MockCursor(self, sql, args)

    def insert(self, sql, args):
        """Mock insert operation."""
        # Parse the INSERT statement to determine which table
        sql_upper = sql.upper().strip()

        if 'PRTSORTERREQUEST' in sql_upper:
            table = 'PRTSorterRequest'
            for row in args:
                record = {
                    'id': self.auto_increment_ids[table],
                    'sorterID': row[0],
                    'transactionID': row[1],
                    'barcode': row[2],
                    'timestamp': datetime.now()
                }
                self.tables[table].append(record)
                self.auto_increment_ids[table] += 1

        elif 'PRTSORTERRESPONSE' in sql_upper:
            table = 'PRTSorterResponse'
            for row in args:
                record = {
                    'id': self.auto_increment_ids[table],
                    'sorterID': row[0],
                    'barcode': row[1],
                    'transactionID': row[2],
                    'destination': row[3],
                    'timestamp': datetime.now()
                }
                self.tables[table].append(record)
                self.auto_increment_ids[table] += 1

        elif 'PRTSORTERREPORT' in sql_upper:
            table = 'PRTSorterReport'
            for row in args:
                record = {
                    'id': self.auto_increment_ids[table],
                    'sorterID': row[0],
                    'barcode': row[1],
                    'active': row[2],
                    'lost': row[3],
                    'good': row[4],
                    'diverted': row[5],
                    'timestamp': datetime.now()
                }
                self.tables[table].append(record)
                self.auto_increment_ids[table] += 1

        elif 'PRTCARTS' in sql_upper:
            table = 'PRTCarts'
            for row in args:
                record = {
                    'id': self.auto_increment_ids[table],
                    'barcode': row[0],
                    'destination': row[1],
                    'created_at': datetime.now()
                }
                self.tables[table].append(record)
                self.auto_increment_ids[table] += 1

        elif 'PRTREMOVECART' in sql_upper:
            table = 'PRTRemoveCart'
            for row in args:
                record = {
                    'id': self.auto_increment_ids[table],
                    'barcode': row[0],
                    'area': row[1],
                    'timestamp': datetime.now()
                }
                self.tables[table].append(record)
                self.auto_increment_ids[table] += 1

        print(f"[MockDatabase] INSERT into {table}: {len(args)} row(s)")
        return len(args)

    def update(self, sql, args):
        """Mock update operation."""
        sql_upper = sql.upper().strip()

        if 'PRTCARTS' in sql_upper and 'WHERE BARCODE' in sql_upper:
            destination = args[0]
            barcode = args[1]

            updated = 0
            for record in self.tables['PRTCarts']:
                if record['barcode'] == barcode:
                    record['destination'] = destination
                    record['updated_at'] = datetime.now()
                    updated += 1

            print(f"[MockDatabase] UPDATE PRTCarts: {updated} row(s) updated")
            return updated

        return 0

    def fetch(self, sql, args):
        """Mock fetch operation - returns list of tuples."""
        sql_upper = sql.upper().strip()

        if 'FROM PRTCARTS' in sql_upper:
            if 'WHERE BARCODE' in sql_upper:
                # Get specific cart by barcode
                barcode = args[0] if args else None
                results = []
                for record in self.tables['PRTCarts']:
                    if record['barcode'] == barcode:
                        # Return as tuple: (barcode, destination)
                        results.append((record['barcode'], record['destination']))
                print(f"[MockDatabase] SELECT from PRTCarts WHERE barcode={barcode}: {len(results)} row(s)")
                return results
            else:
                # Get all carts
                results = [(record['barcode'], record['destination']) for record in self.tables['PRTCarts']]
                print(f"[MockDatabase] SELECT all from PRTCarts: {len(results)} row(s)")
                return results

        return []

    def fetchone(self, sql, args):
        """Mock fetchone operation - returns single tuple or None."""
        results = self.fetch(sql, args)
        return results[0] if results else None

    def print_tables(self):
        """Helper method to print all stored data for debugging."""
        print("\n" + "="*50)
        print("[MockDatabase] Current Database Contents:")
        print("="*50)
        for table_name, records in self.tables.items():
            print(f"\n{table_name} ({len(records)} records):")
            for record in records:
                print(f"  {record}")
        print("="*50 + "\n")

    def __del__(self):
        """Cleanup - prints final state when database is destroyed."""
        if hasattr(self, 'connection') and self.connection:
            print("[MockDatabase] Closing mock database connection")
            # Optionally print final state
            # self.print_tables()


class MockCursor:
    """Mock cursor for query execution."""

    def __init__(self, database, sql, args):
        self.database = database
        self.sql = sql
        self.args = args
        self.rowcount = 0
        self.with_rows = False
        self._results = []

    def execute(self, sql, args):
        """Execute mock query."""
        pass

    def executemany(self, sql, args):
        """Execute mock query with multiple rows."""
        pass

    def fetchall(self):
        """Fetch all results."""
        return self._results

    def fetchone(self):
        """Fetch one result."""
        return self._results[0] if self._results else None

    def close(self):
        """Close cursor."""
        pass
