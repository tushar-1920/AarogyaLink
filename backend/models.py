from extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import uuid, hashlib


def gen_patient_id():
    return "RH-" + uuid.uuid4().hex[:5].upper()

def gen_user_id():
    return "USR-" + uuid.uuid4().hex[:5].upper()

# ── Helper: generate patient ID ──────────────────────
def gen_patient_id():
    return 'RH-' + uuid.uuid4().hex[:5].upper()

def gen_doctor_id():
    return 'DR-' + uuid.uuid4().hex[:5].upper()

# ══════════════════════════════════════════════════════
#  PATIENT MODEL
# ══════════════════════════════════════════════════════
class Patient(db.Model):
    __tablename__ = 'patients'

    id           = db.Column(db.String(12), primary_key=True, default=gen_patient_id)
    name         = db.Column(db.String(120), nullable=False)
    age          = db.Column(db.Integer, nullable=False)
    gender       = db.Column(db.String(10))
    phone        = db.Column(db.String(15))
    village      = db.Column(db.String(100))
    district     = db.Column(db.String(100))
    state        = db.Column(db.String(100))
    blood_group  = db.Column(db.String(5))
    conditions   = db.Column(db.Text)       # comma-separated
    allergies    = db.Column(db.Text)       # comma-separated
    medications  = db.Column(db.Text)       # comma-separated
    emergency_contact = db.Column(db.String(15))
    abha_id      = db.Column(db.String(50), unique=True, nullable=True)
    photo_path   = db.Column(db.String(255))  # patient live photo
    qr_path      = db.Column(db.String(255))
    card_path    = db.Column(db.String(255))
    is_active    = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    visits       = db.relationship('Visit', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    registered_by = db.Column(db.String(12), db.ForeignKey('users.id'), nullable=True)

    def _clean_list(self, value):
        """Split comma-separated field, strip, and remove None/empty values."""
        SKIP = {'none', 'nil', 'n/a', 'no', 'na', ''}
        if not value:
            return []
        return [v.strip() for v in value.split(',') if v.strip().lower() not in SKIP]

    def conditions_list(self):
        return self._clean_list(self.conditions)

    def allergies_list(self):
        return self._clean_list(self.allergies)

    def medications_list(self):
        return self._clean_list(self.medications)

    def visit_count(self):
        return self.visits.count()

    def last_visit(self):
        return self.visits.order_by(Visit.visited_at.desc()).first()

    def __repr__(self):
        return f'<Patient {self.id} — {self.name}>'


# ══════════════════════════════════════════════════════
#  VISIT MODEL
# ══════════════════════════════════════════════════════
class Visit(db.Model):
    __tablename__ = 'visits'

    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id   = db.Column(db.String(12), db.ForeignKey('patients.id'), nullable=False)
    doctor_id    = db.Column(db.String(12), db.ForeignKey('users.id'), nullable=True)
    hospital     = db.Column(db.String(200))
    diagnosis    = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text)
    notes        = db.Column(db.Text)
    follow_up    = db.Column(db.Date, nullable=True)
    visit_type   = db.Column(db.String(50), default='OPD')  # OPD, Emergency, Follow-up
    visited_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Visit {self.id} — Patient {self.patient_id}>'


# ══════════════════════════════════════════════════════
#  USER MODEL (ASHA workers, Doctors, Admins)
# ══════════════════════════════════════════════════════
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id            = db.Column(db.String(12), primary_key=True, default=gen_user_id)
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    phone         = db.Column(db.String(15))
    password_hash = db.Column(db.String(256))
    role          = db.Column(db.String(20), default="asha")   # asha | doctor | admin

    # Professional details
    speciality      = db.Column(db.String(100), nullable=True)
    hospital        = db.Column(db.String(200), nullable=True)
    district        = db.Column(db.String(100))
    state           = db.Column(db.String(100))
    aadhar_number   = db.Column(db.String(20),  nullable=True)
    license_number  = db.Column(db.String(50),  nullable=True)  # medical registration no.

    # Document uploads (paths relative to static/)
    aadhar_doc      = db.Column(db.String(255), nullable=True)   # ASHA + doctor
    degree_doc      = db.Column(db.String(255), nullable=True)   # doctor only
    certificate_doc = db.Column(db.String(255), nullable=True)   # doctor: medical reg cert

    # Admin verification
    is_verified   = db.Column(db.Boolean,  default=False)
    is_active     = db.Column(db.Boolean,  default=True)
    verify_status = db.Column(db.String(20), default="pending")  # pending|approved|rejected
    verify_note   = db.Column(db.Text,     nullable=True)
    verified_by   = db.Column(db.String(12), nullable=True)
    verified_at   = db.Column(db.DateTime,   nullable=True)

    # Online consultation / telemedicine
    photo_path    = db.Column(db.String(255), nullable=True)   # live photo for online profile
    payment_qr    = db.Column(db.String(255), nullable=True)   # UPI QR image path
    payment_upi   = db.Column(db.String(100), nullable=True)   # UPI ID string
    consult_fee   = db.Column(db.Integer,     default=200)      # fee in rupees

    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    last_login  = db.Column(db.DateTime, nullable=True)

    patients_registered = db.relationship("Patient", backref="registrar",
                                           foreign_keys="Patient.registered_by", lazy="dynamic")
    visits_recorded     = db.relationship("Visit", backref="doctor",
                                           foreign_keys="Visit.doctor_id", lazy="dynamic")

    def set_password(self, pw):
        self.password_hash = hashlib.sha256(pw.encode()).hexdigest()

    def check_password(self, pw):
        return self.password_hash == hashlib.sha256(pw.encode()).hexdigest()

    def is_doctor(self): return self.role == "doctor"
    def is_asha(self):   return self.role == "asha"
    def is_admin(self):  return self.role == "admin"

    def can_access(self):
        return self.role == "admin" or self.is_verified

    def status_color(self):
        return {"pending": "amber", "approved": "green", "rejected": "red"}.get(
            self.verify_status, "gray")

    def docs_uploaded(self):
        return sum(1 for d in [self.aadhar_doc, self.degree_doc, self.certificate_doc] if d)

    def __repr__(self): return f"<User {self.id} {self.name} ({self.role})>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# ══════════════════════════════════════════════════════
#  MEDICAL DOCUMENT MODEL  — patient's previous reports
# ══════════════════════════════════════════════════════
class MedicalDocument(db.Model):
    __tablename__ = "medical_documents"

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id  = db.Column(db.String(12), db.ForeignKey("patients.id"), nullable=False)
    uploaded_by = db.Column(db.String(12), db.ForeignKey("users.id"),    nullable=True)
    doc_type    = db.Column(db.String(50),  default="report")   # report|prescription|lab|xray|other
    title       = db.Column(db.String(200), nullable=False)      # e.g. "Blood test 12 Jan 2025"
    file_path   = db.Column(db.String(255), nullable=False)      # relative to static/
    file_type   = db.Column(db.String(10))                       # pdf|jpg|png
    notes       = db.Column(db.Text, nullable=True)
    doc_date    = db.Column(db.Date, nullable=True)              # date of the report itself
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient  = db.relationship("Patient", backref=db.backref("documents", lazy="dynamic"))
    uploader = db.relationship("User",    foreign_keys=[uploaded_by])

    def icon(self):
        return {"pdf": "📄", "jpg": "🖼️", "jpeg": "🖼️", "png": "🖼️"}.get(
            (self.file_type or "").lower(), "📎")

    def is_image(self):
        return (self.file_type or "").lower() in ["jpg", "jpeg", "png"]

    def __repr__(self): return f"<MedicalDocument {self.id} — {self.patient_id}>"

# ══════════════════════════════════════════════════════
#  ONLINE PATIENT MODEL  — patients who register online
#  (different from ASHA-registered patients)
# ══════════════════════════════════════════════════════
def gen_online_patient_id():
    return 'OP-' + uuid.uuid4().hex[:6].upper()

class OnlinePatient(db.Model, UserMixin):
    __tablename__ = 'online_patients'

    id            = db.Column(db.String(12), primary_key=True, default=gen_online_patient_id)
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    phone         = db.Column(db.String(15),  nullable=False)
    password_hash = db.Column(db.String(256))
    age           = db.Column(db.Integer)
    gender        = db.Column(db.String(10))
    blood_group   = db.Column(db.String(5))
    address       = db.Column(db.String(300))
    aadhar_number = db.Column(db.String(20))

    # Documents uploaded at registration
    aadhar_doc    = db.Column(db.String(255))   # path to aadhar image/pdf
    medical_doc1  = db.Column(db.String(255))   # previous reports (optional)
    medical_doc2  = db.Column(db.String(255))
    photo_path    = db.Column(db.String(255))   # live photo

    # Admin verification
    is_verified   = db.Column(db.Boolean, default=False)
    is_active     = db.Column(db.Boolean, default=True)
    verify_status = db.Column(db.String(20), default='pending')
    verify_note   = db.Column(db.Text, nullable=True)
    verified_at   = db.Column(db.DateTime, nullable=True)

    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_login    = db.Column(db.DateTime, nullable=True)

    # Relationships
    bookings      = db.relationship('Appointment', backref='online_patient',
                                    foreign_keys='Appointment.patient_id', lazy='dynamic')
    messages_received = db.relationship('ConsultMessage', backref='patient',
                                         foreign_keys='ConsultMessage.patient_id', lazy='dynamic')

    def set_password(self, pw):
        self.password_hash = hashlib.sha256(pw.encode()).hexdigest()

    def check_password(self, pw):
        return self.password_hash == hashlib.sha256(pw.encode()).hexdigest()

    def get_id(self):
        return f'op:{self.id}'

    def __repr__(self):
        return f'<OnlinePatient {self.id} {self.name}>'


# ══════════════════════════════════════════════════════
#  DOCTOR SLOT MODEL  — time slots generated by doctor
# ══════════════════════════════════════════════════════
class DoctorSlot(db.Model):
    __tablename__ = 'doctor_slots'

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    doctor_id     = db.Column(db.String(12), db.ForeignKey('users.id'), nullable=False)
    slot_date     = db.Column(db.Date,     nullable=False)
    slot_time     = db.Column(db.String(8), nullable=False)   # "10:00 AM"
    duration_mins = db.Column(db.Integer,  default=20)         # minutes per patient
    is_booked     = db.Column(db.Boolean,  default=False)
    is_available  = db.Column(db.Boolean,  default=True)       # doctor can mark unavailable
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    doctor        = db.relationship('User', backref=db.backref('slots', lazy='dynamic'))
    appointment   = db.relationship('Appointment', backref='slot', uselist=False)

    def __repr__(self):
        return f'<Slot {self.id} Dr.{self.doctor_id} {self.slot_date} {self.slot_time}>'


# ══════════════════════════════════════════════════════
#  APPOINTMENT MODEL
# ══════════════════════════════════════════════════════
class Appointment(db.Model):
    __tablename__ = 'appointments'

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    slot_id         = db.Column(db.Integer, db.ForeignKey('doctor_slots.id'), nullable=False)
    patient_id      = db.Column(db.String(12), db.ForeignKey('online_patients.id'), nullable=False)
    doctor_id       = db.Column(db.String(12), db.ForeignKey('users.id'), nullable=False)

    # Patient details at booking time
    symptoms        = db.Column(db.Text)
    report_doc      = db.Column(db.String(255))  # uploaded report/doc at booking

    # Payment
    fee             = db.Column(db.Integer, default=200)   # in rupees
    payment_status  = db.Column(db.String(20), default='pending')  # pending|submitted|verified|failed
    payment_screenshot = db.Column(db.String(255))   # screenshot uploaded by patient
    payment_note    = db.Column(db.String(300))       # doctor's note on payment

    # Status
    status          = db.Column(db.String(20), default='pending')
    # pending → payment_submitted → payment_verified → confirmed → completed | cancelled

    # Room for video call
    room_id         = db.Column(db.String(50))
    call_started_at = db.Column(db.DateTime, nullable=True)
    call_ended_at   = db.Column(db.DateTime, nullable=True)

    # Post-call
    prescription    = db.Column(db.Text, nullable=True)
    doctor_notes    = db.Column(db.Text, nullable=True)

    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    doctor          = db.relationship('User', backref=db.backref('doctor_appointments', lazy='dynamic'))

    def get_room_id(self):
        if not self.room_id:
            self.room_id = f'aarogya-{self.id}-{uuid.uuid4().hex[:6]}'
        return self.room_id

    def __repr__(self):
        return f'<Appointment {self.id} Patient:{self.patient_id} Dr:{self.doctor_id}>'


# ══════════════════════════════════════════════════════
#  CONSULT MESSAGE MODEL  — post-call doctor→patient msg
# ══════════════════════════════════════════════════════
class ConsultMessage(db.Model):
    __tablename__ = 'consult_messages'

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    doctor_id      = db.Column(db.String(12), db.ForeignKey('users.id'), nullable=False)
    patient_id     = db.Column(db.String(12), db.ForeignKey('online_patients.id'), nullable=False)
    message        = db.Column(db.Text, nullable=False)
    prescription   = db.Column(db.Text, nullable=True)
    is_read        = db.Column(db.Boolean, default=False)
    sent_at        = db.Column(db.DateTime, default=datetime.utcnow)

    appointment    = db.relationship('Appointment', backref=db.backref('messages', lazy='dynamic'))
    doctor         = db.relationship('User', backref=db.backref('sent_messages', lazy='dynamic'))

    def __repr__(self):
        return f'<ConsultMessage {self.id} appt:{self.appointment_id}>'