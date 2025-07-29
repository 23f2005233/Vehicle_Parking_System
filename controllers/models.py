from controllers.database import db
class User(db.Model):
    u_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    fullname = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.String(6), nullable=False)
    phno = db.Column(db.String(10), nullable=False)
    role = db.relationship('Role', secondary='user_role')

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50), nullable=False)

class UserRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)

class ParkingLot(db.Model):
    pl_id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False) # Price per hour
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.String(6), nullable=False)
    max_spots = db.Column(db.Integer, nullable=False)

class ParkingSpot(db.Model):
    ps_id = db.Column(db.Integer, primary_key=True)
    pl_id = db.Column(db.Integer, db.ForeignKey('parking_lot.pl_id'), nullable=False)
    spot_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(1), nullable=False, default='A')   # O for Occupied, R for Reserved, A for Available
    vehicle_number = db.Column(db.String(15), nullable=True, default=None)
    parking_lot = db.relationship('ParkingLot', backref='parking_spot')

class Reserve(db.Model):
    r_id = db.Column(db.Integer, primary_key=True)
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id'), nullable=False)
    ps_id = db.Column(db.Integer, nullable=False)
    pl_id = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True, default=None)
    payment = db.Column(db.Float, nullable=False, default=0.0)
    released = db.Column(db.Boolean, default=False)
    vehicle_number = db.Column(db.String(15), nullable=True, default=None)
    user = db.relationship('User', backref='reservations')