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

# ── Static pages Blueprint ────────────────────────
pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/how-it-works')
def how_it_works():
    return render_template('pages/how_it_works.html')

@pages_bp.route('/features')
def features():
    return render_template('pages/features.html')

@pages_bp.route('/asha-guide')
def asha_guide():
    return render_template('pages/asha_guide.html')

@pages_bp.route('/privacy')
def privacy():
    return render_template('pages/privacy.html')

@pages_bp.route('/contact')
def contact():
    return render_template('pages/contact.html')