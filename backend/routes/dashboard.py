from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import Patient, Visit, db
from datetime import datetime, date, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    if current_user.is_doctor():
        return redirect(url_for('dashboard.doctor'))
    elif current_user.is_asha():
        return redirect(url_for('dashboard.asha'))
    elif current_user.is_admin():
        try:
            return redirect(url_for('admin.dashboard'))
        except Exception:
            pass
    return redirect(url_for('main.index'))


@dashboard_bp.route('/dashboard/asha')
@login_required
def asha():
    today     = date.today()
    week_ago  = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    my_patients = current_user.patients_registered

    # ── Core stats
    total     = my_patients.count()
    new_week  = 0
    new_month = 0
    try:
        new_week  = my_patients.filter(func.date(Patient.created_at) >= week_ago).count()
        new_month = my_patients.filter(func.date(Patient.created_at) >= month_ago).count()
    except Exception:
        pass

    # ── District breakdown
    districts = []
    try:
        districts = db.session.query(
            Patient.district, func.count(Patient.id).label('cnt')
        ).filter(
            Patient.registered_by == current_user.id
        ).group_by(Patient.district).order_by(func.count(Patient.id).desc()).all()
    except Exception:
        pass

    # ── Follow-ups
    overdue_followups  = []
    upcoming_followups = []
    try:
        all_ids = [p.id for p in my_patients.all()]
        if all_ids:
            overdue_followups = Visit.query.filter(
                Visit.patient_id.in_(all_ids),
                Visit.follow_up != None,
                Visit.follow_up < today
            ).order_by(Visit.follow_up.asc()).limit(10).all()

            upcoming_followups = Visit.query.filter(
                Visit.patient_id.in_(all_ids),
                Visit.follow_up != None,
                Visit.follow_up >= today,
                Visit.follow_up <= today + timedelta(days=7)
            ).order_by(Visit.follow_up.asc()).limit(10).all()
    except Exception:
        pass

    # ── Blood groups
    blood_groups = []
    try:
        blood_groups = db.session.query(
            Patient.blood_group, func.count(Patient.id).label('cnt')
        ).filter(
            Patient.registered_by == current_user.id,
            Patient.blood_group != None,
            Patient.blood_group != ''
        ).group_by(Patient.blood_group).all()
    except Exception:
        pass

    # ── Registration trend last 7 days
    reg_trend = []
    for i in range(6, -1, -1):
        d   = today - timedelta(days=i)
        cnt = 0
        try:
            cnt = my_patients.filter(func.date(Patient.created_at) == d).count()
        except Exception:
            pass
        reg_trend.append({'date': d.strftime('%d %b'), 'count': cnt})

    # ── Recent patients
    recent_patients = my_patients.order_by(Patient.created_at.desc()).limit(10).all()

    return render_template('dashboard/asha.html',
        patients           = recent_patients,
        total              = total,
        new_week           = new_week,
        new_month          = new_month,
        districts          = districts,
        overdue_followups  = overdue_followups,
        upcoming_followups = upcoming_followups,
        blood_groups       = blood_groups,
        reg_trend          = reg_trend,
        today              = today,
    )


@dashboard_bp.route('/dashboard/doctor')
@login_required
def doctor():
    today    = date.today()
    week_ago = today - timedelta(days=7)

    my_visits    = current_user.visits_recorded
    total_visits = my_visits.count()

    today_visits = 0
    week_visits  = 0
    unique_patients = 0
    try:
        today_visits    = my_visits.filter(func.date(Visit.visited_at) == today).count()
        week_visits     = my_visits.filter(func.date(Visit.visited_at) >= week_ago).count()
        unique_patients = db.session.query(
            func.count(func.distinct(Visit.patient_id))
        ).filter(Visit.doctor_id == current_user.id).scalar() or 0
    except Exception:
        pass

    recent_visits = my_visits.order_by(Visit.visited_at.desc()).limit(15).all()

    visit_types = []
    try:
        visit_types = db.session.query(
            Visit.visit_type, func.count(Visit.id).label('cnt')
        ).filter(Visit.doctor_id == current_user.id).group_by(Visit.visit_type).all()
    except Exception:
        pass

    visit_trend = []
    for i in range(6, -1, -1):
        d   = today - timedelta(days=i)
        cnt = 0
        try:
            cnt = my_visits.filter(func.date(Visit.visited_at) == d).count()
        except Exception:
            pass
        visit_trend.append({'date': d.strftime('%d %b'), 'count': cnt})

    return render_template('dashboard/doctor.html',
        visits          = recent_visits,
        total_visits    = total_visits,
        today_visits    = today_visits,
        week_visits     = week_visits,
        unique_patients = unique_patients,
        visit_types     = visit_types,
        visit_trend     = visit_trend,
        today           = today,
    )