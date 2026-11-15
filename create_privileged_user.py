
from getpass import getpass

from backend.app.database import SessionLocal
from backend.app.models import User
from backend.app.security import hash_password


# Create an Admin or Gate Staff account securely
def create_privileged_user():

    print("\n=== EventSphere Account Creation ===")
    print("1. Admin")
    print("2. Gate Staff")

    role_choice = input("Select account type (1 or 2): ").strip()

    # Determine the account role
    roles = {
        "1": "admin",
        "2": "gate_staff"
    }

    if role_choice not in roles:
        print("Invalid role selection.")
        return

    role = roles[role_choice]

    # Collect account information
    full_name = input("Enter full name: ").strip()
    email = input("Enter email: ").strip().lower()

    if not full_name or not email:
        print("Name and email are required.")
        return

    password = getpass("Enter password: ")
    confirm_password = getpass("Confirm password: ")

    if len(password) < 8:
        print("Password must contain at least 8 characters.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    db = SessionLocal()

    try:
        # Check whether the email is already registered
        existing_user = db.query(User).filter(
            User.email == email
        ).first()

        if existing_user:
            print("An account with this email already exists.")
            return

        # Hash the password before storing it
        new_user = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role=role,
            is_active=True
        )

        # Save the new account in PostgreSQL
        db.add(new_user)
        db.commit()

        print(f"\n{role.title()} account created successfully!")

    except Exception as error:
        db.rollback()
        print("Account creation failed:", error)

    finally:
        db.close()


if __name__ == "__main__":
    create_privileged_user()
