from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from datetime import datetime, date, time
import bcrypt
from config import Config
from functools import wraps
import os

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='patient')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    medications = db.relationship('Medication', backref='user', lazy=True, cascade='all, delete-orphan')
    logs = db.relationship('Log', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def get_id(self):
        return str(self.user_id)

class Medication(db.Model):
    __tablename__ = 'medications'
    medication_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    medication_name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)
    instructions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    schedules = db.relationship('Schedule', backref='medication', lazy=True, cascade='all, delete-orphan')
    logs = db.relationship('Log', backref='medication', lazy=True, cascade='all, delete-orphan')

class Schedule(db.Model):
    __tablename__ = 'schedules'
    schedule_id = db.Column(db.Integer, primary_key=True)
    medication_id = db.Column(db.Integer, db.ForeignKey('medications.medication_id'), nullable=False)
    time = db.Column(db.Time, nullable=False)
    frequency = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    logs = db.relationship('Log', backref='schedule', lazy=True, cascade='all, delete-orphan')

class Log(db.Model):
    __tablename__ = 'logs'
    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    medication_id = db.Column(db.Integer, db.ForeignKey('medications.medication_id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.schedule_id'), nullable=False)
    taken_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum('taken', 'missed', 'skipped'), nullable=False)
    notes = db.Column(db.Text)

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class MedicationForm(FlaskForm):
    medication_name = StringField('Medication Name', validators=[DataRequired()])
    dosage = StringField('Dosage', validators=[DataRequired()])
    instructions = TextAreaField('Instructions')
    submit = SubmitField('Add Medication')

class ScheduleForm(FlaskForm):
    time = StringField('Time (HH:MM)', validators=[DataRequired()])
    frequency = SelectField('Frequency', choices=[
        ('daily', 'Daily'),
        ('twice_daily', 'Twice Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], validators=[DataRequired()])
    start_date = StringField('Start Date (YYYY-MM-DD)', validators=[DataRequired()])
    end_date = StringField('End Date (YYYY-MM-DD)')
    submit = SubmitField('Create Schedule')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered. Please login.', 'warning')
            return redirect(url_for('login'))
        
        hashed_password = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt())
        user = User(
            name=form.name.data,
            email=form.email.data,
            password=hashed_password.decode('utf-8')
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and bcrypt.checkpw(form.password.data.encode('utf-8'), user.password.encode('utf-8')):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    medications = Medication.query.filter_by(user_id=current_user.user_id).all()
    
    today = date.today()
    current_time = datetime.now().time()
    
    upcoming_schedules = []
    for med in medications:
        for schedule in med.schedules:
            if schedule.start_date <= today:
                if not schedule.end_date or schedule.end_date >= today:
                    if schedule.time > current_time:
                        upcoming_schedules.append({
                            'medication': med,
                            'schedule': schedule
                        })
    
    upcoming_schedules.sort(key=lambda x: x['schedule'].time)
    
    today_logs = Log.query.filter_by(
        user_id=current_user.user_id
    ).filter(
        db.func.date(Log.taken_time) == today
    ).all()
    
    return render_template('dashboard.html', 
                         medications=medications,
                         upcoming_schedules=upcoming_schedules,
                         today_logs=today_logs,
                         today=today)

@app.route('/medication/add', methods=['GET', 'POST'])
@login_required
def add_medication():
    form = MedicationForm()
    if form.validate_on_submit():
        medication = Medication(
            user_id=current_user.user_id,
            medication_name=form.medication_name.data,
            dosage=form.dosage.data,
            instructions=form.instructions.data
        )
        db.session.add(medication)
        db.session.commit()
        
        flash('Medication added successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_medication.html', form=form)

@app.route('/medication/<int:medication_id>/schedule/add', methods=['GET', 'POST'])
@login_required
def add_schedule(medication_id):
    medication = Medication.query.get_or_404(medication_id)
    
    if medication.user_id != current_user.user_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = ScheduleForm()
    if form.validate_on_submit():
        try:
            schedule_time = datetime.strptime(form.time.data, '%H:%M').time()
            start_date = datetime.strptime(form.start_date.data, '%Y-%m-%d').date()
            end_date = None
            if form.end_date.data:
                end_date = datetime.strptime(form.end_date.data, '%Y-%m-%d').date()
            
            schedule = Schedule(
                medication_id=medication_id,
                time=schedule_time,
                frequency=form.frequency.data,
                start_date=start_date,
                end_date=end_date
            )
            db.session.add(schedule)
            db.session.commit()
            
            flash('Schedule added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except ValueError:
            flash('Invalid date or time format.', 'danger')
    
    return render_template('add_schedule.html', form=form, medication=medication)

@app.route('/medication/<int:medication_id>/delete')
@login_required
def delete_medication(medication_id):
    medication = Medication.query.get_or_404(medication_id)
    
    if medication.user_id != current_user.user_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(medication)
    db.session.commit()
    
    flash('Medication deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/medication/<int:medication_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_medication(medication_id):
    medication = Medication.query.get_or_404(medication_id)
    
    if medication.user_id != current_user.user_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = MedicationForm(obj=medication)
    if form.validate_on_submit():
        medication.medication_name = form.medication_name.data
        medication.dosage = form.dosage.data
        medication.instructions = form.instructions.data
        db.session.commit()
        
        flash('Medication updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_medication.html', form=form, medication=medication)

@app.route('/log/<int:schedule_id>/<status>')
@login_required
def log_medication(schedule_id, status):
    if status not in ['taken', 'missed', 'skipped']:
        return jsonify({'error': 'Invalid status'}), 400
    
    schedule = Schedule.query.get_or_404(schedule_id)
    medication = Medication.query.get(schedule.medication_id)
    
    if medication.user_id != current_user.user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    log = Log(
        user_id=current_user.user_id,
        medication_id=schedule.medication_id,
        schedule_id=schedule_id,
        status=status
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Medication marked as {status}'})

@app.route('/history')
@login_required
def history():
    logs = Log.query.filter_by(user_id=current_user.user_id)\
        .order_by(Log.taken_time.desc())\
        .limit(100)\
        .all()
    
    return render_template('history.html', logs=logs)

@app.route('/reports')
@login_required
def reports():
    today = date.today()
    
    total_logs_today = Log.query.filter_by(
        user_id=current_user.user_id
    ).filter(
        db.func.date(Log.taken_time) == today
    ).count()
    
    taken_today = Log.query.filter_by(
        user_id=current_user.user_id,
        status='taken'
    ).filter(
        db.func.date(Log.taken_time) == today
    ).count()
    
    missed_today = Log.query.filter_by(
        user_id=current_user.user_id,
        status='missed'
    ).filter(
        db.func.date(Log.taken_time) == today
    ).count()
    
    adherence_rate = 0
    if total_logs_today > 0:
        adherence_rate = (taken_today / total_logs_today) * 100
    
    weekly_logs = Log.query.filter_by(
        user_id=current_user.user_id
    ).filter(
        Log.taken_time >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    ).all()
    
    return render_template('reports.html',
                         today=today,
                         taken_today=taken_today,
                         missed_today=missed_today,
                         adherence_rate=adherence_rate,
                         weekly_logs=weekly_logs)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.route('/setup-db')
def setup_db():
    try:
        db.create_all()
        return '✅ All tables created successfully!'
    except Exception as e:
        return f'❌ Error: {str(e)}'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
