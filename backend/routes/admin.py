from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from models import User, Patient, Visit, db
from datetime import datetime
from functools import wraps
import os

admin_bp = Blueprint("admin", __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("Admin access required.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/admin")
@login_required
@admin_required
def dashboard():
    stats = {
        "total_patients":  Patient.query.filter_by(is_active=True).count(),
        "total_doctors":   User.query.filter_by(role="doctor", is_active=True).count(),
        "total_asha":      User.query.filter_by(role="asha",   is_active=True).count(),
        "total_visits":    Visit.query.count(),
        "pending_doctors": User.query.filter_by(role="doctor", verify_status="pending").count(),
        "pending_asha":    User.query.filter_by(role="asha",   verify_status="pending").count(),
    }
    pending_users   = User.query.filter_by(verify_status="pending")\
                          .filter(User.role != "admin")\
                          .order_by(User.created_at.desc()).all()
    recent_patients = Patient.query.filter_by(is_active=True)\
                            .order_by(Patient.created_at.desc()).limit(6).all()
    recent_users    = User.query.filter(User.role != "admin")\
                          .order_by(User.created_at.desc()).limit(8).all()
    return render_template("admin/dashboard.html",
                           stats=stats, pending_users=pending_users,
                           recent_patients=recent_patients, recent_users=recent_users)


@admin_bp.route("/admin/users")
@login_required
@admin_required
def users():
    role   = request.args.get("role",   "all")
    status = request.args.get("status", "all")
    q      = request.args.get("q",      "").strip()
    query  = User.query.filter(User.role != "admin")
    if role   != "all": query = query.filter_by(role=role)
    if status != "all": query = query.filter_by(verify_status=status)
    if q:
        query = query.filter(db.or_(
            User.name.ilike(f"%{q}%"),
            User.email.ilike(f"%{q}%"),
            User.district.ilike(f"%{q}%")
        ))
    return render_template("admin/users.html",
                           users=query.order_by(User.created_at.desc()).all(),
                           role=role, status=status, q=q)


@admin_bp.route("/admin/user/<user_id>")
@login_required
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("admin/user_detail.html", user=user)


@admin_bp.route("/admin/user/<user_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_verified   = True
    user.verify_status = "approved"
    user.verify_note   = None
    user.verified_by   = current_user.id
    user.verified_at   = datetime.utcnow()
    db.session.commit()
    flash(f"✅ {user.name} ({user.role.upper()}) approved! They can now sign in.", "success")
    return redirect(url_for("admin.user_detail", user_id=user.id))


@admin_bp.route("/admin/user/<user_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_user(user_id):
    user = User.query.get_or_404(user_id)
    note = request.form.get("note", "").strip()
    user.is_verified   = False
    user.verify_status = "rejected"
    user.verify_note   = note or "Documents incomplete or invalid."
    user.verified_by   = current_user.id
    user.verified_at   = datetime.utcnow()
    db.session.commit()
    flash(f"❌ {user.name} rejected. Reason saved.", "error")
    return redirect(url_for("admin.user_detail", user_id=user.id))


@admin_bp.route("/admin/user/<user_id>/revoke", methods=["POST"])
@login_required
@admin_required
def revoke_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_verified   = False
    user.verify_status = "rejected"
    user.verify_note   = "Access revoked by admin."
    db.session.commit()
    flash(f"Access revoked for {user.name}.", "error")
    return redirect(url_for("admin.user_detail", user_id=user.id))


@admin_bp.route("/admin/user/<user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f"User {user.name} {'activated' if user.is_active else 'deactivated'}.", "success")
    return redirect(url_for("admin.user_detail", user_id=user.id))


@admin_bp.route("/admin/doc/<user_id>/<doc_type>")
@login_required
@admin_required
def view_doc(user_id, doc_type):
    user = User.query.get_or_404(user_id)
    rel_path = {"aadhar": user.aadhar_doc, "degree": user.degree_doc,
                "certificate": user.certificate_doc}.get(doc_type)
    if not rel_path:
        flash("Document not found.", "error")
        return redirect(url_for("admin.user_detail", user_id=user.id))
    abs_path = os.path.join(current_app.static_folder, rel_path)
    if not os.path.exists(abs_path):
        flash("File missing on disk.", "error")
        return redirect(url_for("admin.user_detail", user_id=user.id))
    return send_file(abs_path)


@admin_bp.route("/admin/patients")
@login_required
@admin_required
def patients():
    q = request.args.get("q", "").strip()
    query = Patient.query.filter_by(is_active=True)
    if q:
        query = query.filter(db.or_(
            Patient.name.ilike(f"%{q}%"), Patient.id.ilike(f"%{q}%"),
            Patient.village.ilike(f"%{q}%"), Patient.district.ilike(f"%{q}%")
        ))
    return render_template("admin/patients.html",
                           patients=query.order_by(Patient.created_at.desc()).all(), q=q)


@admin_bp.route("/admin/analytics")
@login_required
@admin_required
def analytics():
    from sqlalchemy import func
    district_counts = db.session.query(
        Patient.district, func.count(Patient.id).label("count")
    ).filter_by(is_active=True).group_by(Patient.district)\
     .order_by(func.count(Patient.id).desc()).limit(10).all()
    visit_by_type = db.session.query(
        Visit.visit_type, func.count(Visit.id).label("count")
    ).group_by(Visit.visit_type).all()
    return render_template("admin/analytics.html",
                           district_counts=district_counts, visit_by_type=visit_by_type)