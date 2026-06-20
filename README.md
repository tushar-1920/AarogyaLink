<div align="center">

<img src="frontend/static/favicon-192.png" alt="AarogyaLink Logo" width="120" height="120" style="border-radius:24px"/>

# AarogyaLink 🌿

### *Every patient's story, always with them.*

**A full-stack rural health records + telemedicine + AI platform for India**  
Built for 900M Indians who have zero structured health records.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![GPT-4o](https://img.shields.io/badge/GPT--4o-Powered-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![Render](https://img.shields.io/badge/Deployed_on-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)
[![DPDPA](https://img.shields.io/badge/DPDPA_2023-Compliant-FF6B35?style=for-the-badge&logo=shield&logoColor=white)](https://dpdpa.in)

<br/>

[🚀 Live Demo](https://aarogyalink-ed6h.onrender.com) · [📋 Features](#-features) · [🤖 AI Tools](#-ai-features) · [⚡ Quick Start](#-quick-start) · [🏗️ Architecture](#-architecture)

<br/>

> *"When a patient arrives unconscious, we have no idea what medicines they're allergic to.*  
> *A QR card that tells us instantly could save lives every single day."*  
> — **Dr. Ravinder Singh**, Medical Officer, PHC Sahnewal, Ludhiana

</div>

---

## 🌟 What is AarogyaLink?

AarogyaLink solves one of India's biggest silent crises — **900 million Indians have no structured health records**. When they visit a new doctor, everything starts from zero. Wrong prescriptions are given because nobody knows about allergies. Expensive tests are repeated because old reports are lost. Lives are lost unnecessarily.

**AarogyaLink gives every rural Indian a lifelong QR health card.**

An ASHA worker registers a patient in 2 minutes using voice in Hindi. The system generates a unique QR code instantly. The patient gets a laminated card printed for ₹3. Any doctor, at any hospital, anywhere in India, scans it and sees the complete medical history — immediately. No app. No login. No internet needed at the patient's end.

```
ASHA registers  →  QR generated in 3s  →  Patient gets card (₹3 print)  →  Doctor scans anywhere  →  History instant
```

---

## ✨ Features

### 🏥 Core Health Records
| Feature | Description |
|---------|-------------|
| 🎤 **Voice Registration** | ASHA workers speak patient details in Hindi — form fills automatically via Web Speech API |
| 📸 **Live Photo Capture** | Camera opens in browser, circular crop saved — no app needed |
| 🔲 **QR Code in 3 Seconds** | Unique patient ID + QR generated instantly on registration |
| 📄 **PDF Health Card** | Printable A4/card-size PDF ready immediately — print for ₹3 at any shop |
| 📁 **Document Upload** | Old lab reports, X-rays, prescriptions — all attached to patient profile |
| 📵 **Offline-First PWA** | Works without internet — syncs when connection returns |
| 🚨 **Emergency QR View** | Unconscious patient scanned — blood group + allergies shown WITHOUT login |
| ⚠️ **Allergy Alert Banner** | Red banner on every visit page — impossible for doctors to miss |

### 🎥 Telemedicine
| Feature | Description |
|---------|-------------|
| 👤 **Online Patient Accounts** | Patients create accounts with live photo + Aadhar verification |
| 📅 **Doctor Slot Management** | Doctors generate time slots — system auto-creates appointments |
| 💳 **UPI Payments** | Doctor's QR shown on payment page — patient pays + uploads screenshot |
| 🎥 **Jitsi Video Calls** | Free, no-app video consultations in any browser |
| 💬 **Digital Prescriptions** | Doctor sends prescription after call — appears in patient messages instantly |
| 🔍 **Doctor Directory** | Browse verified doctors by speciality — filter by availability |

### 🤖 AI Features
| Feature | Description |
|---------|-------------|
| 🧠 **Symptom Checker** | Chat with AI about symptoms — urgency assessment + possible conditions in Hindi/English |
| 💊 **Drug Interaction Checker** | Add medicines → AI flags dangerous interactions + suggests safer alternatives |
| ❤️ **Health Risk Score** | 0–100 score with domain breakdown, action plan, 5-year outlook powered by GPT-4o |
| 🤖 **AarogyaBot** | Voice AI chatbot (Hindi/Punjabi/English) — knows YOUR patients, speaks back |

### 👩‍⚕️ ASHA Worker Tools
| Feature | Description |
|---------|-------------|
| 🎯 **Target Tracker** | Monthly registration targets with progress bars |
| 📓 **Daily Activity Log** | Replaces paper diary — supervisor views from admin panel |
| 🏆 **Leaderboard + Badges** | District rankings, milestone badges, shareable certificates |
| 🗺️ **Village Coverage Map** | Leaflet.js map showing registered vs uncovered areas |

### ⚙️ Admin & Security
| Feature | Description |
|---------|-------------|
| 🛡️ **Document Verification** | Admin reviews Aadhar + degree + council certificate before approving |
| 📜 **Full Audit Trail** | Every access logged with timestamp + IP — tamper-proof |
| 📊 **District Analytics** | Real-time charts — registrations, top conditions, visit trends |
| 🔐 **DPDPA 2023 Compliant** | Explicit consent, right to erasure, data minimisation |

---

## 🤖 AI Features

### 🧠 Symptom Checker
```
Doctor/ASHA describes symptoms → GPT-4o reads patient history → Returns:
├── 🔴 Urgency Level (Emergency / Monitor / Routine)
├── 🩺 Possible Conditions (differential diagnosis)
├── ✅ Recommended Actions (practical rural India steps)
└── ⚠️ Warning Signs to watch for
```
Supports **Hindi + English** with one-click language toggle. Patient history automatically injected into every query.

### 💊 Drug Interaction Checker
```
Add 2+ medicines → AI analyzes → Returns:
├── ⚡ Severity (Mild / Moderate / Severe / DANGEROUS)
├── 📋 Mechanism (why it happens, in simple terms)
├── ✅ Clinical Recommendation
├── 🔄 Safer Alternatives
└── 🚨 Allergy Cross-Checks
```

### ❤️ Health Risk Score
```
Patient profile + lifestyle factors → GPT-4o → Returns:
├── 📊 Overall Score (0-100, animated gauge)
├── 🏥 Domain Scores (Cardiac, Metabolic, Respiratory, Mental, Lifestyle)
├── ⚠️ Top Risk Factors (High/Medium/Low impact)
├── ✅ Action Plan (NOW / This Week / This Month)
├── 🔬 Screening Recommendations
└── 🔮 5-Year Health Outlook
```

### 🤖 AarogyaBot — Voice AI Assistant
The most advanced feature. A floating AI assistant on **every page** that:
- 🎤 **Listens** in Hindi, Punjabi, or English via Web Speech API
- 🔊 **Speaks back** using Speech Synthesis API
- 🧠 **Knows your patients** — pulls real data from the database
- 🔒 **Privacy-first** — public users get zero patient data
- ⚡ **Takes actions** — guides you to the right page, answers clinical questions

```
Doctor says (in Hindi): "आज कितने follow-ups हैं?"
AarogyaBot replies (in Hindi + speaks): "आपके 3 मरीज़ हैं — Ramesh Kumar, Priya Devi, Sukhwinder Singh"
```

---

## 🏗️ Architecture

```
AarogyaLink/
├── 📄 server.py                    # Gunicorn entry point
├── 📄 Procfile                     # Render deployment config
├── 📄 render.yaml                  # Persistent disk + env vars
├── 📄 requirements.txt
│
├── 🐍 backend/
│   ├── app.py                      # Flask factory function
│   ├── config.py                   # DB paths (local + Render persistent disk)
│   ├── extensions.py               # db, login_manager
│   ├── models.py                   # SQLAlchemy models
│   └── routes/
│       ├── main.py                 # Homepage + static pages
│       ├── auth.py                 # Login / Register / Logout
│       ├── patient.py              # Patient CRUD + QR + PDF
│       ├── dashboard.py            # Role dashboards
│       ├── scan.py                 # QR scanner
│       ├── admin.py                # Admin panel
│       ├── telemedicine.py         # Video consultations
│       └── ai_features.py          # GPT-4o AI features + AarogyaBot
│
└── 🎨 frontend/
    ├── templates/
    │   ├── base.html               # Dark navbar + AarogyaBot widget
    │   ├── index.html              # Landing page (Hindi + English)
    │   ├── auth/                   # Login + Register (live camera)
    │   ├── ai/                     # Symptom Checker, Drug Checker, Risk Score
    │   ├── pages/                  # How it works, Features, ASHA Guide, Privacy
    │   ├── dashboard/              # Doctor + ASHA + Admin dashboards
    │   ├── patient/                # Patient profile + registration
    │   └── tele/                   # Telemedicine pages
    └── static/
        ├── uploads/                # Patient + doctor photos, documents
        ├── qrcodes/                # Generated QR codes
        └── favicon.ico             # 🌿 AarogyaLink favicon
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, Flask 3.1, SQLAlchemy, Flask-Login |
| **Database** | SQLite (development) / PostgreSQL (production) |
| **AI / LLM** | OpenAI GPT-4o (Symptom Checker, Drug Checker, Risk Score, AarogyaBot) |
| **Voice** | Web Speech API (STT) + Speech Synthesis API (TTS) |
| **Frontend** | Jinja2, Vanilla CSS, Vanilla JS (no frameworks) |
| **QR Codes** | qrcode[pil] library |
| **PDF Generation** | ReportLab |
| **Video Calls** | Jitsi Meet (embedded) |
| **Deployment** | Render.com (Web Service + Persistent Disk) |
| **Process Manager** | Gunicorn |

---

## 👥 User Roles

```
┌─────────────────────────────────────────────────────────┐
│                    AarogyaLink Users                    │
├──────────────┬──────────────────┬───────────────────────┤
│  ASHA Worker │     Doctor       │        Admin          │
├──────────────┼──────────────────┼───────────────────────┤
│ Register     │ Scan QR cards    │ Verify doctors/ASHA   │
│ patients     │ View full history│ Review documents      │
│ Voice input  │ Add visits       │ Manage all patients   │
│ Print cards  │ AI tools         │ District analytics    │
│ Activity log │ Video slots      │ Full audit trail      │
│ Follow-ups   │ Digital Rx       │ Platform health       │
│ AI chatbot   │ AI chatbot       │                       │
└──────────────┴──────────────────┴───────────────────────┘
                         +
┌─────────────────────────────────────────────────────────┐
│              Online Patient (Telemedicine)              │
├─────────────────────────────────────────────────────────┤
│ Browse doctors │ Book slots │ Pay UPI │ Video call │ Rx │
└─────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Git

### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/tushar-1920/AarogyaLink.git
cd AarogyaLink

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file at root
echo "OPENAI_API_KEY=sk-your-key-here
SECRET_KEY=aarogyalink-secret-2025
FLASK_DEBUG=true
ADMIN_EMAIL=admin@aarogyalink.in
ADMIN_PASSWORD=Admin@2025#Secure" > .env

# 4. Run locally
python backend/app.py

# 5. Open in browser
# http://localhost:5000
```

### Default Admin Login
```
Email:    admin@aarogyalink.in
Password: Admin@2025#Secure
```

> ⚠️ Change admin credentials immediately in production!

---

## 🚀 Deployment (Render)

### Step 1: Render Setup
1. Connect GitHub repo to Render
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn --workers 1 --bind 0.0.0.0:$PORT --timeout 120 server:app`

### Step 2: Environment Variables
```
SECRET_KEY          = <generate random>
FLASK_DEBUG         = false
RENDER              = true
ADMIN_EMAIL         = admin@aarogyalink.in
ADMIN_PASSWORD      = <your secure password>
OPENAI_API_KEY      = sk-your-key-here
```

### Step 3: Persistent Disk (Critical!)
```
Render Dashboard → Disks → Add Disk
Name:       aarogyalink-data
Mount Path: /var/data
Size:       1 GB
```
> Without this, your database resets on every deploy!

---

## 🔒 Privacy & Security

- **DPDPA 2023 Compliant** — India's Digital Personal Data Protection Act
- **Login required** for all patient data access
- **Role-based access** — ASHA sees only their patients, doctors see their patients
- **Zero patient data** for public/unauthenticated users (AarogyaBot included)
- **Audit trail** — every patient record access logged with timestamp + IP
- **No GPS tracking**, no advertising, no data selling — ever

---

## 📊 Impact Numbers

```
900M+        Indians with zero health records
1.05M        ASHA workers who can use AarogyaLink today
₹0           Cost to patients — free forever
₹3           Cost to print a lifetime QR health card
2 minutes    Time to register a patient (vs 20 min on paper)
3 seconds    Time to generate QR code + PDF card
0            Apps needed by the patient
```

---

## 🗺️ Roadmap

- [x] Core patient registration with QR + PDF
- [x] Doctor visit management + allergy alerts
- [x] Telemedicine with Jitsi video + UPI payments
- [x] GPT-4o AI tools (Symptom Checker, Drug Checker, Risk Score)
- [x] AarogyaBot — voice AI assistant (Hindi/Punjabi/English)
- [x] ASHA worker tools (targets, logs, leaderboard)
- [x] Advanced dark navbar + responsive mobile UI
- [x] DPDPA 2023 compliance
- [ ] WhatsApp Bot integration (Twilio)
- [ ] Disease outbreak detection (AI monitoring)
- [ ] Vitals tracker with trend charts
- [ ] Lab report AI scanner (photo → digital)
- [ ] ABHA (Ayushman Bharat Health Account) integration
- [ ] SMS medication reminders
- [ ] Hospital subscription API

---

## 👨‍💻 Developer

<div align="center">

**Tushar**  
B.Tech Computer Science · Chandigarh Engineering College (CGC), Mohali  
Graduating 2027

[![GitHub](https://img.shields.io/badge/GitHub-tushar--1920-181717?style=for-the-badge&logo=github)](https://github.com/tushar-1920)
[![LeetCode](https://img.shields.io/badge/LeetCode-400%2B_Problems-FFA116?style=for-the-badge&logo=leetcode&logoColor=white)](https://leetcode.com)

*Shortlisted twice for Smart India Hackathon*  
*Actively applying for Data Science / ML / SWE internships*

</div>

---

## 📄 License

```
MIT License — © 2026 Tushar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
```

---

<div align="center">

**Built with ❤️ for rural India**

*"One card. One scan. A lifetime of care."*

🌿 **AarogyaLink** — *Because every patient's story deserves to survive.*

<br/>

⭐ **Star this repo if you believe rural India deserves better healthcare** ⭐

</div>