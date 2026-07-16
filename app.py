from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length, Regexp
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transport_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
with app.app_context():
    db.create_all()

# Models
class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    vehicle_id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='vehicle', lazy=True)

class Driver(db.Model):
    __tablename__ = 'drivers'
    driver_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(10), nullable=False)
    phone_number = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default='available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='driver', lazy=True)

class Route(db.Model):
    __tablename__ = 'routes'
    route_id = db.Column(db.Integer, primary_key=True)
    route_name = db.Column(db.String(100), nullable=False)
    start_location = db.Column(db.String(100), nullable=False)
    end_location = db.Column(db.String(100), nullable=False)
    distance_km = db.Column(db.Numeric(10, 2), nullable=False)
    estimated_time_minutes = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='route', lazy=True)

class Booking(db.Model):
    __tablename__ = 'bookings'
    booking_id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.vehicle_id'))
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.driver_id'))
    route_id = db.Column(db.Integer, db.ForeignKey('routes.route_id'))
    booking_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Forms
class VehicleForm(FlaskForm):
    vehicle_number = StringField('Vehicle Number', validators=[DataRequired()])
    vehicle_type = SelectField('Vehicle Type', choices=[
        ('car', 'Car'),
        ('truck', 'Truck'),
        ('bus', 'Bus')
    ], validators=[DataRequired()])
    capacity = IntegerField('Capacity', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Add Vehicle')

class DriverForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    license_number = StringField('License Number', validators=[
        DataRequired(),
        Length(min=10, max=10, message='License number must be exactly 10 digits'),
        Regexp('^[0-9]{10}$', message='License number must contain only numbers')
    ])
    phone_number = StringField('Phone Number', validators=[
        DataRequired(),
        Length(min=10, max=10, message='Phone number must be exactly 10 digits'),
        Regexp('^[0-9]{10}$', message='Phone number must contain only numbers')
    ])
    submit = SubmitField('Add Driver')

class RouteForm(FlaskForm):
    route_name = StringField('Route Name', validators=[DataRequired()])
    start_location = StringField('Start Location', validators=[DataRequired()])
    end_location = StringField('End Location', validators=[DataRequired()])
    distance_km = IntegerField('Distance (km)', validators=[DataRequired(), NumberRange(min=1)])
    estimated_time_minutes = IntegerField('Estimated Time (minutes)', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Add Route')

class BookingForm(FlaskForm):
    vehicle_id = SelectField('Vehicle', coerce=int, validators=[DataRequired()])
    driver_id = SelectField('Driver', coerce=int, validators=[DataRequired()])
    route_id = SelectField('Route', coerce=int, validators=[DataRequired()])
    booking_date = DateField('Booking Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ])
    submit = SubmitField('Create Booking')

# Routes
@app.route('/')
def index():
    vehicles = Vehicle.query.all()
    drivers = Driver.query.all()
    routes = Route.query.all()
    bookings = Booking.query.all()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    return render_template('index.html', 
                         vehicles=vehicles,
                         drivers=drivers,
                         routes=routes,
                         bookings=bookings,
                         recent_bookings=recent_bookings)

@app.route('/vehicles', methods=['GET', 'POST'])
def vehicles():
    form = VehicleForm()
    if form.validate_on_submit():
        vehicle = Vehicle(
            vehicle_number=form.vehicle_number.data,
            vehicle_type=form.vehicle_type.data,
            capacity=form.capacity.data
        )
        db.session.add(vehicle)
        db.session.commit()
        flash('Vehicle added successfully!', 'success')
        return redirect(url_for('vehicles'))
    vehicles = Vehicle.query.all()
    return render_template('vehicles.html', form=form, vehicles=vehicles)

@app.route('/drivers', methods=['GET', 'POST'])
def drivers():
    form = DriverForm()
    if form.validate_on_submit():
        driver = Driver(
            name=form.name.data,
            license_number=form.license_number.data,
            phone_number=form.phone_number.data
        )
        db.session.add(driver)
        db.session.commit()
        flash('Driver added successfully!', 'success')
        return redirect(url_for('drivers'))
    drivers = Driver.query.all()
    return render_template('drivers.html', form=form, drivers=drivers)

@app.route('/routes', methods=['GET', 'POST'])
def routes():
    form = RouteForm()
    if form.validate_on_submit():
        route = Route(
            route_name=form.route_name.data,
            start_location=form.start_location.data,
            end_location=form.end_location.data,
            distance_km=form.distance_km.data,
            estimated_time_minutes=form.estimated_time_minutes.data
        )
        db.session.add(route)
        db.session.commit()
        flash('Route added successfully!', 'success')
        return redirect(url_for('routes'))
    routes = Route.query.all()
    return render_template('routes.html', form=form, routes=routes)

@app.route('/bookings', methods=['GET', 'POST'])
def bookings():
    form = BookingForm()
    
    # Get all available vehicles, drivers, and routes
    vehicles = Vehicle.query.all()
    drivers = Driver.query.all()
    routes = Route.query.all()
    
    # Set choices for the form
    form.vehicle_id.choices = [(v.vehicle_id, f"{v.vehicle_number} - {v.vehicle_type}") for v in vehicles]
    form.driver_id.choices = [(d.driver_id, d.name) for d in drivers]
    form.route_id.choices = [(r.route_id, f"{r.route_name} ({r.start_location} to {r.end_location})") for r in routes]
    
    if form.validate_on_submit():
        try:
            booking = Booking(
                vehicle_id=form.vehicle_id.data,
                driver_id=form.driver_id.data,
                route_id=form.route_id.data,
                booking_date=form.booking_date.data,
                status='pending'  # New bookings always start as pending
            )
            db.session.add(booking)
            db.session.commit()
            flash('Booking created successfully!', 'success')
            return redirect(url_for('bookings'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating booking: {str(e)}', 'danger')
    
    bookings = Booking.query.all()
    return render_template('bookings.html', form=form, bookings=bookings)

@app.route('/vehicles/edit/<int:id>', methods=['GET', 'POST'])
def edit_vehicle(id):
    vehicle = Vehicle.query.get_or_404(id)
    form = VehicleForm(obj=vehicle)
    if form.validate_on_submit():
        vehicle.vehicle_number = form.vehicle_number.data
        vehicle.vehicle_type = form.vehicle_type.data
        vehicle.capacity = form.capacity.data
        db.session.commit()
        flash('Vehicle updated successfully!', 'success')
        return redirect(url_for('vehicles'))
    return render_template('edit_vehicle.html', form=form, vehicle=vehicle)

@app.route('/vehicles/delete/<int:id>')
def delete_vehicle(id):
    vehicle = Vehicle.query.get_or_404(id)
    try:
        db.session.delete(vehicle)
        db.session.commit()
        flash('Vehicle deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting vehicle: {str(e)}', 'danger')
    return redirect(url_for('vehicles'))

@app.route('/drivers/edit/<int:id>', methods=['GET', 'POST'])
def edit_driver(id):
    driver = Driver.query.get_or_404(id)
    form = DriverForm(obj=driver)
    if form.validate_on_submit():
        driver.name = form.name.data
        driver.license_number = form.license_number.data
        driver.phone_number = form.phone_number.data
        db.session.commit()
        flash('Driver updated successfully!', 'success')
        return redirect(url_for('drivers'))
    return render_template('edit_driver.html', form=form, driver=driver)

@app.route('/drivers/delete/<int:id>')
def delete_driver(id):
    driver = Driver.query.get_or_404(id)
    try:
        db.session.delete(driver)
        db.session.commit()
        flash('Driver deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting driver: {str(e)}', 'danger')
    return redirect(url_for('drivers'))

@app.route('/routes/edit/<int:id>', methods=['GET', 'POST'])
def edit_route(id):
    route = Route.query.get_or_404(id)
    form = RouteForm(obj=route)
    
    if form.validate_on_submit():
        try:
            route.route_name = form.route_name.data
            route.start_location = form.start_location.data
            route.end_location = form.end_location.data
            route.distance_km = form.distance_km.data
            route.estimated_time_minutes = form.estimated_time_minutes.data
            
            db.session.commit()
            flash('Route updated successfully!', 'success')
            return redirect(url_for('routes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating route: {str(e)}', 'danger')
    
    return render_template('edit_route.html', form=form, route=route)

@app.route('/routes/delete/<int:id>')
def delete_route(id):
    route = Route.query.get_or_404(id)
    try:
        db.session.delete(route)
        db.session.commit()
        flash('Route deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting route: {str(e)}', 'danger')
    return redirect(url_for('routes'))

@app.route('/bookings/edit/<int:id>', methods=['GET', 'POST'])
def edit_booking(id):
    booking = Booking.query.get_or_404(id)
    form = BookingForm(obj=booking)
    
    # Get all available vehicles, drivers, and routes
    vehicles = Vehicle.query.all()
    drivers = Driver.query.all()
    routes = Route.query.all()
    
    # Set choices for the form
    form.vehicle_id.choices = [(v.vehicle_id, f"{v.vehicle_number} - {v.vehicle_type}") for v in vehicles]
    form.driver_id.choices = [(d.driver_id, d.name) for d in drivers]
    form.route_id.choices = [(r.route_id, f"{r.route_name} ({r.start_location} to {r.end_location})") for r in routes]
    
    if form.validate_on_submit():
        try:
            # Store old status for comparison
            old_status = booking.status
            
            # Update booking details
            booking.vehicle_id = form.vehicle_id.data
            booking.driver_id = form.driver_id.data
            booking.route_id = form.route_id.data
            booking.booking_date = form.booking_date.data
            booking.status = form.status.data
            
            # Update vehicle and driver status based on status change
            if old_status != booking.status:
                if booking.status == 'confirmed':
                    booking.vehicle.status = 'in_use'
                    booking.driver.status = 'on_duty'
                elif booking.status == 'completed' or booking.status == 'cancelled':
                    booking.vehicle.status = 'available'
                    booking.driver.status = 'available'
                elif booking.status == 'pending':
                    booking.vehicle.status = 'available'
                    booking.driver.status = 'available'
            
            db.session.commit()
            flash('Booking updated successfully!', 'success')
            return redirect(url_for('bookings'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating booking: {str(e)}', 'danger')
    
    return render_template('edit_booking.html', form=form, booking=booking)

@app.route('/bookings/update_status/<int:id>', methods=['POST'])
def update_booking_status(id):
    booking = Booking.query.get_or_404(id)
    new_status = request.form.get('status')
    
    if new_status not in ['pending', 'confirmed', 'completed', 'cancelled']:
        flash('Invalid status!', 'danger')
        return redirect(url_for('bookings'))
    
    try:
        booking.status = new_status
        
        # Update vehicle and driver status based on booking status
        if new_status == 'confirmed':
            booking.vehicle.status = 'in_use'
            booking.driver.status = 'on_duty'
        elif new_status == 'completed' or new_status == 'cancelled':
            booking.vehicle.status = 'available'
            booking.driver.status = 'available'
        
        db.session.commit()
        flash('Booking status updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating booking status: {str(e)}', 'danger')
    
    return redirect(url_for('bookings'))

@app.route('/bookings/delete/<int:id>')
def delete_booking(id):
    booking = Booking.query.get_or_404(id)
    try:
        db.session.delete(booking)
        db.session.commit()
        flash('Booking deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting booking: {str(e)}', 'danger')
    return redirect(url_for('bookings'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
