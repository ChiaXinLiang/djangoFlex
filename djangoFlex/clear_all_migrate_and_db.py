import os
import shutil

def clear_migrations_and_db():
    # Remove the database file
    if os.path.exists('db.sqlite3'):
        os.remove('db.sqlite3')
        print("Removed db.sqlite3")

    # Remove all migration files except __init__.py
    for root, dirs, files in os.walk('.'):
        if 'migrations' in dirs:
            migrations_dir = os.path.join(root, 'migrations')
            for file in os.listdir(migrations_dir):
                if file != '__init__.py':
                    file_path = os.path.join(migrations_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
            print(f"Cleared migrations in {migrations_dir}")

    print("All migrations and database have been cleared.")

if __name__ == "__main__":
    clear_migrations_and_db()
