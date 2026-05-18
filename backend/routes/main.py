from flask import Blueprint, render_template
from models import Patient, Visit, User

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    stats = {
        'patients': Patient.query.filter_by(is_active=True).count(),
        'visits':   Visit.query.count(),
        'doctors':  User.query.filter_by(role='doctor', is_active=True).count(),
        'villages': Patient.query.with_entities(Patient.village).distinct().count(),
    }
    return render_template('index.html', stats=stats)

@main_bp.route('/about')
def about():
    return render_template('about.html')