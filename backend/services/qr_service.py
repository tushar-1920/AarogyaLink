import os
import qrcode
from PIL import Image, ImageDraw, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors


def generate_qr(patient_id, base_url, output_dir):
    """Generate a QR code PNG for a patient and return its path."""
    os.makedirs(output_dir, exist_ok=True)
    url = f"{base_url}/patient/{patient_id}"
    qr = qrcode.QRCode(
        version=1, box_size=10, border=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a6b4a", back_color="white")
    path = os.path.join(output_dir, f"{patient_id}_qr.png")
    img.save(path)
    return path


def make_circle_photo(photo_path, size=120):
    """Crop patient photo into a circle and return PIL Image."""
    try:
        img = Image.open(photo_path).convert("RGBA")
        img = ImageOps.fit(img, (size, size), method=Image.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        output.paste(img, mask=mask)
        # Save temp circle photo
        tmp = photo_path.replace('.jpg', '_circle.png').replace('.jpeg', '_circle.png').replace('.png', '_circle.png')
        output.save(tmp, "PNG")
        return tmp
    except Exception as e:
        print(f"Photo processing error: {e}")
        return None


def generate_card_pdf(patient, qr_path, output_dir, photo_path=None):
    """Generate a printable credit-card sized health card PDF with optional photo."""
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{patient.id}_card.pdf")

    # Credit card size: 85.6mm x 53.98mm
    W = 8.56 * cm
    H = 5.40 * cm

    c = canvas.Canvas(pdf_path, pagesize=(W, H))

    # ── Background
    c.setFillColor(colors.HexColor('#f2faf6'))
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # ── Green header bar
    c.setFillColor(colors.HexColor('#1a6b4a'))
    c.rect(0, H - 1.3 * cm, W, 1.3 * cm, fill=1, stroke=0)

    # ── Header text
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(0.35 * cm, H - 0.75 * cm, "AarogyaLink")
    c.setFont("Helvetica", 5.5)
    c.drawString(0.35 * cm, H - 1.1 * cm, "aarogyalink.in  |  Rural Health Record")

    # ── Patient photo (top-right of header, circular)
    PHOTO_SIZE = 1.1 * cm
    has_photo  = False
    if photo_path and os.path.exists(photo_path):
        circle_path = make_circle_photo(photo_path, size=110)
        if circle_path and os.path.exists(circle_path):
            try:
                # White circle border behind photo
                c.setFillColor(colors.white)
                c.circle(W - 0.85 * cm, H - 0.65 * cm, PHOTO_SIZE / 2 + 0.06 * cm, fill=1, stroke=0)
                c.drawImage(
                    circle_path,
                    W - PHOTO_SIZE - 0.3 * cm,
                    H - PHOTO_SIZE - 0.1 * cm,
                    PHOTO_SIZE, PHOTO_SIZE,
                    preserveAspectRatio=True,
                    mask='auto',
                )
                has_photo = True
            except Exception as e:
                print(f"Photo draw error: {e}")

    # ── Patient ID badge
    c.setFillColor(colors.HexColor('#e6f4ee'))
    c.roundRect(0.25 * cm, H - 2.05 * cm, 3.0 * cm, 0.58 * cm, 0.1 * cm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#1a6b4a'))
    c.setFont("Helvetica-Bold", 7)
    c.drawString(0.45 * cm, H - 1.72 * cm, f"ID: {patient.id}")

    # ── Patient name
    c.setFillColor(colors.HexColor('#0c1a12'))
    c.setFont("Helvetica-Bold", 9.5)
    name_display = patient.name[:20] if len(patient.name) > 20 else patient.name
    c.drawString(0.25 * cm, H - 2.65 * cm, name_display)

    # ── Details
    c.setFont("Helvetica", 6.5)
    c.setFillColor(colors.HexColor('#2e4a38'))
    age_gender = f"Age: {patient.age} yrs"
    if patient.gender:
        age_gender += f"  |  {patient.gender}"
    c.drawString(0.25 * cm, H - 3.05 * cm, age_gender)

    c.setFillColor(colors.HexColor('#5a7265'))
    if patient.blood_group:
        c.drawString(0.25 * cm, H - 3.38 * cm, f"Blood: {patient.blood_group}")
    if patient.village:
        c.drawString(0.25 * cm, H - 3.68 * cm, f"Village: {patient.village[:28]}")

    # ── Conditions
    if patient.conditions:
        c.setFont("Helvetica", 6)
        c.setFillColor(colors.HexColor('#b45309'))
        c.drawString(0.25 * cm, H - 3.98 * cm, f"Conditions: {patient.conditions[:36]}")

    # ── Allergy bar
    allergy_text = (patient.allergies or '').strip()
    allergy_display = allergy_text if allergy_text and allergy_text.lower() != 'none' else None
    if allergy_display:
        c.setFillColor(colors.HexColor('#dc2626'))
        c.rect(0.25 * cm, 0.38 * cm, 4.8 * cm, 0.5 * cm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 6)
        c.drawString(0.4 * cm, 0.56 * cm, f"Allergy: {allergy_display[:32]}")

    # ── QR Code
    if qr_path and os.path.exists(qr_path):
        qr_size = 2.4 * cm
        c.drawImage(
            qr_path,
            W - qr_size - 0.2 * cm,
            0.35 * cm,
            qr_size, qr_size,
            preserveAspectRatio=True,
            mask='auto',
        )

    # ── Scan label
    c.setFont("Helvetica", 4.5)
    c.setFillColor(colors.HexColor('#5a7265'))
    c.drawCentredString(W - 1.4 * cm, 0.22 * cm, "Scan for full history")

    c.save()
    return pdf_path