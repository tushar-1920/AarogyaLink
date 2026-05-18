# AarogyaLink - Safe package installer for Anaconda
# Run from your AarogyaLink root folder: .\install.ps1

Write-Host "Installing AarogyaLink packages (Anaconda-safe)..." -ForegroundColor Green

# Install one by one to avoid version conflicts
$packages = @(
    "flask",
    "flask-sqlalchemy",
    "flask-login",
    "flask-socketio",
    "python-dotenv",
    "qrcode",
    "reportlab",
    "eventlet"
)

foreach ($pkg in $packages) {
    Write-Host "Installing $pkg..." -ForegroundColor Cyan
    pip install $pkg --quiet
}

# Pillow separately - use --upgrade to get compatible version
Write-Host "Installing Pillow..." -ForegroundColor Cyan
pip install Pillow --upgrade --quiet

Write-Host ""
Write-Host "All packages installed!" -ForegroundColor Green
Write-Host "Now run: cd backend && python app.py" -ForegroundColor Yellow