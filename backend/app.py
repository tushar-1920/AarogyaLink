import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from extensions import db, login_manager

def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder=os.path.abspath(Config.TEMPLATE_FOLDER),
        static_folder=os.path.abspath(Config.STATIC_FOLDER),
    )
    app.config.from_object(config_class)

    # Create database directory if using local SQLite
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI','')
    if 'sqlite' in db_uri and '///' in db_uri:
        db_path = db_uri.split('///')[1]
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    os.makedirs(app.config['QR_OUTPUT_DIR'],   exist_ok=True)
    os.makedirs(app.config['CARD_OUTPUT_DIR'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from routes.main      import main_bp, pages_bp
    from routes.patient   import patient_bp
    from routes.auth      import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.scan      import scan_bp
    from routes.admin        import admin_bp
    from routes.telemedicine import tele_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(patient_bp,   url_prefix='/patient')
    app.register_blueprint(auth_bp,      url_prefix='/auth')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(tele_bp)

    # Create upload dirs
    static = os.path.abspath(Config.STATIC_FOLDER)
    for folder in ['uploads/aadhar', 'uploads/degree', 'uploads/certificates',
                   'uploads/documents', 'uploads/op_photos', 'uploads/op_aadhar',
                   'uploads/op_reports', 'uploads/op_payments', 'uploads/doctor_qr',
                   'photos', 'qrcodes', 'cards']:
        os.makedirs(os.path.join(static, folder), exist_ok=True)

    with app.app_context():
        db.create_all()
        _migrate_add_columns()
        _seed_admin()
        _seed_demo_data()

    return app


def _migrate_add_columns():
    """Auto-migrate DB — adds missing columns and creates missing tables."""
    try:
        with db.engine.connect() as conn:

            # ── patients table ─────────────────────────────────────
            res  = conn.execute(db.text("PRAGMA table_info(patients)"))
            cols = [r[1] for r in res.fetchall()]
            for col, typ in [
                ("photo_path", "VARCHAR(255)"),
                ("updated_at", "DATETIME"),
            ]:
                if col not in cols:
                    conn.execute(db.text(f"ALTER TABLE patients ADD COLUMN {col} {typ}"))
                    conn.commit()

            # ── users table ────────────────────────────────────────
            res  = conn.execute(db.text("PRAGMA table_info(users)"))
            cols = [r[1] for r in res.fetchall()]
            for col, typ in [
                ("aadhar_number",  "VARCHAR(20)"),
                ("license_number", "VARCHAR(50)"),
                ("aadhar_doc",     "VARCHAR(255)"),
                ("degree_doc",     "VARCHAR(255)"),
                ("certificate_doc","VARCHAR(255)"),
                ("verify_status",  "VARCHAR(20) DEFAULT 'pending'"),
                ("verify_note",    "TEXT"),
                ("verified_by",    "VARCHAR(12)"),
                ("verified_at",    "DATETIME"),
                ("photo_path",     "VARCHAR(255)"),
                ("payment_qr",     "VARCHAR(255)"),
                ("payment_upi",    "VARCHAR(100)"),
                ("consult_fee",    "INTEGER DEFAULT 200"),
            ]:
                if col not in cols:
                    conn.execute(db.text(f"ALTER TABLE users ADD COLUMN {col} {typ}"))
                    conn.commit()

            # ── medical_documents ──────────────────────────────────
            res = conn.execute(db.text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='medical_documents'"))
            if not res.fetchone():
                conn.execute(db.text("""
                    CREATE TABLE medical_documents (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_id  VARCHAR(12) NOT NULL REFERENCES patients(id),
                        uploaded_by VARCHAR(12) REFERENCES users(id),
                        doc_type    VARCHAR(50)  DEFAULT 'report',
                        title       VARCHAR(200) NOT NULL,
                        file_path   VARCHAR(255) NOT NULL,
                        file_type   VARCHAR(10),
                        notes       TEXT,
                        doc_date    DATE,
                        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
                print("[AarogyaLink] Created medical_documents table")

            # ── online_patients ────────────────────────────────────
            res = conn.execute(db.text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='online_patients'"))
            if not res.fetchone():
                conn.execute(db.text("""
                    CREATE TABLE online_patients (
                        id            VARCHAR(12) PRIMARY KEY,
                        name          VARCHAR(120) NOT NULL,
                        email         VARCHAR(150) UNIQUE NOT NULL,
                        phone         VARCHAR(15)  NOT NULL,
                        password_hash VARCHAR(256),
                        age           INTEGER,
                        gender        VARCHAR(10),
                        blood_group   VARCHAR(5),
                        address       VARCHAR(300),
                        aadhar_number VARCHAR(20),
                        aadhar_doc    VARCHAR(255),
                        medical_doc1  VARCHAR(255),
                        medical_doc2  VARCHAR(255),
                        photo_path    VARCHAR(255),
                        is_verified   BOOLEAN DEFAULT 1,
                        is_active     BOOLEAN DEFAULT 1,
                        verify_status VARCHAR(20) DEFAULT 'approved',
                        verify_note   TEXT,
                        verified_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_login    DATETIME
                    )
                """))
                conn.commit()
                print("[AarogyaLink] Created online_patients table")

            # ── doctor_slots ───────────────────────────────────────
            res = conn.execute(db.text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='doctor_slots'"))
            if not res.fetchone():
                conn.execute(db.text("""
                    CREATE TABLE doctor_slots (
                        id            INTEGER PRIMARY KEY AUTOINCREMENT,
                        doctor_id     VARCHAR(12) NOT NULL REFERENCES users(id),
                        slot_date     DATE        NOT NULL,
                        slot_time     VARCHAR(8)  NOT NULL,
                        duration_mins INTEGER DEFAULT 20,
                        is_booked     BOOLEAN DEFAULT 0,
                        is_available  BOOLEAN DEFAULT 1,
                        created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
                print("[AarogyaLink] Created doctor_slots table")

            # ── appointments ───────────────────────────────────────
            res = conn.execute(db.text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'"))
            if not res.fetchone():
                conn.execute(db.text("""
                    CREATE TABLE appointments (
                        id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                        slot_id            INTEGER     NOT NULL REFERENCES doctor_slots(id),
                        patient_id         VARCHAR(12) NOT NULL REFERENCES online_patients(id),
                        doctor_id          VARCHAR(12) NOT NULL REFERENCES users(id),
                        symptoms           TEXT,
                        report_doc         VARCHAR(255),
                        fee                INTEGER DEFAULT 200,
                        payment_status     VARCHAR(20) DEFAULT 'pending',
                        payment_screenshot VARCHAR(255),
                        payment_note       VARCHAR(300),
                        status             VARCHAR(20) DEFAULT 'pending',
                        room_id            VARCHAR(50),
                        call_started_at    DATETIME,
                        call_ended_at      DATETIME,
                        prescription       TEXT,
                        doctor_notes       TEXT,
                        created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at         DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
                print("[AarogyaLink] Created appointments table")

            # ── consult_messages ───────────────────────────────────
            res = conn.execute(db.text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='consult_messages'"))
            if not res.fetchone():
                conn.execute(db.text("""
                    CREATE TABLE consult_messages (
                        id             INTEGER PRIMARY KEY AUTOINCREMENT,
                        appointment_id INTEGER     NOT NULL REFERENCES appointments(id),
                        doctor_id      VARCHAR(12) NOT NULL REFERENCES users(id),
                        patient_id     VARCHAR(12) NOT NULL REFERENCES online_patients(id),
                        message        TEXT        NOT NULL,
                        prescription   TEXT,
                        is_read        BOOLEAN DEFAULT 0,
                        sent_at        DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
                print("[AarogyaLink] Created consult_messages table")

            print("[AarogyaLink] DB schema up to date ✅")

    except Exception as e:
        print(f"[AarogyaLink] Migration warning: {e}")


def _seed_admin():
    from models import User
    EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@aarogyalink.in')
    PWD   = os.environ.get('ADMIN_PASSWORD', 'Admin@2025#Secure')
    if not User.query.filter_by(email=EMAIL).first():
        a = User(
            name          = "AarogyaLink Admin",
            email         = EMAIL,
            role          = "admin",
            is_verified   = True,
            verify_status = "approved",
            is_active     = True,
            district      = "All Districts",
            state         = "All States",
        )
        a.set_password(PWD)
        db.session.add(a)
        db.session.commit()
        print(f"[AarogyaLink] Admin created: {EMAIL}")


def _seed_demo_data():
    from models import Patient
    if Patient.query.count() == 0:
        demo = Patient(
            id='RH-DEMO1', name='Ramesh Kumar', age=52,
            gender='Male', phone='9876543210',
            village='Sahnewal', district='Ludhiana', state='Punjab',
            blood_group='B+',
            conditions='Diabetes Type 2, Hypertension',
            allergies='Penicillin',
            medications='Metformin 500mg, Amlodipine 5mg',
            emergency_contact='9876543211',
        )
        db.session.add(demo)
        db.session.commit()
        print("[AarogyaLink] Demo patient seeded")


if __name__ == '__main__':
    app = create_app()

    PORT = int(os.environ.get('PORT', 5000))
    print()
    print('  ╔══════════════════════════════════════════╗')
    print('  ║         AarogyaLink is running! 🌿       ║')
    print('  ╠══════════════════════════════════════════╣')
    print(f'  ║  Local:   http://localhost:{PORT}          ║')
    print(f'  ║  Network: http://0.0.0.0:{PORT}            ║')
    print('  ╠══════════════════════════════════════════╣')
    print('  ║  Press CTRL+C to stop the server         ║')
    print('  ╚══════════════════════════════════════════╝')
    print()

    app.run(host='0.0.0.0', port=PORT, debug=False)