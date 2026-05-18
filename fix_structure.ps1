# AarogyaLink - One-click structure fixer
# Run this from your AarogyaLink root folder: .\fix_structure.ps1

Write-Host "Fixing AarogyaLink folder structure..." -ForegroundColor Green

# Create correct subfolders
New-Item -ItemType Directory -Force -Path "frontend\templates\auth"
New-Item -ItemType Directory -Force -Path "frontend\templates\patient"
New-Item -ItemType Directory -Force -Path "frontend\templates\dashboard"
New-Item -ItemType Directory -Force -Path "frontend\static\qrcodes"
New-Item -ItemType Directory -Force -Path "frontend\static\cards"
New-Item -ItemType Directory -Force -Path "database"

# Move files to correct locations (only if they exist in wrong place)
$moves = @(
    @("frontend\templates\login.html",    "frontend\templates\auth\login.html"),
    @("frontend\templates\register.html", "frontend\templates\auth\register.html"),
    @("frontend\templates\profile.html",  "frontend\templates\patient\profile.html"),
    @("frontend\templates\search.html",   "frontend\templates\patient\search.html"),
    @("frontend\templates\asha.html",     "frontend\templates\dashboard\asha.html"),
    @("frontend\templates\doctor.html",   "frontend\templates\dashboard\doctor.html")
)

foreach ($move in $moves) {
    $src = $move[0]; $dst = $move[1]
    if (Test-Path $src) {
        Move-Item -Path $src -Destination $dst -Force
        Write-Host "  Moved: $src -> $dst" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "Structure fixed! Now install packages:" -ForegroundColor Green
Write-Host "  cd backend" -ForegroundColor Yellow
Write-Host "  pip install flask flask-sqlalchemy flask-login flask-socketio python-dotenv qrcode reportlab eventlet" -ForegroundColor Yellow
Write-Host "  python app.py" -ForegroundColor Yellow