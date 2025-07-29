from app import app
from flask import render_template, request, redirect, url_for, flash, session
from controllers.database import db
from controllers.models import User, Role, ParkingLot, ParkingSpot, Reserve
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend for matplotlib
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from collections import defaultdict

@app.route('/')
def home():
    if not session.get('email'):
        parking_lots_locations = [loc[0] for loc in db.session.query(ParkingLot.prime_location_name).all()]
        return render_template('info.html', parking_lots_locations=parking_lots_locations)
    parking_lots = ParkingLot.query.all()
    def get_spots_count(parking_lot):
        return ParkingSpot.query.filter_by(pl_id=parking_lot.pl_id, status='O').count()
    def get_spots(parking_lot):
        return ParkingSpot.query.filter_by(pl_id=parking_lot.pl_id).all()
    def reserved_spots():
        if session.get('email') is not None:
            user = User.query.filter_by(email=session.get('email')).first()
            if user:
                return Reserve.query.filter_by(u_id=user.u_id).all()
            else:
                return []
    def get_user_id(email):
        return int(User.query.filter_by(email = email).first().u_id)

    return render_template('home.html', parking_lots=parking_lots, get_spots_count=get_spots_count, get_spots=get_spots, reserved_spots=reserved_spots, get_user_id = get_user_id)

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
        session['user_id'] = user.u_id
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
    new_user = User(fullname=fullname, email=email, password=password, address=address, pincode=pincode, phno=phno, role=[Role.query.filter_by(role='User').first()])
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('roles', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/users')
def users():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/add_parking_lot', methods=['POST'])
def add_parking_lot():
    if request.method == 'POST':
        prime_location_name = request.form.get('prime_location_name')
        price = request.form.get('price')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        max_spots = request.form.get('max_spots')
        
        if not prime_location_name or not price or not address or not pincode or not max_spots:
            flash('All fields are required.', 'error')
            return redirect(url_for('home'))
        
        new_parking_lot = ParkingLot(
            prime_location_name=prime_location_name, 
            price=float(price), 
            address=address, 
            pincode=pincode, 
            max_spots=int(max_spots))
        db.session.add(new_parking_lot)
        db.session.commit()

        for i in range(new_parking_lot.max_spots):
            new_spot = ParkingSpot(pl_id=new_parking_lot.pl_id, spot_number=int(i + 1))
            db.session.add(new_spot)
        db.session.commit()

        flash('Parking lot & parking spots added successfully!', 'success')
        return redirect(url_for('home'))

@app.route('/reserve/<int:lot_id>', methods=['GET', 'POST'])
def reserve(lot_id, ps_id=None):
    lot_id = int(lot_id)
    if request.method == 'GET':
        available_spot = ParkingSpot.query.filter_by(pl_id=lot_id, status='A').first()
        if not available_spot:
            flash('No available parking spots in this lot.', 'error')
            return redirect(url_for('home'))
        start_time = datetime.now()
        return render_template(
            'reserve.html',
            lot_id=lot_id,
            ps=available_spot,
            start_time=start_time
        )
    ps_id = request.form.get('ps_id')
    start_time = request.form.get('start_time')
    vehicle_number = request.form.get('vehicle_number')
    if not vehicle_number or not start_time or not ps_id:
        flash('All fields are required.', 'error')
        return redirect(url_for('reserve', lot_id=lot_id))
    user = User.query.filter_by(email=session.get('email')).first()
    if not user:
        flash('User not logged in.', 'error')
        return redirect(url_for('login'))
    new_reservation = Reserve(
        u_id=user.u_id,
        ps_id=int(ps_id),
        pl_id=int(lot_id),
        start_time=datetime.fromisoformat(start_time),
        vehicle_number=vehicle_number,
    )
    ps = ParkingSpot.query.filter_by(ps_id=int(ps_id)).first()
    ps.status = 'O'
    ps.vehicle_number = vehicle_number
    db.session.add(new_reservation)
    db.session.commit()
    flash('Reservation successful!', 'success')
    return redirect(url_for('home'))

@app.route('/edit_parking_lot/<int:lot_id>', methods=['GET', 'POST'])
def edit_parking_lot(lot_id):
    lot_id = int(lot_id)
    if request.method == 'GET':
        if not session.get('email'):
            flash('You must be logged in to edit parking lots.', 'error')
            return redirect(url_for('login'))
        if 'Admin' in session.get('roles', []):
            lot = ParkingLot.query.filter_by(pl_id=lot_id).first()
            if not lot:
                flash('Parking lot not found.', 'error')
                return redirect(url_for('home'))
            return render_template('edit_parking_lot.html', lot=lot)
        else:
            flash('You do not have permission to edit parking lots.', 'error')
            return redirect(url_for('home'))

    if request.method == 'POST':
        lot = ParkingLot.query.filter_by(pl_id=lot_id).first()
        if not lot:
            flash('Parking lot not found.', 'error')
            return redirect(url_for('home'))

        previous_spots = int(lot.max_spots)
        previous_price = float(lot.price)
        lot.prime_location_name = request.form.get('prime_location_name', lot.prime_location_name)
        new_price = float(request.form.get('price', lot.price))
        lot.address = request.form.get('address', lot.address)
        lot.pincode = request.form.get('pincode', lot.pincode)
        new_max_spots = int(request.form.get('max_spots', lot.max_spots))
        lot.max_spots = new_max_spots

        if new_price != previous_price:
            spots = ParkingSpot.query.filter_by(pl_id=lot_id).all()
            for spot in spots:
                spot.price = new_price

        lot.price = new_price

        if previous_spots == new_max_spots:
            pass
        elif previous_spots < new_max_spots:
            for i in range(previous_spots + 1, new_max_spots + 1):
                new_spot = ParkingSpot(pl_id=lot_id, spot_number=i)
                db.session.add(new_spot)
        else:
            flash("Spots cannot be deleted with edit function","message")
            if (new_price != previous_price):
                flash("Price updated successfully!","success")

        db.session.commit()
        flash('Parking lot updated successfully!', 'success')
        return redirect(url_for('home'))

@app.route('/delete_parking_lot/<int:lot_id>', methods=['GET','POST'])
def delete_parking_lot(lot_id):
    lot_id = int(lot_id)
    if not session.get('email'):
        flash('You must be logged in to delete a parking lot.', 'error')
        return render_template('delete_parking_lot.html')
    lot = ParkingLot.query.filter_by(pl_id=lot_id).first()
    if not lot:
        flash('Parking lot not found.', 'error')
        return redirect(url_for('home'))
    spots = ParkingSpot.query.filter_by(pl_id=lot_id).all()
    for spot in spots:
        if spot.status == 'O':
            flash('Parking spot is reserved by someone so cannot delete the parking lot', 'error')
            return redirect(url_for('home'))
    for spot in spots:
        db.session.delete(spot)
    db.session.delete(lot)
    db.session.commit()
    flash('Deletion successful', 'success')
    return redirect(url_for('home'))

@app.route('/release/<int:spot_id>', methods=['GET', 'POST'])
def release(spot_id):
    spot_id = int(spot_id)
    def calculate_payment(reservation):
        start = reservation.start_time
        end = reservation.end_time or datetime.now()
        duration = (end - start).total_seconds() // 3600  # hours
        if duration < 1:
            duration = 1
        spot = ParkingSpot.query.filter_by(ps_id=reservation.ps_id).first()
        lot = ParkingLot.query.filter_by(pl_id=spot.pl_id).first()
        price_per_hour = lot.price
        total = round(duration * price_per_hour, 2)
        return total, duration
    user = User.query.filter_by(email=session.get('email')).first()
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('login'))

    reservation = Reserve.query.filter_by(ps_id=spot_id, u_id=user.u_id).order_by(Reserve.start_time.desc()).first()

    reserved_spot = ParkingSpot.query.filter_by(ps_id=spot_id).first()
    if not reserved_spot or reserved_spot.status != 'O':
        flash('Spot not reserved.', 'error')
        return redirect(url_for('home'))

    reservation = Reserve.query.filter_by(ps_id=spot_id, u_id=User.query.filter_by(email=session.get('email')).first().u_id).order_by(Reserve.start_time.desc()).first()
    if not reservation:
        flash('Reservation not found.', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'GET':
        total_payment, duration = calculate_payment(reservation)
        return render_template('payment.html', total=total_payment, duration=duration, lot=reserved_spot.parking_lot, spot=reserved_spot)
    
    if request.method == 'POST':
        total_payment, _ = calculate_payment(reservation)
        reservation.payment = total_payment
        reservation.end_time = datetime.now()
        reserved_spot.vehicle_number = None
        reserved_spot.status = 'A'  
        reservation.released = True
        db.session.add(reservation)
        db.session.add(reserved_spot)
        db.session.commit()
        return redirect(url_for('home'))

@app.route('/my_profile', methods=['GET'])
def my_profile():
    user = User.query.filter_by(email = session.get('email')).first()
    return render_template('my_profile.html', user = user)
    
@app.route('/edit_profile/<int:user_id>', methods = ['GET','POST'])
def edit_profile (user_id):
    user_id = int(user_id)
    if request.method == 'GET':
        user = User.query.filter_by(u_id = int(user_id)).first()
        return render_template('edit_profile.html', user = user)
    if request.method == 'POST':
        if session.get('email'):
            user = User.query.filter_by(u_id = int(user_id)).first()
            user.email = request.form.get('email', user.email)
            previous_password = request.form.get('previous_password')
            if(previous_password != user.password):
                flash("Wrong password!!!","error")
                return redirect(url_for('edit_profile', user_id = user.u_id))
            pwd = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            if pwd != confirm_password:
                flash('Passwords do not match.', 'error')
                return redirect(url_for('edit_profile', user_id = user.u_id))
            if len(pwd) < 8:
                flash('Password must be at least 8 characters long.', 'error')
                return redirect(url_for('edit_profile', user_id = user.u_id))
            user.password = pwd
            user.address = request.form.get('address', user.address)
            user.pincode = request.form.get('pincode', user.pincode)
            user.phno = request.form.get('phno', user.phno)
            db.session.commit()
        flash('Profile updated successfully','success')
        return redirect(url_for('my_profile'))
    
@app.route('/reservation/<int:spot_id>', methods=['GET'])
def reservation(spot_id):
    spot_id = int(spot_id)
    reservation = Reserve.query.filter_by(ps_id=spot_id).order_by(Reserve.start_time.desc()).first()
    if not reservation:
        flash('No reservation found for this spot.', 'error')
        return redirect(url_for('home'))
    
    spot = ParkingSpot.query.filter_by(ps_id=spot_id).first()
    if not spot:
        flash('Parking spot not found.', 'error')
        return redirect(url_for('home'))
    
    lot = ParkingLot.query.filter_by(pl_id=spot.pl_id).first()
    if not lot:
        flash('Parking lot not found.', 'error')
        return redirect(url_for('home'))
    
    user = User.query.filter_by(u_id=reservation.u_id).first()
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('home'))
    
    def estimated_cost(start_time, price_per_hour):
        price_per_hour = float(price_per_hour)
        if reservation.end_time:
            end_time = reservation.end_time
        else:
            end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 3600
        return round(duration * price_per_hour, 2)
    return render_template('reservation_details.html', reservation=reservation, spot=spot, lot=lot, user = user, estimated_cost=estimated_cost)

@app.route('/user_details/<int:user_id>')
def user_details(user_id):
    user = User.query.get_or_404(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('users'))
    reservations = Reserve.query.filter_by(u_id=user_id).all()
    total_usage = len(reservations)
    if total_usage == 0:
        total_duration = 0
    else:
        total_duration = sum([(r.end_time - r.start_time).total_seconds() / 3600 for r in reservations if r.end_time and r.start_time])
    return render_template('user_details.html', user=user, reservations=reservations, total_usage=total_usage, total_duration=total_duration)

def group_reservations_by_month(reservations, now=None):
    revenue_by_month = defaultdict(float)
    reservations_by_month = defaultdict(int)
    
    for r in reservations:
        date = r.start_time or now
        if not date:
            continue
        month_key = date.strftime('%Y-%m')  # Example: '2025-07'
        reservations_by_month[month_key] += 1
        if r.payment:
            revenue_by_month[month_key] += r.payment
            
    return revenue_by_month, reservations_by_month

@app.route('/admin_summary')
def admin_summary():
    users = User.query.all()
    spots = ParkingSpot.query.all()
    reservations = Reserve.query.all()
    if not users or not spots or not reservations:
        flash('No data available for summary.', 'error')
        return redirect(url_for('home'))
    total_users = len(users)
    total_spots = len(spots)
    total_reservations = len(reservations)
    active_reservations = Reserve.query.filter(Reserve.end_time == None).count()

    durations = [
        (r.end_time - r.start_time).total_seconds() / 3600
        for r in reservations if r.start_time and r.end_time
    ]
    avg_duration = round(sum(durations) / len(durations), 2) if durations else 0

    total_revenue = sum(r.payment for r in reservations if r.payment is not None)

    spot_usage = {}
    for r in reservations:
        spot_usage[r.ps_id] = spot_usage.get(r.ps_id, 0) + 1
    
    plt.figure(figsize=(6, 6))
    plt.pie(spot_usage.values(), labels=spot_usage.keys(), autopct='%1.1f%%')
    plt.title("Parking Spot Usage Distribution")
    buf1 = BytesIO()
    plt.savefig(buf1, format='png')
    buf1.seek(0)
    spot_usage_chart = base64.b64encode(buf1.read()).decode('utf-8')
    plt.close()

    user_reservations = {}
    for r in reservations:
        uname = r.user.fullname
        user_reservations[uname] = user_reservations.get(uname, 0) + 1
    
    plt.figure(figsize=(8, 4))
    plt.bar(user_reservations.keys(), user_reservations.values(), color='teal')
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Reservations")
    plt.title("User-wise Reservation Count")
    plt.tight_layout()
    buf2 = BytesIO()
    plt.savefig(buf2, format='png')
    buf2.seek(0)
    user_res_chart = base64.b64encode(buf2.read()).decode('utf-8')
    plt.close()

    now = datetime.now()
    revenue_by_month, reservations_by_month = group_reservations_by_month(reservations, now)

    # Month-wise Revenue Chart
    months = sorted(revenue_by_month.keys())
    revenues = [revenue_by_month[m] for m in months]

    plt.figure(figsize=(8, 4))
    plt.bar(months, revenues, color='green')
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Revenue (₹)")
    plt.title("Month-wise Revenue")
    plt.tight_layout()
    buf3 = BytesIO()
    plt.savefig(buf3, format='png')
    buf3.seek(0)
    monthly_revenue_chart = base64.b64encode(buf3.read()).decode('utf-8')
    plt.close()

    # Month-wise Reservations Chart
    res_counts = [reservations_by_month[m] for m in months]

    plt.figure(figsize=(8, 4))
    plt.bar(months, res_counts, color='orange')
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Reservations")
    plt.title("Month-wise Reservations")
    plt.tight_layout()
    buf4 = BytesIO()
    plt.savefig(buf4, format='png')
    buf4.seek(0)
    monthly_res_chart = base64.b64encode(buf4.read()).decode('utf-8')
    plt.close()

    return render_template("admin_summary.html",
                           total_users=total_users,
                           total_spots=total_spots,
                           total_reservations=total_reservations,
                           active_reservations=active_reservations,
                           avg_duration=avg_duration,
                           spot_usage_chart=spot_usage_chart,
                           user_res_chart=user_res_chart,
                           total_revenue=total_revenue,
                           monthly_revenue_chart=monthly_revenue_chart,
                           monthly_res_chart=monthly_res_chart)


@app.route('/user_summary')
def user_summary():
    user_id = session.get('user_id')
    now = datetime.now()

    # Fetch all completed reservations
    reservations = Reserve.query.filter_by(u_id=user_id).order_by(Reserve.start_time.desc()).all()

    total_usage    = len(reservations)
    total_duration = sum(((r.end_time or now) - r.start_time).total_seconds() / 3600 for r in reservations)
    total_cost     = sum(r.payment for r in reservations if r.end_time)

    # Fetch active reservation if any (one with no end_time)
    active_reservation = Reserve.query.filter_by(u_id=user_id, end_time=None).first()

    revenue_by_month, reservations_by_month = group_reservations_by_month(reservations, now)

    months = sorted(reservations_by_month.keys())
    revenues = [revenue_by_month[m] for m in months]
    res_counts = [reservations_by_month[m] for m in months]

    # Reservations Chart
    plt.figure(figsize=(8, 4))
    plt.bar(months, res_counts, color='skyblue')
    plt.xticks(rotation=45)
    plt.ylabel("Reservations")
    plt.title("Your Month-wise Reservations")
    plt.tight_layout()
    buf6 = BytesIO()
    plt.savefig(buf6, format='png')
    buf6.seek(0)
    user_monthly_res_chart = base64.b64encode(buf6.read()).decode('utf-8')
    plt.close()

    return render_template(
      'user_summary.html',
      reservations=reservations,
      total_usage=total_usage,
      total_duration=total_duration,
      total_cost=total_cost,
      active_reservation=active_reservation,
      now=now,
      user_monthly_res_chart=user_monthly_res_chart
    )