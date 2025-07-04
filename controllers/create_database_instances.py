from flask import current_app as app
from controllers.database import db
from controllers.models import User, Role, ParkingLot, ParkingSpot, Reserve
def create_tables():
    with app.app_context():
        db.create_all()
    User_role = Role.query.filter_by(role='User').first()
    if not User_role:
        # Create a default user role if it doesn't exist
        User_role = Role(role='User')
        db.session.add(User_role)
        db.session.commit()
    Admin_role = Role.query.filter_by(role='Admin').first()
    if not Admin_role:
        # Create a default admin role if it doesn't exist
        Admin_role = Role(role='Admin')
        db.session.add(Admin_role)
        db.session.commit()
    
    if not User.query.first():
        # Create a default admin user if no users exist
        admin_user = User(
            email = 'admin@vps',
            password = 'let me in, I am the admin',
            fullname = 'Admin User',
            address = '123 Admin Street',
            pincode = '123456',
            phno = '1234567890',
            role = [Admin_role]  # Assign the admin role to this user
        )
        db.session.add(admin_user)
        db.session.commit()
    
