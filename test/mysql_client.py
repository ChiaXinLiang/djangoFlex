import mysql.connector
from django.conf import settings

class MySQLClient:
    def __init__(self):
        self.connection = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host="localhost",
                port=3306,
                user="root",
                password="your_mysql_password",
                database="your_database_name"
            )
            return True
        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")
            return False

    def disconnect(self):
        if self.connection:
            self.connection.close()

    def create(self, table, data):
        if not self.connection:
            if not self.connect():
                return False, "Failed to connect to the database"

        try:
            cursor = self.connection.cursor()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['%s'] * len(data))
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            cursor.execute(query, list(data.values()))
            self.connection.commit()
            return True, cursor.lastrowid
        except mysql.connector.Error as err:
            return False, f"Error creating record: {err}"
        finally:
            cursor.close()

    def read(self, table, conditions=None):
        if not self.connection:
            if not self.connect():
                return False, "Failed to connect to the database"

        try:
            cursor = self.connection.cursor(dictionary=True)
            query = f"SELECT * FROM {table}"
            if conditions:
                where_clause = ' AND '.join([f"{k} = %s" for k in conditions.keys()])
                query += f" WHERE {where_clause}"
                cursor.execute(query, list(conditions.values()))
            else:
                cursor.execute(query)
            result = cursor.fetchall()
            return True, result
        except mysql.connector.Error as err:
            return False, f"Error reading records: {err}"
        finally:
            cursor.close()

    def update(self, table, data, conditions):
        if not self.connection:
            if not self.connect():
                return False, "Failed to connect to the database"

        try:
            cursor = self.connection.cursor()
            set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
            where_clause = ' AND '.join([f"{k} = %s" for k in conditions.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
            cursor.execute(query, list(data.values()) + list(conditions.values()))
            self.connection.commit()
            return True, cursor.rowcount
        except mysql.connector.Error as err:
            return False, f"Error updating records: {err}"
        finally:
            cursor.close()

    def delete(self, table, conditions):
        if not self.connection:
            if not self.connect():
                return False, "Failed to connect to the database"

        try:
            cursor = self.connection.cursor()
            where_clause = ' AND '.join([f"{k} = %s" for k in conditions.keys()])
            query = f"DELETE FROM {table} WHERE {where_clause}"
            cursor.execute(query, list(conditions.values()))
            self.connection.commit()
            return True, cursor.rowcount
        except mysql.connector.Error as err:
            return False, f"Error deleting records: {err}"
        finally:
            cursor.close()

    def run_classroom_data_example(self):
        # Create the classroom table if it doesn't exist
        self.create_classroom_table()

        # Create (Insert) a new classroom
        create_success, create_result = self.create('classroom', {
            'name': 'Math 101',
            'capacity': 30,
            'teacher': 'John Doe'
        })
        print(f"Create result: {'Success' if create_success else 'Failed'}, ID: {create_result}")

        # Read all classrooms
        read_success, read_result = self.read('classroom')
        print(f"Read all classrooms: {'Success' if read_success else 'Failed'}")
        for classroom in read_result:
            print(classroom)

        # Update the classroom
        update_success, update_result = self.update('classroom', 
            {'capacity': 35, 'teacher': 'Jane Smith'}, 
            {'name': 'Math 101'}
        )
        print(f"Update result: {'Success' if update_success else 'Failed'}, Rows affected: {update_result}")

        # Read the updated classroom
        read_updated_success, read_updated_result = self.read('classroom', {'name': 'Math 101'})
        print(f"Read updated classroom: {'Success' if read_updated_success else 'Failed'}")
        print(read_updated_result)

        # Delete the classroom
        delete_success, delete_result = self.delete('classroom', {'name': 'Math 101'})
        print(f"Delete result: {'Success' if delete_success else 'Failed'}, Rows affected: {delete_result}")

        # Confirm deletion
        confirm_delete_success, confirm_delete_result = self.read('classroom', {'name': 'Math 101'})
        print(f"Confirm deletion: {'Success' if confirm_delete_success else 'Failed'}")
        print(f"Deleted classroom should not be found: {confirm_delete_result}")

    def create_classroom_table(self):
        if not self.connection:
            if not self.connect():
                return False, "Failed to connect to the database"

        try:
            cursor = self.connection.cursor()
            query = """
            CREATE TABLE IF NOT EXISTS classroom (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                capacity INT,
                teacher VARCHAR(255)
            )
            """
            cursor.execute(query)
            self.connection.commit()
            return True, "Classroom table created successfully"
        except mysql.connector.Error as err:
            return False, f"Error creating classroom table: {err}"
        finally:
            cursor.close()

if __name__ == "__main__":
    client = MySQLClient()
    client.run_classroom_data_example()
    client.disconnect()
