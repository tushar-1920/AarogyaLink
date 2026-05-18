from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import User, db
from datetime import datetime
import os, hashlib

auth_bp = Blueprint("auth", __name__)


def save_doc(file_obj, subfolder, user_id, suffix):
    """Save uploaded document and return path relative to static/."""
    if not file_obj or file_obj.filename == "":
        return None
    ext = os.path.splitext(file_obj.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".pdf"]:
        return None
    upload_dir = os.path.join(current_app.static_folder, "uploads", subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    filename  = f"{user_id}_{suffix}{ext}"
    full_path = os.path.join(upload_dir, filename)
    file_obj.save(full_path)
    return f"uploads/{subfolder}/{filename}"


@auth_bp.route("/auth/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    if request.method == "POST":
        email    = request.form.get("email", "").lower().strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"
        user     = User.query.filter_by(email=email, is_active=True).first()

        if user and user.check_password(password):
            # Block unverified non-admin users
            if not user.can_access():
                flash("Your account is pending admin verification. Please wait for approval.", "error")
                return redirect(url_for("auth.login"))
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash(f"Welcome back, {user.name}! 👋", "success")
            next_page = request.args.get("next")
            if user.is_admin():
                return redirect(next_page or url_for("admin.dashboard"))
            return redirect(next_page or url_for("main.index"))

        flash("Invalid email or password. Please try again.", "error")
    return render_template("auth/login.html")


@auth_bp.route("/auth/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        role  = request.form.get("role", "asha")
        email = request.form.get("email", "").lower().strip()
        name  = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        pwd   = request.form.get("password", "")
        pwd2  = request.form.get("password2", "")

        # Validation
        if not name or not email or not phone or not pwd:
            flash("All required fields must be filled.", "error")
            return redirect(url_for("auth.register"))
        if pwd != pwd2:
            flash("Passwords do not match.", "error")
            return redirect(url_for("auth.register"))
        if len(pwd) < 6:
            flash("Password must be at least 6 characters.", "error")
            return redirect(url_for("auth.register"))
        if User.query.filter_by(email=email).first():
            flash("This email is already registered.", "error")
            return redirect(url_for("auth.register"))

        user = User(
            name         = name,
            email        = email,
            phone        = phone,
            role         = role,
            district     = request.form.get("district", "").strip(),
            state        = request.form.get("state", "Punjab").strip(),
            is_verified  = False,
            verify_status= "pending",
        )
        user.set_password(pwd)

        # Role-specific fields
        if role == "doctor":
            user.speciality     = request.form.get("speciality", "").strip()
            user.hospital       = request.form.get("hospital", "").strip()
            user.license_number = request.form.get("license_number", "").strip()
            user.aadhar_number  = request.form.get("aadhar_number", "").strip()
        else:
            user.aadhar_number  = request.form.get("aadhar_number_asha", "").strip()

        db.session.add(user)
        db.session.flush()  # get user.id before saving files

        # Save uploaded documents
        if role == "doctor":
            user.aadhar_doc     = save_doc(request.files.get("aadhar_doc_doctor"), "aadhar",       user.id, "aadhar")
            user.degree_doc     = save_doc(request.files.get("degree_doc"),        "degree",       user.id, "degree")
            user.certificate_doc= save_doc(request.files.get("certificate_doc"),   "certificates", user.id, "cert")
        else:
            user.aadhar_doc     = save_doc(request.files.get("aadhar_doc"),        "aadhar",       user.id, "aadhar")

        db.session.commit()

        flash(
            f"Registration submitted! Your account is pending admin verification. "
            f"You will be able to sign in once approved.",
            "success"
        )
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/auth/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out safely.", "info")
    return redirect(url_for("main.index"))