import os
import sys
import getpass
from dotenv import load_dotenv

# Ensure the project root directory is in the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# Load environment variables from .env file
load_dotenv(os.path.join(project_root, '.env'))

from app import create_app, db
from app.models.user import User

app = create_app()

def create_superuser():
    """Creates an admin/superuser user in the database."""
    with app.app_context():
        print("Creating a new superuser...")
        
        while True:
            username = input("Enter username: ").strip()
            if not username:
                print("Username cannot be empty.")
                continue
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                print(f"Username '{username}' already exists. Please choose another.")
            else:
                break
                
        while True:
            name = input("Enter full name: ").strip()
            if name:
                break
            else:
                print("Name cannot be empty.")

        while True:
            password = getpass.getpass("Enter password: ")
            if not password:
                print("Password cannot be empty.")
                continue
            password_confirm = getpass.getpass("Confirm password: ")
            if password == password_confirm:
                break
            else:
                print("Passwords do not match. Please try again.")

        try:
            new_user = User(
                username=username,
                name=name,
                is_admin=True,
                is_superuser=True
            )
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            print(f"Superuser '{username}' created successfully with ID: {new_user.id}")
            
        except Exception as e:
            db.session.rollback()
            print(f"An error occurred: {e}")
            print("Failed to create superuser.")

if __name__ == "__main__":
    create_superuser() 