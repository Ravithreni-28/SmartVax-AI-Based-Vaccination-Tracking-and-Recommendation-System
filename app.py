import os
import sys
import io
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, date, timedelta
from flask import (Flask, render_template, redirect, url_for, flash, request,
                   jsonify, session, send_file, send_from_directory, abort)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from functools import wraps

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from extensions import db, login_manager, csrf, mail, limiter


# ══════════════════════════════════════════════════════════════════════════════
#  LOGGING SETUP
# ══════════════════════════════════════════════════════════════════════════════
def setup_logging(app):
    """Configure rotating file logger + stream handler."""
    log_level = logging.DEBUG if app.config.get('DEBUG') else logging.INFO
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Stream handler (console)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(log_level)

    # File handler (rotate at 5 MB, keep 3 backups)
    os.makedirs('logs', exist_ok=True)
    file_handler = RotatingFileHandler(
        'logs/smartvax.log', maxBytes=5 * 1024 * 1024, backupCount=3
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    app.logger.addHandler(stream_handler)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)
    app.logger.info('SmartVax logging initialized.')


# ══════════════════════════════════════════════════════════════════════════════
#  APPLICATION FACTORY
# ══════════════════════════════════════════════════════════════════════════════
def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    setup_logging(app)
    return app


app = create_app()

# ── Import models & seed database ────────────────────────────────────────────
with app.app_context():
    from models.models import User, Vaccine, UserVaccine, PredictionLog, Reminder
    from models.seed_vaccines import seed_vaccines
    db.create_all()
    seed_vaccines(app)

    # Migrate: add new columns if they don't exist yet
    _migrations = [
        'ALTER TABLE users ADD COLUMN last_login DATETIME',
        'ALTER TABLE prediction_logs ADD COLUMN confidence REAL',
        'ALTER TABLE prediction_logs ADD COLUMN missed_count INTEGER DEFAULT 0',
        'ALTER TABLE reminders ADD COLUMN scheduled_date DATE',
        'ALTER TABLE reminders ADD COLUMN email_sent BOOLEAN DEFAULT 0',
        'ALTER TABLE reminders ADD COLUMN last_email_sent_at DATETIME',
        'ALTER TABLE users ADD COLUMN phone_number VARCHAR(20)',
    ]
    for _sql in _migrations:
        try:
            db.session.execute(db.text(_sql))
            db.session.commit()
        except Exception:
            db.session.rollback()   # Column already exists — that's fine


# ══════════════════════════════════════════════════════════════════════════════
#  EMAIL REMINDER SCHEDULER  (APScheduler — background thread)
# ══════════════════════════════════════════════════════════════════════════════
def send_vaccine_reminder_email(app_ctx, user_id: int, reminder_id: int):
    """Send a reminder email for a specific reminder record."""
    with app_ctx.app_context():
        from models.models import User, Reminder
        from flask_mail import Message

        reminder = Reminder.query.get(reminder_id)
        if not reminder or not reminder.is_active:
            return

        user = User.query.get(user_id)
        if not user:
            return

        vaccine = reminder.vaccine
        if not vaccine:
            return

        # Calculate days until due
        if reminder.scheduled_date:
            days_until = (reminder.scheduled_date - date.today()).days
        else:
            age_months = user.get_age_in_months()
            months_diff = vaccine.recommended_age_months - age_months
            days_until = int(months_diff * 30.44)

        is_overdue = days_until < 0
        priority = 'HIGH ⚠️' if is_overdue else 'Upcoming 📅'

        subject = (
            f'[SmartVax] ⚠️ Vaccine OVERDUE: {vaccine.vaccine_name}'
            if is_overdue
            else f'[SmartVax] 🔔 Vaccine Due Soon: {vaccine.vaccine_name}'
        )

        body_html = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f8f9fa;padding:20px;">
        <div style="max-width:600px;margin:auto;background:#fff;border-radius:12px;
                    padding:30px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
          <h2 style="color:#2563eb;margin-bottom:4px;">💉 SmartVax Reminder</h2>
          <p style="color:#6b7280;margin-top:0;">Vaccination Health Tracker</p>
          <hr style="border-color:#e5e7eb;">

          <p>Hi <strong>{user.name}</strong>,</p>
          <p>This is a reminder about your upcoming vaccination:</p>

          <div style="background:{'#fef2f2' if is_overdue else '#eff6ff'};border-left:4px solid
               {'#ef4444' if is_overdue else '#2563eb'};padding:16px;border-radius:8px;margin:20px 0;">
            <h3 style="margin:0 0 8px;color:{'#dc2626' if is_overdue else '#1d4ed8'};">
              {vaccine.vaccine_name}
            </h3>
            <p style="margin:4px 0;color:#374151;">
              📋 <strong>Priority:</strong> {priority}
            </p>
            <p style="margin:4px 0;color:#374151;">
              ⏰ <strong>Status:</strong>
              {'OVERDUE by ' + str(abs(days_until)) + ' days' if is_overdue
               else 'Due in ' + str(days_until) + ' days'}
            </p>
            {'<p style="margin:4px 0;color:#374151;">📅 <strong>Appointment:</strong> '
             + reminder.scheduled_date.strftime('%d %B %Y')
             + '</p>' if reminder.scheduled_date else ''}
            {'<p style="margin:4px 0;color:#374151;">🛡️ <strong>Prevents:</strong> '
             + vaccine.disease_prevented + '</p>' if vaccine.disease_prevented else ''}
          </div>

          <p>Please visit your nearest healthcare provider to get this vaccine as soon as possible.</p>

          <div style="text-align:center;margin:24px 0;">
            <a href="#" style="background:#2563eb;color:#fff;padding:12px 28px;
               border-radius:8px;text-decoration:none;font-weight:600;">
              Open SmartVax Dashboard
            </a>
          </div>

          <hr style="border-color:#e5e7eb;">
          <p style="font-size:12px;color:#9ca3af;">
            ⚠️ This is an automated reminder from SmartVax. For medical advice,
            always consult your healthcare provider.
          </p>
        </div>
        </body></html>
        """

        # Also create an In-App Notification (Backup for email)
        try:
            from models.models import Notification
            new_notif = Notification(
                user_id=user.id,
                title=f"Upcoming Vaccine: {vaccine.vaccine_name}",
                message=f"Reminder: Your vaccine '{vaccine.vaccine_name}' is {'OVERDUE' if is_overdue else 'due soon'}. Please visit your provider.",
                type='danger' if is_overdue else 'info'
            )
            db.session.add(new_notif)
            db.session.commit()
        except Exception as ne:
            app_ctx.logger.error(f"Failed to create in-app notification: {ne}")
            
        try:
            from extensions import mail as _mail
            msg = Message(
                subject=subject,
                recipients=[user.email],
                html=body_html,
                sender=app_ctx.config.get('MAIL_DEFAULT_SENDER', 'SmartVax <noreply@smartvax.com>')
            )
            _mail.send(msg)
            # Mark email as sent
            reminder.email_sent = True
            reminder.last_email_sent_at = datetime.utcnow()
            db.session.commit()
            app_ctx.logger.info(f'Email reminder sent to {user.email} for {vaccine.vaccine_name}')
        except Exception as e:
            app_ctx.logger.error(f'Failed to send reminder email to {user.email}: {e}')


def check_and_send_reminders():
    # MASTER SYNC FOR ALL OVERDUE VACCINES
    with app.app_context():
        from models.models import User, UserVaccine, Notification
        users = User.query.all()
        for u in users:
            age_m = u.get_age_in_months()
            overdue = UserVaccine.query.filter_by(user_id=u.id, status="Pending").all()
            for uv in overdue:
                if uv.vaccine.recommended_age_months <= age_m:
                    t = f"Due: {uv.vaccine.vaccine_name}"
                    if not Notification.query.filter_by(user_id=u.id, is_read=False, title=t).first():
                        db.session.add(Notification(user_id=u.id, title=t, message=f"{uv.vaccine.vaccine_name} is overdue.", type="danger"))
        db.session.commit()
    """Scheduled task: check all active reminders and send emails if due."""
    with app.app_context():
        from models.models import Reminder, User, Notification
        reminders = Reminder.query.filter_by(is_active=True).all()

        for reminder in reminders:
            try:
                user = reminder.user
                if not user or not user.email:
                    continue

                # Calculate days until due
                if reminder.scheduled_date:
                    days_until = (reminder.scheduled_date - date.today()).days
                else:
                    age_months = user.get_age_in_months()
                    months_diff = reminder.vaccine.recommended_age_months - age_months
                    days_until = int(months_diff * 30.44)

                should_notify = days_until < 0 or days_until <= reminder.days_before

                if not should_notify:
                    continue

                # Don't spam — skip if email sent in the last 24 hours
                if reminder.last_email_sent_at:
                    hours_since = (datetime.utcnow() - reminder.last_email_sent_at).total_seconds() / 3600
                    if hours_since < 24:
                        continue

                # Send the email
                # IN-APP NOTIFICATION ENGINE
                notif_t = f"Due: {reminder.vaccine.vaccine_name}"
                if not Notification.query.filter_by(user_id=user.id, is_read=False, title=notif_t).first():
                    db.session.add(Notification(user_id=user.id, title=notif_t, message=f"Vaccine {reminder.vaccine.vaccine_name} is due.", type="warning"))
                    db.session.commit()

                send_vaccine_reminder_email(app, user.id, reminder.id)

            except Exception as e:
                app.logger.error(f'Reminder check error for reminder {reminder.id}: {e}')


def start_scheduler():
    """Start APScheduler background job for email reminders."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = BackgroundScheduler(daemon=True)
        # Run every day at 09:00
        scheduler.add_job(
            func=check_and_send_reminders,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_reminder_check',
            name='Daily Vaccine Reminder Emails',
            replace_existing=True
        )
        scheduler.start()
        app.logger.info('[Scheduler] Daily reminder job started (runs at 09:00).')
        return scheduler
    except ImportError:
        app.logger.warning('[Scheduler] APScheduler not installed — email reminders disabled.')
        return None


# Start scheduler only in main process (not during reload or testing)
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    _scheduler = start_scheduler()


# ══════════════════════════════════════════════════════════════════════════════
#  USER LOADER
# ══════════════════════════════════════════════════════════════════════════════
@login_manager.user_loader
def load_user(user_id):
    from models.models import User
    return User.query.get(int(user_id))


# ══════════════════════════════════════════════════════════════════════════════
#  DECORATORS
# ══════════════════════════════════════════════════════════════════════════════
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


# ══════════════════════════════════════════════════════════════════════════════
#  CONTEXT PROCESSORS
# ══════════════════════════════════════════════════════════════════════════════
@app.context_processor
def inject_globals():
    return {
        'now': datetime.now(),
        'app_name': 'SmartVax'
    }


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — STATIC
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico', mimetype='image/x-icon'
    )


@app.route('/')
def index():
    return render_template('index.html')


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — AUTH
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/register', methods=['GET', 'POST'])
def register():
    from models.models import User, Vaccine, UserVaccine
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        dob_str = request.form.get('date_of_birth', '')
        child_name = request.form.get('child_name', '').strip()
        child_dob_str = request.form.get('child_dob', '').strip()
        phone_number = request.form.get('phone_number', '').strip()

        # Validation
        errors = []
        if not name or len(name) < 2:
            errors.append('Name must be at least 2 characters.')
        if not email or '@' not in email:
            errors.append('Please enter a valid email.')

        # ── Strong password validation ────────────────────────────────────
        pw_errors = User.validate_password_strength(password)
        errors.extend(pw_errors)

        if password != confirm_password:
            errors.append('Passwords do not match.')
        if not dob_str:
            errors.append('Date of birth is required.')
        if User.query.filter_by(email=email).first():
            errors.append('Email is already registered.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html')

        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'danger')
            return render_template('register.html')

        user = User(name=name, email=email, date_of_birth=dob, phone_number=phone_number)
        user.set_password(password)

        if child_name and child_dob_str:
            try:
                user.child_name = child_name
                user.child_dob = datetime.strptime(child_dob_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        db.session.add(user)
        db.session.flush()

        all_vaccines = Vaccine.query.all()
        for v in all_vaccines:
            uv = UserVaccine(user_id=user.id, vaccine_id=v.id, status='Pending')
            db.session.add(uv)

        db.session.commit()
        app.logger.info(f'[AUTH] New user registered: {email}')
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    from models.models import User
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=bool(remember))
            # ── Update last_login ─────────────────────────────────────────
            user.last_login = datetime.utcnow()
            db.session.commit()
            session.permanent = True
            app.logger.info(f'[AUTH] Login: {email}')
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.name}! 👋', 'success')
            return redirect(next_page or url_for('dashboard'))
        else:
            app.logger.warning(f'[AUTH] Failed login attempt: {email}')
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    app.logger.info(f'[AUTH] Logout: {current_user.email}')
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/dashboard')
@login_required
def dashboard():
    from models.models import Vaccine, UserVaccine, PredictionLog
    from ai_module.recommendation import recommender, predictor

    all_vaccines = Vaccine.query.all()
    user_vaccines = UserVaccine.query.filter_by(user_id=current_user.id).all()

    completed_ids = [uv.vaccine_id for uv in user_vaccines if uv.status == 'Completed']
    recs = recommender.get_recommendations(current_user.get_age_in_months(), completed_ids, all_vaccines)

    # Last vaccine date
    last_vaccine = UserVaccine.query.filter_by(
        user_id=current_user.id, status='Completed'
    ).order_by(UserVaccine.date_taken.desc()).first()

    days_since_last = 0
    if last_vaccine and last_vaccine.date_taken:
        days_since_last = (date.today() - last_vaccine.date_taken).days

    # ── Calculate actual missed vaccines (overdue ones) ────────────────────
    actual_missed = len(recs['due_now'])

    pred_result = predictor.predict({
        'age_months': current_user.get_age_in_months(),
        'completed_vaccines': recs['completed_count'],
        'pending_vaccines': recs['pending_count'],
        'days_since_last_vaccine': days_since_last,
        'num_missed_before': actual_missed,
        'has_child_profile': 1 if current_user.child_name else 0,
        'incomplete_series': max(0, recs['pending_count'] - recs['upcoming_count']),
    })

    # Save prediction log
    log = PredictionLog(
        user_id=current_user.id,
        risk_level=pred_result['risk_level'],
        risk_score=pred_result['risk_score'],
        confidence=pred_result['confidence'],
        missed_count=actual_missed,
        details=str(pred_result['recommendations'])
    )
    db.session.add(log)
    db.session.commit()

    app.logger.info(
        f'[PREDICTION] user={current_user.id} risk={pred_result["risk_level"]} '
        f'score={pred_result["risk_score"]} overdue={actual_missed}'
    )

    chart_data = {
        'completed': recs['completed_count'],
        'pending': recs['pending_count'],
        'upcoming': recs['upcoming_count']
    }

    return render_template('dashboard.html',
                           stats=recs,
                           due_now=recs['due_now_detailed'][:5],
                           upcoming=recs['upcoming_detailed'][:5],
                           prediction=pred_result,
                           chart_data=chart_data,
                           last_vaccine=last_vaccine,
                           next_vaccine=recs.get('next_vaccine'))


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — VACCINE SCHEDULE
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/schedule')
@login_required
def schedule():
    from models.models import Vaccine, UserVaccine
    from ai_module.recommendation import recommender

    all_vaccines = Vaccine.query.order_by(Vaccine.recommended_age_months).all()
    user_vaccines = UserVaccine.query.filter_by(user_id=current_user.id).all()
    uv_map = {uv.vaccine_id: uv for uv in user_vaccines}

    completed_ids = [vid for vid, uv in uv_map.items() if uv.status == 'Completed']
    recs = recommender.get_recommendations(current_user.get_age_in_months(), completed_ids, all_vaccines)

    schedule_items = []
    for v in all_vaccines:
        uv = uv_map.get(v.id)
        months_diff = v.recommended_age_months - current_user.get_age_in_months()

        if uv and uv.status == 'Completed':
            status_class = 'completed'
            status_label = 'Completed'
            priority_badge = 'success'
        elif months_diff <= 0:
            status_class = 'overdue'
            status_label = 'Overdue'
            priority_badge = 'danger'
        elif months_diff <= 3:
            status_class = 'upcoming'
            status_label = 'Upcoming'
            priority_badge = 'warning'
        else:
            status_class = 'future'
            status_label = 'Scheduled'
            priority_badge = 'info'

        schedule_items.append({
            'vaccine': v,
            'user_vaccine': uv,
            'status_class': status_class,
            'status_label': status_label,
            'priority_badge': priority_badge,
            'months_diff': months_diff
        })

    return render_template('schedule.html',
                           schedule_items=schedule_items,
                           stats=recs)


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — MARK COMPLETE
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/vaccine/mark_complete/<int:vaccine_id>', methods=['POST'])
@login_required
def mark_complete(vaccine_id):
    from models.models import UserVaccine
    uv = UserVaccine.query.filter_by(user_id=current_user.id, vaccine_id=vaccine_id).first()
    if uv:
        uv.status = 'Completed'
        date_taken_str = request.form.get('date_taken', '')
        if date_taken_str:
            try:
                uv.date_taken = datetime.strptime(date_taken_str, '%Y-%m-%d').date()
            except ValueError:
                uv.date_taken = date.today()
        else:
            uv.date_taken = date.today()
        uv.notes = request.form.get('notes', '')
        db.session.commit()
        flash('Vaccine marked as completed! ✅', 'success')
    else:
        flash('Vaccine record not found.', 'danger')
    return redirect(request.referrer or url_for('schedule'))


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — VACCINATION HISTORY
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/history')
@login_required
def history():
    from models.models import UserVaccine
    completed_vaccines = UserVaccine.query.filter_by(
        user_id=current_user.id, status='Completed'
    ).order_by(UserVaccine.date_taken.desc()).all()

    return render_template('history.html', completed_vaccines=completed_vaccines)


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — AI RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/recommendations')
@login_required
def recommendations():
    from models.models import Vaccine, UserVaccine, PredictionLog
    from ai_module.recommendation import recommender, predictor

    all_vaccines = Vaccine.query.all()
    user_vaccines = UserVaccine.query.filter_by(user_id=current_user.id).all()
    completed_ids = [uv.vaccine_id for uv in user_vaccines if uv.status == 'Completed']

    recs = recommender.get_recommendations(current_user.get_age_in_months(), completed_ids, all_vaccines)

    last_vaccine = UserVaccine.query.filter_by(
        user_id=current_user.id, status='Completed'
    ).order_by(UserVaccine.date_taken.desc()).first()

    days_since_last = 0
    if last_vaccine and last_vaccine.date_taken:
        days_since_last = (date.today() - last_vaccine.date_taken).days

    actual_missed = len(recs['due_now'])

    pred_result = predictor.predict({
        'age_months': current_user.get_age_in_months(),
        'completed_vaccines': recs['completed_count'],
        'pending_vaccines': recs['pending_count'],
        'days_since_last_vaccine': days_since_last,
        'num_missed_before': actual_missed,
        'has_child_profile': 1 if current_user.child_name else 0,
        'incomplete_series': max(0, recs['pending_count'] - recs['upcoming_count']),
    })

    prediction_history = PredictionLog.query.filter_by(
        user_id=current_user.id
    ).order_by(PredictionLog.prediction_date.desc()).limit(5).all()

    app.logger.info(
        f'[PREDICTION] Recommendations loaded: user={current_user.id} '
        f'risk={pred_result["risk_level"]} confidence={pred_result["confidence"]}%'
    )

    return render_template('recommendations.html',
                           recs=recs,
                           prediction=pred_result,
                           prediction_history=prediction_history,
                           age_months=current_user.get_age_in_months(),
                           age_years=round(current_user.get_age_in_years(), 1))


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — CHATBOT
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/chatbot')
@login_required
def chatbot_page():
    from ai_module.chatbot import chatbot
    suggestions = chatbot.get_suggestions()
    return render_template('chatbot.html', suggestions=suggestions)


@app.route('/api/chat', methods=['POST'])
@login_required
@limiter.limit("60 per minute")
def chat_api():
    from ai_module.chatbot import chatbot
    data = request.get_json()
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({'error': 'Empty message'}), 400

    response = chatbot.get_response(user_message)
    return jsonify(response)


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — REMINDERS
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/reminders')
@login_required
def reminders_page():
    from models.models import Reminder, Vaccine, UserVaccine

    user_vaccines = UserVaccine.query.filter(
        UserVaccine.user_id == current_user.id,
        UserVaccine.status != 'Completed'
    ).all()
    vaccine_ids = [uv.vaccine_id for uv in user_vaccines]
    vaccines = Vaccine.query.filter(
        Vaccine.id.in_(vaccine_ids)
    ).order_by(Vaccine.recommended_age_months).all()

    existing = {r.vaccine_id: r for r in Reminder.query.filter_by(user_id=current_user.id).all()}

    reminder_items = []
    for v in vaccines:
        months_diff = v.recommended_age_months - current_user.get_age_in_months()
        # Calculate days_until_due
        reminder = existing.get(v.id)
        if reminder and reminder.scheduled_date:
            days_until_due = (reminder.scheduled_date - date.today()).days
        else:
            days_until_due = int(months_diff * 30.44)

        if months_diff <= 0:
            status_label = 'Overdue'
            status_class = 'overdue'
        else:
            status_label = 'Upcoming'
            status_class = 'upcoming'

        should_notify = (reminder and reminder.is_active and
                         (days_until_due < 0 or days_until_due <= (reminder.days_before if reminder else 7)))

        reminder_items.append({
            'vaccine': v,
            'reminder': reminder,
            'status_label': status_label,
            'status_class': status_class,
            'months_diff': months_diff,
            'days_until_due': days_until_due,
            'should_notify': should_notify,
        })

    active_count = sum(1 for r in existing.values() if r.is_active)
    return render_template('reminders.html',
                           reminder_items=reminder_items,
                           active_count=active_count,
                           total_pending=len(vaccines))


@app.route('/reminders/set/<int:vaccine_id>', methods=['POST'])
@login_required
def set_reminder(vaccine_id):
    from models.models import Reminder, Vaccine
    vaccine = Vaccine.query.get_or_404(vaccine_id)
    days_before = int(request.form.get('days_before', 7))
    notify_time = request.form.get('notify_time', '09:00')
    is_active = request.form.get('is_active', 'true') == 'true'
    scheduled_date_str = request.form.get('scheduled_date', '').strip()

    scheduled_date = None
    if scheduled_date_str:
        try:
            scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    reminder = Reminder.query.filter_by(user_id=current_user.id, vaccine_id=vaccine_id).first()
    if reminder:
        reminder.days_before = days_before
        reminder.notify_time = notify_time
        reminder.is_active = is_active
        reminder.scheduled_date = scheduled_date
        reminder.updated_at = datetime.utcnow()
        flash(f'Reminder updated for {vaccine.vaccine_name}!', 'success')
    else:
        reminder = Reminder(
            user_id=current_user.id,
            vaccine_id=vaccine_id,
            days_before=days_before,
            notify_time=notify_time,
            is_active=is_active,
            scheduled_date=scheduled_date
        )
        db.session.add(reminder)
        flash(f'Reminder set for {vaccine.vaccine_name}! 🔔', 'success')

    db.session.commit()
    return redirect(url_for('reminders_page'))


@app.route('/reminders/delete/<int:reminder_id>', methods=['POST'])
@login_required
def delete_reminder(reminder_id):
    from models.models import Reminder
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=current_user.id).first_or_404()
    vaccine_name = reminder.vaccine.vaccine_name
    db.session.delete(reminder)
    db.session.commit()
    flash(f'Reminder for {vaccine_name} removed.', 'info')
    return redirect(url_for('reminders_page'))


@app.route('/reminders/toggle/<int:reminder_id>', methods=['POST'])
@login_required
def toggle_reminder(reminder_id):
    from models.models import Reminder
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=current_user.id).first_or_404()
    reminder.is_active = not reminder.is_active
    reminder.updated_at = datetime.utcnow()
    db.session.commit()
    status = 'activated ✅' if reminder.is_active else 'paused ⏸️'
    flash(f'Reminder {status} for {reminder.vaccine.vaccine_name}.', 'success')
    return redirect(url_for('reminders_page'))


@app.route('/api/reminders')
@login_required
def reminders_api():
    from models.models import Reminder
    reminders = Reminder.query.filter_by(user_id=current_user.id, is_active=True).all()
    data = []
    for r in reminders:
        if r.scheduled_date:
            days_until_due = (r.scheduled_date - date.today()).days
        else:
            age_months = current_user.get_age_in_months()
            months_diff = r.vaccine.recommended_age_months - age_months
            days_until_due = int(months_diff * 30.44)

        should_notify = days_until_due < 0 or days_until_due <= r.days_before
        data.append({
            'id': r.id,
            'vaccine_id': r.vaccine_id,
            'vaccine_name': r.vaccine.vaccine_name,
            'days_before': r.days_before,
            'notify_time': r.notify_time,
            'days_until_due': days_until_due,
            'should_notify': should_notify,
            'is_overdue': days_until_due < 0,
            'scheduled_date': r.scheduled_date.strftime('%d %b %Y') if r.scheduled_date else None,
        })
    return jsonify(data)


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — PDF REPORT (Enhanced)
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/download_report')
@login_required
def download_report():
    from models.models import UserVaccine
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.units import inch

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch
    )
    styles = getSampleStyleSheet()
    story = []

    # ── Colours ───────────────────────────────────────────────────────────
    PRIMARY   = colors.HexColor('#2563eb')
    SUCCESS   = colors.HexColor('#10b981')
    DANGER    = colors.HexColor('#ef4444')
    LIGHT_BG  = colors.HexColor('#f1f5f9')
    MUTED     = colors.HexColor('#6b7280')

    # ── Styles ────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        'SV_Title', parent=styles['Title'],
        fontSize=26, spaceAfter=4, textColor=PRIMARY, fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'SV_Subtitle', parent=styles['Normal'],
        fontSize=11, textColor=MUTED, spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'SV_Heading', parent=styles['Heading2'],
        fontSize=14, textColor=PRIMARY, spaceBefore=16, spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    normal_style = ParagraphStyle(
        'SV_Normal', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#374151')
    )

    # ── Header ────────────────────────────────────────────────────────────
    story.append(Paragraph('💉 SmartVax — Vaccination Report', title_style))
    story.append(Paragraph(
        f'Generated on: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}',
        subtitle_style
    ))
    story.append(HRFlowable(width='100%', thickness=2, color=PRIMARY))
    story.append(Spacer(1, 0.2 * inch))

    # ── Patient Information ───────────────────────────────────────────────
    story.append(Paragraph('Patient Information', heading_style))
    user_info = [
        ['Name:', current_user.name],
        ['Email:', current_user.email],
        ['Date of Birth:', current_user.date_of_birth.strftime('%B %d, %Y')],
        ['Age:', f'{current_user.get_age_in_months()} months ({round(current_user.get_age_in_years(), 1)} years)'],
    ]
    if current_user.child_name:
        user_info.append(['Child Name:', current_user.child_name])
        if current_user.child_dob:
            user_info.append(['Child DOB:', current_user.child_dob.strftime('%B %d, %Y')])

    t = Table(user_info, colWidths=[2 * inch, 4.5 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_BG),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('PADDING', (0, 0), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.15 * inch))

    # ── Summary Box ───────────────────────────────────────────────────────
    completed_all = UserVaccine.query.filter_by(
        user_id=current_user.id, status='Completed'
    ).all()
    pending_all = UserVaccine.query.filter_by(
        user_id=current_user.id, status='Pending'
    ).all()
    total = len(completed_all) + len(pending_all)
    pct = round(len(completed_all) / max(total, 1) * 100, 1)

    story.append(Paragraph('📊 Summary', heading_style))
    summary_data = [
        ['Total Vaccines', str(total)],
        ['Completed', f'{len(completed_all)}  ({pct}%)'],
        ['Pending / Overdue', str(len(pending_all))],
    ]
    st = Table(summary_data, colWidths=[3 * inch, 3.5 * inch])
    st.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1),
         [colors.white, LIGHT_BG, colors.HexColor('#fef2f2')]),
    ]))
    story.append(st)
    story.append(Spacer(1, 0.15 * inch))

    # ── Completed Vaccinations ────────────────────────────────────────────
    story.append(Paragraph('✅ Completed Vaccinations', heading_style))
    if completed_all:
        vax_data = [['Vaccine Name', 'Date Taken', 'Notes']]
        for uv in sorted(completed_all, key=lambda x: x.date_taken or date.min, reverse=True):
            vax_data.append([
                uv.vaccine.vaccine_name,
                uv.date_taken.strftime('%d %b %Y') if uv.date_taken else 'N/A',
                uv.notes or '—'
            ])
        vt = Table(vax_data, colWidths=[3 * inch, 1.5 * inch, 2 * inch])
        vt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), SUCCESS),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(vt)
    else:
        story.append(Paragraph('No completed vaccinations recorded yet.', normal_style))

    story.append(Spacer(1, 0.15 * inch))

    # ── Pending Vaccinations ──────────────────────────────────────────────
    story.append(Paragraph('⚠️ Pending / Overdue Vaccinations', heading_style))
    if pending_all:
        pend_data = [['Vaccine Name', 'Recommended Age', 'Disease Prevented']]
        for uv in pending_all:
            pend_data.append([
                uv.vaccine.vaccine_name,
                uv.vaccine.get_recommended_age_display(),
                uv.vaccine.disease_prevented or '—'
            ])
        pt = Table(pend_data, colWidths=[3 * inch, 1.5 * inch, 2 * inch])
        pt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), DANGER),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff5f5')]),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(pt)

    story.append(Spacer(1, 0.2 * inch))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#e5e7eb')))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        '⚠️ Disclaimer: This report is for informational purposes only. '
        'Always consult your healthcare provider for medical advice.',
        ParagraphStyle('disclaimer', parent=styles['Normal'],
                       fontSize=8, textColor=MUTED, italic=True)
    ))

    doc.build(story)
    buffer.seek(0)

    filename = (
        f"SmartVax_Report_{current_user.name.replace(' ', '_')}"
        f"_{datetime.now().strftime('%Y%m%d')}.pdf"
    )
    return send_file(buffer, mimetype='application/pdf',
                     as_attachment=True, download_name=filename)


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — ADMIN
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    from models.models import User, Vaccine, UserVaccine, PredictionLog
    users = User.query.all()
    vaccines = Vaccine.query.order_by(Vaccine.recommended_age_months).all()
    total_vaccinations = UserVaccine.query.filter_by(status='Completed').count()
    high_risk_count = PredictionLog.query.filter_by(risk_level='High Risk').count()
    return render_template('admin.html', users=users, vaccines=vaccines,
                           total_vaccinations=total_vaccinations,
                           high_risk_count=high_risk_count)


@app.route('/admin/add_vaccine', methods=['POST'])
@login_required
@admin_required
def admin_add_vaccine():
    from models.models import Vaccine, User, UserVaccine
    vaccine_name = request.form.get('vaccine_name', '').strip()
    recommended_age_months = int(request.form.get('recommended_age_months', 0))
    description = request.form.get('description', '').strip()
    dose_number = int(request.form.get('dose_number', 1))
    disease_prevented = request.form.get('disease_prevented', '').strip()
    category = request.form.get('category', 'Recommended').strip()

    if not vaccine_name:
        flash('Vaccine name is required.', 'danger')
        return redirect(url_for('admin_panel'))

    v = Vaccine(
        vaccine_name=vaccine_name,
        recommended_age_months=recommended_age_months,
        description=description,
        dose_number=dose_number,
        disease_prevented=disease_prevented,
        category=category
    )
    db.session.add(v)
    db.session.flush()

    for user in User.query.all():
        uv = UserVaccine(user_id=user.id, vaccine_id=v.id, status='Pending')
        db.session.add(uv)

    db.session.commit()
    app.logger.info(f'[ADMIN] Vaccine added: {vaccine_name}')
    flash(f'Vaccine "{vaccine_name}" added successfully!', 'success')
    return redirect(url_for('admin_panel'))


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES — API
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/api/vaccine_stats')
@login_required
def vaccine_stats_api():
    from models.models import UserVaccine
    completed = UserVaccine.query.filter_by(user_id=current_user.id, status='Completed').count()
    pending = UserVaccine.query.filter_by(user_id=current_user.id, status='Pending').count()
    return jsonify({
        'completed': completed,
        'pending': pending,
        'total': completed + pending
    })


@app.route('/api/send_test_reminder', methods=['POST'])
@login_required
def send_test_reminder():
    """Manually trigger a test reminder email for development/testing."""
    from models.models import Reminder
    r = Reminder.query.filter_by(user_id=current_user.id, is_active=True).first()
    if not r:
        return jsonify({'error': 'No active reminders found. Set a reminder first.'}), 400

    try:
        send_vaccine_reminder_email(app, current_user.id, r.id)
        return jsonify({'success': True, 'message': f'Test email sent to {current_user.email}'})
    except Exception as e:
        app.logger.error(f'Test email failed: {e}')
        return jsonify({'error': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ══════════════════════════════════════════════════════════════════════════════
@app.errorhandler(404)
def not_found(e):
    app.logger.warning(f'[404] {request.url}')
    return render_template('errors/404.html'), 404


@app.errorhandler(403)
def forbidden(e):
    app.logger.warning(f'[403] {request.url} — {current_user}')
    return render_template('errors/403.html'), 403


@app.errorhandler(500)
def server_error(e):
    app.logger.error(f'[500] {request.url}: {e}')
    return render_template('errors/500.html'), 500


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/admin/trigger-reminders', methods=['POST'])
@login_required
@admin_required
def trigger_reminders_manual():
    """Manually trigger the background reminder check."""
    try:
        check_and_send_reminders()
        flash('Manual reminder scan completed successfully.', 'success')
    except Exception as e:
        flash(f'Manual scan failed: {e}', 'danger')
    return redirect(url_for('admin_panel'))


@app.route('/admin/test-email', methods=['POST'])
@login_required
@admin_required
def test_email_config():
    """Send a simple test email to the current user."""
    from flask_mail import Message
    from extensions import mail as _mail
    
    try:
        msg = Message(
            subject='[SmartVax] SMTP Connection Test SUCCESS ✅',
            recipients=[current_user.email],
            body=f'Hi {current_user.name},\n\nIf you are reading this, your SMTP configuration is WORKING perfectly!\n\nSystem: SmartVax Health Platform\nTimestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            sender=app.config.get('MAIL_DEFAULT_SENDER')
        )
        _mail.send(msg)
        flash(f'Test email sent successfully to {current_user.email}!', 'success')
    except Exception as e:
        flash(f'SMTP Test Failed: {e}. Check your .env file and Gmail App Password settings.', 'danger')
    return redirect(url_for('admin_panel'))


@app.route('/api/notifications')
@login_required
def get_notifications():
    """Fetch unread notifications for the current user."""
    from models.models import Notification
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()
    # Also get count of unread
    from models.models import Reminder
    unread_count = Reminder.query.filter_by(user_id=current_user.id, is_active=True).count()
    
    return jsonify({
        'unread_count': unread_count,
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'created_at': n.created_at.strftime('%H:%M %d %b'),
            'is_read': n.is_read
        } for n in notifs]
    })


@app.route('/api/notifications/read', methods=['POST'])
@login_required
def mark_notifications_read():
    """Mark all notifications as read."""
    from models.models import Notification
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'status': 'success'})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_vaccines(app)

        from models.models import User, Vaccine, UserVaccine, Reminder
        if not User.query.filter_by(email='admin@smartvax.com').first():
            admin = User(
                name='Admin',
                email='admin@smartvax.com',
                date_of_birth=date(1990, 1, 1),
                role='admin'
            )
            admin.set_password('Admin@1234')
            db.session.add(admin)
            db.session.flush()

            all_vaccines = Vaccine.query.all()
            for v in all_vaccines:
                uv = UserVaccine(user_id=admin.id, vaccine_id=v.id, status='Pending')
                db.session.add(uv)

            db.session.commit()
            print('[OK] Admin user created: admin@smartvax.com / Admin@1234')

    print('[OK] SmartVax running at http://127.0.0.1:5000')
    app.run(debug=True, host='0.0.0.0', port=5000)
