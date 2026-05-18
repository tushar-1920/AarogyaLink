from flask import Blueprint, render_template
from flask_login import login_required

scan_bp = Blueprint('scan', __name__)

@scan_bp.route('/scan')
def scan():
    return render_template('scan.html')