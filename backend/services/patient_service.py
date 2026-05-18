from models import Patient, db


def get_all_patients(page=1, per_page=20):
    return Patient.query\
        .filter_by(is_active=True)\
        .order_by(Patient.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)


def get_patient_by_id(patient_id):
    return Patient.query.get_or_404(patient_id)


def search_patients(query, limit=20):
    q = query.strip()
    return Patient.query.filter(
        db.or_(
            Patient.name.ilike(f'%{q}%'),
            Patient.id.ilike(f'%{q}%'),
            Patient.village.ilike(f'%{q}%'),
            Patient.district.ilike(f'%{q}%'),
            Patient.phone.ilike(f'%{q}%'),
        )
    ).filter_by(is_active=True).limit(limit).all()


def create_patient(data):
    patient = Patient(**data)
    db.session.add(patient)
    db.session.commit()
    return patient


def update_patient(patient_id, data):
    patient = Patient.query.get_or_404(patient_id)
    for key, val in data.items():
        if hasattr(patient, key):
            setattr(patient, key, val)
    db.session.commit()
    return patient


def deactivate_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    patient.is_active = False
    db.session.commit()
    return patient