from datetime import datetime
from flask_login import UserMixin
from extensions import db
import bcrypt
import re


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)          # ← NEW: track last login
    phone_number = db.Column(db.String(20), nullable=True)      # ← NEW: phone number for SMS/WhatsApp
    child_name = db.Column(db.String(150), nullable=True)
    child_dob = db.Column(db.Date, nullable=True)

    vaccines = db.relationship('UserVaccine', backref='user', lazy='dynamic',
                               cascade='all, delete-orphan')
    predictions = db.relationship('PredictionLog', backref='user', lazy='dynamic',
                                  cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic',
                                    cascade='all, delete-orphan')

    # ── Password helpers ──────────────────────────────────────────
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode('utf-8'), self.password_hash.encode('utf-8')
        )

    @staticmethod
    def validate_password_strength(password: str) -> list:
        """
        Returns a list of error strings.  Empty list = password is valid.
        Requirements: ≥8 chars, ≥1 uppercase, ≥1 digit, ≥1 special char.
        """
        errors = []
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        if not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter.')
        if not re.search(r'\d', password):
            errors.append('Password must contain at least one number.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-\+\=\[\]\\\/]', password):
            errors.append('Password must contain at least one special character.')
        return errors

    # ── Age helpers ───────────────────────────────────────────────
    def get_age_in_months(self):
        today = datetime.today().date()
        dob = self.date_of_birth
        months = (today.year - dob.year) * 12 + (today.month - dob.month)
        return max(0, months)

    def get_age_in_years(self):
        return self.get_age_in_months() / 12

    def __repr__(self):
        return f'<User {self.email}>'


class Vaccine(db.Model):
    __tablename__ = 'vaccines'

    id = db.Column(db.Integer, primary_key=True)
    vaccine_name = db.Column(db.String(200), nullable=False)
    recommended_age_months = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    dose_number = db.Column(db.Integer, default=1)
    disease_prevented = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(100), nullable=True)

    user_vaccines = db.relationship('UserVaccine', backref='vaccine', lazy='dynamic')

    def get_recommended_age_display(self):
        months = self.recommended_age_months
        if months < 12:
            return f"{months} month{'s' if months != 1 else ''}"
        elif months % 12 == 0:
            years = months // 12
            return f"{years} year{'s' if years != 1 else ''}"
        else:
            years = months // 12
            rem = months % 12
            return f"{years}y {rem}m"

    def __repr__(self):
        return f'<Vaccine {self.vaccine_name}>'


class UserVaccine(db.Model):
    __tablename__ = 'user_vaccines'
    __table_args__ = (
        db.Index('ix_uv_user_id', 'user_id'),   # ← DB index for performance
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vaccine_id = db.Column(db.Integer, db.ForeignKey('vaccines.id'), nullable=False)
    status = db.Column(db.String(20), default='Pending')   # Completed / Pending
    date_taken = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<UserVaccine user={self.user_id} vaccine={self.vaccine_id} status={self.status}>'


class PredictionLog(db.Model):
    __tablename__ = 'prediction_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    risk_level = db.Column(db.String(20), nullable=False)   # High Risk / Low Risk
    risk_score = db.Column(db.Float, nullable=True)
    confidence = db.Column(db.Float, nullable=True)         # ← NEW: model confidence
    missed_count = db.Column(db.Integer, default=0)         # ← NEW: actual missed vaccines
    prediction_date = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<PredictionLog user={self.user_id} risk={self.risk_level}>'


class Reminder(db.Model):
    __tablename__ = 'reminders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    vaccine_id = db.Column(db.Integer, db.ForeignKey('vaccines.id'), nullable=False)
    days_before = db.Column(db.Integer, default=7)
    notify_time = db.Column(db.String(5), default='09:00')
    scheduled_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    email_sent = db.Column(db.Boolean, default=False)       # ← NEW: track email sent
    last_email_sent_at = db.Column(db.DateTime, nullable=True)  # ← NEW
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('reminders', lazy='dynamic',
                                                       cascade='all, delete-orphan'))
    vaccine = db.relationship('Vaccine', backref=db.backref('reminders', lazy='dynamic'))

    def __repr__(self):
        return f'<Reminder user={self.user_id} vaccine={self.vaccine_id} days={self.days_before}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')  # info, warning, danger, success
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Notification user={self.user_id} title={self.title} read={self.is_read}>'
