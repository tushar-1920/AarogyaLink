from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, send_file
from flask_login import login_required, current_user
from models import Patient, Visit, MedicalDocument, db
from services.patient_service import get_patient_by_id, search_patients, create_patient
from services.qr_service import generate_qr, generate_card_pdf
import os, base64, uuid
from datetime import datetime

patient_bp = Blueprint("patient", __name__)


# ── Save base64 photo to disk ─────────────────────────
def save_photo(patient_id, b64_data, photos_dir):
    try:
        os.makedirs(photos_dir, exist_ok=True)
        if "," in b64_data:
            b64_data = b64_data.split(",", 1)[1]
        img_bytes  = base64.b64decode(b64_data)
        photo_path = os.path.join(photos_dir, f"{patient_id}_photo.jpg")
        with open(photo_path, "wb") as f:
            f.write(img_bytes)
        return photo_path
    except Exception as e:
        print(f"Photo save error: {e}")
        return None


# ── Save uploaded document file ───────────────────────
def save_document(file_obj, patient_id, docs_dir):
    """Save an uploaded medical document. Returns (path, ext) or (None, None)."""
    if not file_obj or file_obj.filename == "":
        return None, None
    ext = os.path.splitext(file_obj.filename)[1].lower().strip(".")
    if ext not in ["jpg", "jpeg", "png", "pdf"]:
        return None, None
    os.makedirs(docs_dir, exist_ok=True)
    filename  = f"{patient_id}_{uuid.uuid4().hex[:8]}.{ext}"
    full_path = os.path.join(docs_dir, filename)
    file_obj.save(full_path)
    rel_path = f"uploads/documents/{filename}"
    return rel_path, ext


# ══════════════════════════════════════════════════════
#  PATIENT PROFILE
# ══════════════════════════════════════════════════════
@patient_bp.route("/<patient_id>")
def profile(patient_id):
    patient   = get_patient_by_id(patient_id)
    visits    = patient.visits.order_by(Visit.visited_at.desc()).all()
    documents = patient.documents.order_by(MedicalDocument.uploaded_at.desc()).all()
    return render_template("patient/profile.html",
                           patient=patient, visits=visits, documents=documents)


# ══════════════════════════════════════════════════════
#  REGISTER PATIENT
# ══════════════════════════════════════════════════════
@patient_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name    = request.form.get("name", "").strip()
        age     = request.form.get("age",  "").strip()
        village = request.form.get("village", "").strip()

        if not name or not age or not village:
            flash("Name, Age and Village are required.", "error")
            return redirect(url_for("patient.register"))

        data = {
            "name":              name,
            "age":               int(age),
            "gender":            request.form.get("gender"),
            "phone":             request.form.get("phone", "").strip(),
            "village":           village,
            "district":          request.form.get("district", "").strip(),
            "state":             request.form.get("state", "Punjab").strip(),
            "blood_group":       request.form.get("blood_group"),
            "conditions":        request.form.get("conditions", "").strip(),
            "allergies":         request.form.get("allergies", "").strip(),
            "medications":       request.form.get("medications", "").strip(),
            "emergency_contact": request.form.get("emergency_contact", "").strip(),
        }
        if current_user.is_authenticated:
            data["registered_by"] = current_user.id

        patient = create_patient(data)

        # Save live photo
        photo_b64  = request.form.get("photo_data", "").strip()
        photos_dir = os.path.join(current_app.static_folder, "photos")
        photo_path = None
        if photo_b64:
            photo_path = save_photo(patient.id, photo_b64, photos_dir)
            if photo_path and os.path.exists(photo_path):
                patient.photo_path = "photos/" + os.path.basename(photo_path)

        # Save uploaded medical documents (previous reports)
        docs_dir  = os.path.join(current_app.static_folder, "uploads", "documents")
        files     = request.files.getlist("medical_docs")
        titles    = request.form.getlist("doc_titles")
        doc_types = request.form.getlist("doc_types")
        doc_dates = request.form.getlist("doc_dates")

        for i, file_obj in enumerate(files):
            if not file_obj or file_obj.filename == "":
                continue
            rel_path, ext = save_document(file_obj, patient.id, docs_dir)
            if rel_path:
                title = titles[i] if i < len(titles) and titles[i].strip() else file_obj.filename
                dtype = doc_types[i] if i < len(doc_types) else "report"
                ddate = None
                if i < len(doc_dates) and doc_dates[i]:
                    try:
                        ddate = datetime.strptime(doc_dates[i], "%Y-%m-%d").date()
                    except ValueError:
                        pass
                med_doc = MedicalDocument(
                    patient_id  = patient.id,
                    uploaded_by = current_user.id if current_user.is_authenticated else None,
                    doc_type    = dtype,
                    title       = title,
                    file_path   = rel_path,
                    file_type   = ext,
                    doc_date    = ddate,
                )
                db.session.add(med_doc)

        # Generate QR + PDF card
        try:
            base_url  = request.host_url.rstrip("/")
            qr_path   = generate_qr(patient.id, base_url, current_app.config["QR_OUTPUT_DIR"])
            card_path = generate_card_pdf(patient, qr_path, current_app.config["CARD_OUTPUT_DIR"], photo_path=photo_path)
            patient.qr_path   = os.path.relpath(qr_path,   current_app.static_folder).replace(os.sep, "/")
            patient.card_path = os.path.relpath(card_path, current_app.static_folder).replace(os.sep, "/")
        except Exception as e:
            current_app.logger.warning(f"QR/Card generation failed: {e}")

        db.session.commit()
        flash(f"Patient {patient.name} registered! ID: {patient.id}", "success")
        return redirect(url_for("patient.profile", patient_id=patient.id))

    return render_template("patient/register.html")


# ══════════════════════════════════════════════════════
#  UPLOAD PHOTO (from profile page)
# ══════════════════════════════════════════════════════
@patient_bp.route("/<patient_id>/upload-photo", methods=["POST"])
def upload_photo(patient_id):
    patient   = get_patient_by_id(patient_id)
    photo_b64 = request.form.get("photo_data", "").strip()
    if not photo_b64:
        flash("No photo captured.", "error")
        return redirect(url_for("patient.profile", patient_id=patient.id))

    photos_dir = os.path.join(current_app.static_folder, "photos")
    photo_path = save_photo(patient.id, photo_b64, photos_dir)

    if photo_path and os.path.exists(photo_path):
        patient.photo_path = "photos/" + os.path.basename(photo_path)
        try:
            qr_abs    = os.path.join(current_app.static_folder, patient.qr_path) if patient.qr_path else None
            card_path = generate_card_pdf(patient, qr_abs, current_app.config["CARD_OUTPUT_DIR"], photo_path=photo_path)
            patient.card_path = os.path.relpath(card_path, current_app.static_folder).replace(os.sep, "/")
        except Exception as e:
            current_app.logger.warning(f"Card regen failed: {e}")
        db.session.commit()
        flash("Photo saved and health card updated!", "success")
    else:
        flash("Could not save photo. Try again.", "error")

    return redirect(url_for("patient.profile", patient_id=patient.id))


# ══════════════════════════════════════════════════════
#  UPLOAD MEDICAL DOCUMENT (from profile page)
# ══════════════════════════════════════════════════════
@patient_bp.route("/<patient_id>/upload-doc", methods=["POST"])
def upload_doc(patient_id):
    patient  = get_patient_by_id(patient_id)
    file_obj = request.files.get("doc_file")
    title    = request.form.get("doc_title", "").strip()
    dtype    = request.form.get("doc_type",  "report")
    ddate_s  = request.form.get("doc_date",  "").strip()

    if not file_obj or file_obj.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("patient.profile", patient_id=patient.id))

    docs_dir = os.path.join(current_app.static_folder, "uploads", "documents")
    rel_path, ext = save_document(file_obj, patient.id, docs_dir)

    if not rel_path:
        flash("Invalid file. Only JPG, PNG, PDF allowed.", "error")
        return redirect(url_for("patient.profile", patient_id=patient.id))

    ddate = None
    if ddate_s:
        try:
            ddate = datetime.strptime(ddate_s, "%Y-%m-%d").date()
        except ValueError:
            pass

    med_doc = MedicalDocument(
        patient_id  = patient.id,
        uploaded_by = current_user.id if current_user.is_authenticated else None,
        doc_type    = dtype,
        title       = title or file_obj.filename,
        file_path   = rel_path,
        file_type   = ext,
        doc_date    = ddate,
    )
    db.session.add(med_doc)
    db.session.commit()
    flash("Document uploaded successfully!", "success")
    return redirect(url_for("patient.profile", patient_id=patient.id))


# ══════════════════════════════════════════════════════
#  VIEW / DELETE MEDICAL DOCUMENT
# ══════════════════════════════════════════════════════
@patient_bp.route("/doc/<int:doc_id>/view")
def view_doc(doc_id):
    doc      = MedicalDocument.query.get_or_404(doc_id)
    abs_path = os.path.join(current_app.static_folder, doc.file_path)
    if not os.path.exists(abs_path):
        flash("File not found on disk.", "error")
        return redirect(url_for("patient.profile", patient_id=doc.patient_id))
    return send_file(abs_path)


@patient_bp.route("/doc/<int:doc_id>/delete", methods=["POST"])
@login_required
def delete_doc(doc_id):
    doc = MedicalDocument.query.get_or_404(doc_id)
    pid = doc.patient_id
    try:
        abs_path = os.path.join(current_app.static_folder, doc.file_path)
        if os.path.exists(abs_path):
            os.remove(abs_path)
    except Exception:
        pass
    db.session.delete(doc)
    db.session.commit()
    flash("Document deleted.", "success")
    return redirect(url_for("patient.profile", patient_id=pid))


# ══════════════════════════════════════════════════════
#  SEARCH
# ══════════════════════════════════════════════════════
@patient_bp.route("/search")
def search():
    q       = request.args.get("q", "").strip()
    results = search_patients(q) if q else []
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify([{
            "id": p.id, "name": p.name,
            "village": p.village or "", "age": p.age, "blood": p.blood_group or "",
        } for p in results])
    return render_template("patient/search.html", results=results, query=q)


# ══════════════════════════════════════════════════════
#  ADD VISIT
# ══════════════════════════════════════════════════════
@patient_bp.route("/<patient_id>/add-visit", methods=["POST"])
@login_required
def add_visit(patient_id):
    patient = get_patient_by_id(patient_id)
    if not current_user.is_doctor() and not current_user.is_admin():
        flash("Only verified doctors can add visits.", "error")
        return redirect(url_for("patient.profile", patient_id=patient.id))
    diagnosis = request.form.get("diagnosis", "").strip()
    if not diagnosis:
        flash("Diagnosis is required.", "error")
        return redirect(url_for("patient.profile", patient_id=patient.id))
    visit = Visit(
        patient_id   = patient.id,
        doctor_id    = current_user.id,
        hospital     = request.form.get("hospital", "").strip() or current_user.hospital,
        diagnosis    = diagnosis,
        prescription = request.form.get("prescription", "").strip(),
        notes        = request.form.get("notes", "").strip(),
        visit_type   = request.form.get("visit_type", "OPD"),
    )
    db.session.add(visit)
    db.session.commit()
    flash("Visit recorded successfully!", "success")
    return redirect(url_for("patient.profile", patient_id=patient.id))


# ══════════════════════════════════════════════════════
#  SCANNER API
# ══════════════════════════════════════════════════════
@patient_bp.route("/api/<patient_id>")
def api_patient(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"found": False, "error": f"No patient: {patient_id}"}), 404
    return jsonify({
        "found": True, "id": patient.id, "name": patient.name,
        "age": patient.age, "gender": patient.gender or "",
        "blood": patient.blood_group or "", "village": patient.village or "",
        "district": patient.district or "", "conditions": patient.conditions or "",
        "allergies": patient.allergies or "",
        "visits": int(patient.visit_count()), "visit_count": int(patient.visit_count()),
        "has_photo": bool(patient.photo_path),
    })