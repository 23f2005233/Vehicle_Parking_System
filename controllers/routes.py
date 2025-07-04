from app import app
from flask import render_template, request, redirect, url_for, flash, session
from controllers.database import db
from controllers.models import User, Role, ParkingLot, ParkingSpot, Reserve

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash('Email and password are required.', 'error')
            return redirect(url_for('login'))
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('User not found. Please register.', 'error')
            return redirect(url_for('register'))
        if user.password != password:
            flash('Incorrect password. Please try again.', 'error')
            return redirect(url_for('login'))
        session['email'] = user.email
        session['roles'] = [roles.role for roles in user.role]
        flash('Login successful!', 'success')
        return redirect(url_for('home'))
    
    
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    fullname = request.form.get('fullname')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    if not fullname or not email or not password or not confirm_password:
        flash('All fields are required.', 'error')
        return redirect(url_for('register'))
    if password != confirm_password:
        flash('Passwords do not match.', 'error')
        return redirect(url_for('register'))
    if len(password) < 8:
        flash('Password must be at least 8 characters long.', 'error')
        return redirect(url_for('register'))
    if User.query.filter_by(email=email).first():
        flash('Email already registered', 'error')
        return redirect(url_for('register'))
    address = request.form.get('address')
    pincode = request.form.get('pincode')
    phno = request.form.get('phno')
    new_user = User(fullname=fullname, email=email, password=password, address=address, pincode=pincode, phno=phno)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('roles', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))