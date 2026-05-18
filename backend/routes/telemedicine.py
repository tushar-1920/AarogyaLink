from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, current_app, jsonify, session, g)
from models import (db, User, OnlinePatient, DoctorSlot, Appointment,
                    ConsultMessage)
from datetime import datetime, date, timedelta
import os, hashlib, base64, uuid

tele_bp = Blueprint('tele', __name__)

# ─── helpers ────────────────────────────────────────
def current_online_patient():
    uid = session.get('op_id')
    if uid:
        return OnlinePatient.query.get(uid)
    return None

def op_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_online_patient():
            flash('Please sign in to book an appointment.', 'error')
            return redirect(url_for('tele.op_login', next=request.url))
        return f(*args, **kwargs)
    return wrapper

def save_file(file_obj, folder, prefix):
    if not file_obj or file_obj.filename == '':
        return None
    ext  = os.path.splitext(file_obj.filename)[1].lower()
    if ext not in ['.jpg','.jpeg','.png','.pdf']:
        return None
    dest = os.path.join(current_app.static_folder, 'uploads', folder)
    os.makedirs(dest, exist_ok=True)
    fname = f'{prefix}_{uuid.uuid4().hex[:8]}{ext}'
    file_obj.save(os.path.join(dest, fname))
    return f'uploads/{folder}/{fname}'

def save_b64_photo(b64_data, folder, prefix):
    try:
        if ',' in b64_data:
            b64_data = b64_data.split(',', 1)[1]
        dest = os.path.join(current_app.static_folder, 'uploads', folder)
        os.makedirs(dest, exist_ok=True)
        fname = f'{prefix}_{uuid.uuid4().hex[:8]}.jpg'
        with open(os.path.join(dest, fname), 'wb') as f:
            f.write(base64.b64decode(b64_data))
        return f'uploads/{folder}/{fname}'
    except Exception as e:
        current_app.logger.warning(f'Photo save failed: {e}')
        return None


# ══════════════════════════════════════════════════════
#  ONLINE PATIENT AUTH
# ══════════════════════════════════════════════════════

@tele_bp.route('/consult/register', methods=['GET', 'POST'])
def op_register():
    if request.method == 'POST':
        name   = request.form.get('name','').strip()
        email  = request.form.get('email','').lower().strip()
        phone  = request.form.get('phone','').strip()
        pwd    = request.form.get('password','')
        pwd2   = request.form.get('password2','')

        if not all([name, email, phone, pwd]):
            flash('All required fields must be filled.', 'error')
            return redirect(url_for('tele.op_register'))
        if pwd != pwd2:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('tele.op_register'))
        if OnlinePatient.query.filter_by(email=email).first():
            flash('This email is already registered.', 'error')
            return redirect(url_for('tele.op_register'))

        op = OnlinePatient(
            name          = name,
            email         = email,
            phone         = phone,
            age           = request.form.get('age', type=int),
            gender        = request.form.get('gender',''),
            blood_group   = request.form.get('blood_group',''),
            address       = request.form.get('address','').strip(),
            aadhar_number = request.form.get('aadhar_number','').strip(),
            verify_status = 'approved',   # auto-approved — no admin step needed
            is_verified   = True,
            verified_at   = datetime.utcnow(),
        )
        op.set_password(pwd)
        db.session.add(op)
        db.session.flush()

        # Save live photo
        photo_b64 = request.form.get('photo_data','').strip()
        if photo_b64:
            op.photo_path = save_b64_photo(photo_b64, 'op_photos', op.id)

        # Save aadhar doc
        op.aadhar_doc  = save_file(request.files.get('aadhar_doc'),  'op_aadhar',  op.id)
        op.medical_doc1 = save_file(request.files.get('medical_doc1'), 'op_reports', op.id)
        op.medical_doc2 = save_file(request.files.get('medical_doc2'), 'op_reports', op.id)

        db.session.commit()
        flash('Account created successfully! You can now sign in and book consultations.', 'success')
        return redirect(url_for('tele.op_login'))

    return render_template('tele/op_register.html')


@tele_bp.route('/consult/login', methods=['GET', 'POST'])
def op_login():
    if current_online_patient():
        return redirect(url_for('tele.find_doctors'))
    if request.method == 'POST':
        email = request.form.get('email','').lower().strip()
        pwd   = request.form.get('password','')
        op    = OnlinePatient.query.filter_by(email=email, is_active=True).first()
        if op and op.check_password(pwd):
            session['op_id'] = op.id
            op.last_login = datetime.utcnow()
            db.session.commit()
            flash(f'Welcome back, {op.name}! 👋', 'success')
            next_url = request.args.get('next') or request.form.get('next')
            return redirect(next_url or url_for('tele.find_doctors'))
        flash('Invalid email or password.', 'error')
    return render_template('tele/op_login.html')


@tele_bp.route('/consult/logout')
def op_logout():
    session.pop('op_id', None)
    flash('Signed out.', 'info')
    return redirect(url_for('tele.find_doctors'))


# ══════════════════════════════════════════════════════
#  FIND DOCTORS (public)
# ══════════════════════════════════════════════════════

@tele_bp.route('/consult')
@tele_bp.route('/consult/doctors')
def find_doctors():
    q     = request.args.get('q','').strip()
    spec  = request.args.get('spec','').strip()
    today = date.today()

    doctors = User.query.filter_by(role='doctor', is_verified=True, is_active=True)
    if q:
        doctors = doctors.filter(User.name.ilike(f'%{q}%'))
    if spec:
        doctors = doctors.filter(User.speciality.ilike(f'%{spec}%'))
    doctors = doctors.all()

    # Attach availability info
    for doc in doctors:
        from datetime import datetime as dt
        now_time = dt.now().strftime('%I:%M %p')
        all_today = DoctorSlot.query.filter_by(
            doctor_id=doc.id, slot_date=today, is_available=True, is_booked=False
        ).all()
        doc.today_slots = len(all_today)
        # Also count next 7 days slots
        from datetime import timedelta
        week_slots = DoctorSlot.query.filter(
            DoctorSlot.doctor_id == doc.id,
            DoctorSlot.slot_date >= today,
            DoctorSlot.is_available == True,
            DoctorSlot.is_booked == False
        ).count()
        doc.week_slots = week_slots
        doc.is_online = week_slots > 0

    specialities = db.session.query(User.speciality).filter(
        User.role=='doctor', User.is_verified==True,
        User.speciality != None, User.speciality != ''
    ).distinct().all()
    specialities = [s[0] for s in specialities]

    op = current_online_patient()
    return render_template('tele/find_doctors.html',
                           doctors=doctors, specialities=specialities,
                           q=q, spec=spec, op=op)


# ══════════════════════════════════════════════════════
#  DOCTOR PROFILE + SLOTS (public view)
# ══════════════════════════════════════════════════════

@tele_bp.route('/consult/doctor/<doctor_id>')
def doctor_profile(doctor_id):
    doctor = User.query.filter_by(id=doctor_id, role='doctor', is_verified=True).first_or_404()
    today  = date.today()
    # Show slots for next 14 days
    slots_by_day = {}
    for i in range(14):
        d = today + timedelta(days=i)
        slots = DoctorSlot.query.filter_by(
            doctor_id=doctor_id, slot_date=d, is_available=True, is_booked=False
        ).order_by(DoctorSlot.slot_time).all()
        if slots:
            slots_by_day[d.strftime('%A, %d %b')] = slots

    op = current_online_patient()
    return render_template('tele/doctor_profile.html',
                           doctor=doctor, slots_by_day=slots_by_day, op=op)


# ══════════════════════════════════════════════════════
#  BOOK APPOINTMENT
# ══════════════════════════════════════════════════════

@tele_bp.route('/consult/book/<int:slot_id>', methods=['GET', 'POST'])
@op_required
def book_slot(slot_id):
    slot   = DoctorSlot.query.get_or_404(slot_id)
    doctor = slot.doctor
    op     = current_online_patient()

    if slot.is_booked or not slot.is_available:
        flash('This slot is no longer available.', 'error')
        return redirect(url_for('tele.doctor_profile', doctor_id=doctor.id))

    if request.method == 'POST':
        step = request.form.get('step','1')

        if step == '1':
            # Save booking details to session
            session['booking'] = {
                'slot_id':  slot_id,
                'symptoms': request.form.get('symptoms','').strip(),
            }
            # Save report doc if uploaded
            rep_doc = save_file(request.files.get('report_doc'), 'op_reports', op.id)
            session['booking']['report_doc'] = rep_doc
            return render_template('tele/book_payment.html',
                                   slot=slot, doctor=doctor, op=op,
                                   fee=doctor.consultation_fee if hasattr(doctor,'consultation_fee') else 200)

        elif step == '2':
            # Payment screenshot uploaded
            booking = session.get('booking',{})
            screenshot = save_file(request.files.get('payment_screenshot'), 'op_payments', op.id)
            if not screenshot:
                flash('Please upload payment screenshot.', 'error')
                return render_template('tele/book_payment.html',
                                       slot=slot, doctor=doctor, op=op, fee=200)

            # Create appointment
            appt = Appointment(
                slot_id         = slot_id,
                patient_id      = op.id,
                doctor_id       = doctor.id,
                symptoms        = booking.get('symptoms',''),
                report_doc      = booking.get('report_doc'),
                payment_screenshot = screenshot,
                payment_status  = 'submitted',
                status          = 'payment_submitted',
                fee             = 200,
            )
            appt.get_room_id()
            slot.is_booked = True
            db.session.add(appt)
            db.session.commit()
            session.pop('booking', None)
            flash('Appointment booked! Awaiting payment verification by the doctor.', 'success')
            return redirect(url_for('tele.my_appointments'))

    return render_template('tele/book_slot.html', slot=slot, doctor=doctor, op=op)


# ══════════════════════════════════════════════════════
#  PATIENT: MY APPOINTMENTS + MESSAGES
# ══════════════════════════════════════════════════════

@tele_bp.route('/consult/my-appointments')
@op_required
def my_appointments():
    op    = current_online_patient()
    appts = Appointment.query.filter_by(patient_id=op.id)\
                             .order_by(Appointment.created_at.desc()).all()
    return render_template('tele/my_appointments.html', appts=appts, op=op)


@tele_bp.route('/consult/messages')
@op_required
def patient_messages():
    op   = current_online_patient()
    msgs = ConsultMessage.query.filter_by(patient_id=op.id)\
                               .order_by(ConsultMessage.sent_at.desc()).all()
    # Mark all as read
    for m in msgs:
        if not m.is_read:
            m.is_read = True
    db.session.commit()
    return render_template('tele/patient_messages.html', msgs=msgs, op=op)


@tele_bp.route('/consult/video/<int:appt_id>')
@op_required
def patient_video(appt_id):
    op   = current_online_patient()
    appt = Appointment.query.filter_by(id=appt_id, patient_id=op.id).first_or_404()
    if appt.status not in ['confirmed', 'in_call']:
        flash('Video call is not available yet. Waiting for doctor confirmation.', 'error')
        return redirect(url_for('tele.my_appointments'))
    room = appt.get_room_id()
    db.session.commit()
    return render_template('tele/video_call.html', appt=appt, room=room, role='patient', op=op)


# ══════════════════════════════════════════════════════
#  DOCTOR: SLOT MANAGEMENT
# ══════════════════════════════════════════════════════

@tele_bp.route('/consult/doctor/slots', methods=['GET','POST'])
def doctor_slots():
    from flask_login import current_user, login_required
    if not (hasattr(current_user, 'is_authenticated') and current_user.is_authenticated
            and current_user.is_doctor()):
        flash('Doctor access required.', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        action = request.form.get('action','add')

        if action == 'add':
            slot_date_str = request.form.get('slot_date','')
            start_time    = request.form.get('start_time','09:00')
            end_time      = request.form.get('end_time','17:00')
            duration      = int(request.form.get('duration', 20))

            try:
                slot_date = datetime.strptime(slot_date_str, '%Y-%m-%d').date()
                if slot_date < date.today():
                    flash('Cannot add slots for past dates.', 'error')
                    return redirect(url_for('tele.doctor_slots'))

                # Generate time slots between start and end
                start_dt = datetime.strptime(f'{slot_date_str} {start_time}', '%Y-%m-%d %H:%M')
                end_dt   = datetime.strptime(f'{slot_date_str} {end_time}',   '%Y-%m-%d %H:%M')
                current  = start_dt
                added    = 0
                while current < end_dt:
                    time_str = current.strftime('%I:%M %p')
                    existing = DoctorSlot.query.filter_by(
                        doctor_id=current_user.id,
                        slot_date=slot_date,
                        slot_time=time_str
                    ).first()
                    if not existing:
                        s = DoctorSlot(
                            doctor_id=current_user.id,
                            slot_date=slot_date,
                            slot_time=time_str,
                            duration_mins=duration,
                        )
                        db.session.add(s)
                        added += 1
                    current += timedelta(minutes=duration)
                db.session.commit()
                flash(f'Added {added} slots for {slot_date.strftime("%d %b %Y")}.', 'success')
            except ValueError:
                flash('Invalid date or time format.', 'error')

        elif action == 'toggle_available':
            slot_id = request.form.get('slot_id', type=int)
            slot    = DoctorSlot.query.filter_by(id=slot_id, doctor_id=current_user.id).first()
            if slot and not slot.is_booked:
                slot.is_available = not slot.is_available
                db.session.commit()

        elif action == 'delete':
            slot_id = request.form.get('slot_id', type=int)
            slot    = DoctorSlot.query.filter_by(id=slot_id, doctor_id=current_user.id).first()
            if slot and not slot.is_booked:
                db.session.delete(slot)
                db.session.commit()

        return redirect(url_for('tele.doctor_slots'))

    # GET: show slots for next 7 days
    today   = date.today()
    slots   = DoctorSlot.query.filter(
        DoctorSlot.doctor_id == current_user.id,
        DoctorSlot.slot_date >= today
    ).order_by(DoctorSlot.slot_date, DoctorSlot.slot_time).all()

    return render_template('tele/doctor_slots.html', slots=slots, today=today)


# ══════════════════════════════════════════════════════
#  DOCTOR: APPOINTMENTS MANAGEMENT
# ══════════════════════════════════════════════════════

@tele_bp.route('/consult/doctor/appointments')
def doctor_appointments():
    from flask_login import current_user
    if not (current_user.is_authenticated and current_user.is_doctor()):
        return redirect(url_for('auth.login'))

    status = request.args.get('status', 'all')
    q = Appointment.query.filter_by(doctor_id=current_user.id)
    if status != 'all':
        q = q.filter_by(status=status)
    appts = q.order_by(Appointment.created_at.desc()).all()
    return render_template('tele/doctor_appointments.html', appts=appts, status=status)


@tele_bp.route('/consult/doctor/appointment/<int:appt_id>/verify-payment', methods=['POST'])
def verify_payment(appt_id):
    from flask_login import current_user
    if not (current_user.is_authenticated and current_user.is_doctor()):
        return redirect(url_for('auth.login'))

    appt   = Appointment.query.filter_by(id=appt_id, doctor_id=current_user.id).first_or_404()
    action = request.form.get('action','approve')

    if action == 'approve':
        appt.payment_status = 'verified'
        appt.status         = 'confirmed'
        appt.payment_note   = request.form.get('note','').strip()
        flash('Payment verified. Appointment confirmed!', 'success')
    else:
        appt.payment_status = 'failed'
        appt.status         = 'cancelled'
        appt.payment_note   = request.form.get('note','Payment verification failed.').strip()
        # Unbook the slot
        slot = appt.slot
        if slot:
            slot.is_booked = False
        flash('Payment rejected. Appointment cancelled.', 'error')

    db.session.commit()
    return redirect(url_for('tele.doctor_appointments'))


@tele_bp.route('/consult/doctor/appointment/<int:appt_id>/send-message', methods=['POST'])
def send_message(appt_id):
    from flask_login import current_user
    if not (current_user.is_authenticated and current_user.is_doctor()):
        return redirect(url_for('auth.login'))

    appt = Appointment.query.filter_by(id=appt_id, doctor_id=current_user.id).first_or_404()
    msg  = request.form.get('message','').strip()
    if msg:
        cm = ConsultMessage(
            appointment_id = appt.id,
            doctor_id      = current_user.id,
            patient_id     = appt.patient_id,
            message        = msg,
            prescription   = request.form.get('prescription','').strip(),
        )
        appt.status = 'completed'
        db.session.add(cm)
        db.session.commit()
        flash('Message sent to patient.', 'success')

    return redirect(url_for('tele.doctor_appointments'))


@tele_bp.route('/consult/doctor/video/<int:appt_id>')
def doctor_video(appt_id):
    from flask_login import current_user
    if not (current_user.is_authenticated and current_user.is_doctor()):
        return redirect(url_for('auth.login'))

    appt = Appointment.query.filter_by(id=appt_id, doctor_id=current_user.id).first_or_404()
    if appt.status not in ['confirmed', 'in_call']:
        flash('Appointment not confirmed yet.', 'error')
        return redirect(url_for('tele.doctor_appointments'))

    appt.status         = 'in_call'
    appt.call_started_at = datetime.utcnow()
    room = appt.get_room_id()
    db.session.commit()
    return render_template('tele/video_call.html', appt=appt, room=room,
                           role='doctor', op=None)


# ══════════════════════════════════════════════════════
#  ADMIN: ONLINE PATIENT VERIFICATION
# ══════════════════════════════════════════════════════

@tele_bp.route('/admin/online-patients')
def admin_online_patients():
    from flask_login import current_user
    if not (current_user.is_authenticated and current_user.is_admin()):
        return redirect(url_for('auth.login'))

    status = request.args.get('status', 'pending')
    q = OnlinePatient.query
    if status != 'all':
        q = q.filter_by(verify_status=status)
    patients = q.order_by(OnlinePatient.created_at.desc()).all()
    return render_template('tele/admin_online_patients.html',
                           patients=patients, status=status)


@tele_bp.route('/admin/online-patient/<patient_id>/approve', methods=['POST'])
def admin_approve_op(patient_id):
    from flask_login import current_user
    if not (current_user.is_authenticated and current_user.is_admin()):
        return redirect(url_for('auth.login'))

    op = OnlinePatient.query.get_or_404(patient_id)
    op.is_verified   = True
    op.verify_status = 'approved'
    op.verified_at   = datetime.utcnow()
    db.session.commit()
    flash(f'{op.name} approved.', 'success')
    return redirect(url_for('tele.admin_online_patients'))


@tele_bp.route('/admin/online-patient/<patient_id>/reject', methods=['POST'])
def admin_reject_op(patient_id):
    from flask_login import current_user
    if not (current_user.is_authenticated and current_user.is_admin()):
        return redirect(url_for('auth.login'))

    op = OnlinePatient.query.get_or_404(patient_id)
    op.verify_status = 'rejected'
    op.verify_note   = request.form.get('note','')
    db.session.commit()
    flash(f'{op.name} rejected.', 'success')
    return redirect(url_for('tele.admin_online_patients'))


# ══════════════════════════════════════════════════════
#  DOCTOR QR / BANK DETAILS  (doctor sets payment info)
# ══════════════════════════════════════════════════════

@tele_bp.route('/consult/doctor/payment-setup', methods=['GET','POST'])
def doctor_payment_setup():
    from flask_login import current_user
    if not (current_user.is_authenticated and current_user.is_doctor()):
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        # Save QR image
        qr_file = request.files.get('payment_qr')
        if qr_file and qr_file.filename:
            path = save_file(qr_file, 'doctor_qr', current_user.id)
            current_user.payment_qr  = path
        current_user.payment_upi  = request.form.get('upi_id','').strip()
        current_user.consult_fee  = request.form.get('fee', 200, type=int)
        db.session.commit()
        flash('Payment details saved!', 'success')
        return redirect(url_for('tele.doctor_slots'))

    return render_template('tele/doctor_payment_setup.html')