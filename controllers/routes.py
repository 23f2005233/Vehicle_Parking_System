from app import app
from flask import render_template, request
from controllers.database import db
from controllers.models import User, Role, ParkingLot, ParkingSpot, Reserve

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')
    
@app.route('/register/submit', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    fullname = request.form['fullname']
    email = request.form['email']
    password = request.form['password']
    address = request.form['address']
    pincode = request.form['pincode']
    phno = request.form['phno']
    new_user = User(fullname=fullname, email=email, password=password, address=address, pincode=pincode, phno=phno)
    db.session.add(new_user)
    db.session.commit()