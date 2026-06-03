"""
AarogyaLink AI Features — GPT-4o powered
1. Symptom Checker Chatbot (Hindi + English)
2. Drug Interaction Checker
3. Health Risk Score Calculator
"""
from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from models import Patient, Visit, db
import os, json, re
from datetime import datetime

ai_bp = Blueprint('ai', __name__)

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')


def call_gpt(messages, model="gpt-4o", max_tokens=1200, json_mode=False):
    """Call OpenAI API using urllib (no extra packages needed)."""
    import urllib.request, urllib.error, json as _json

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it in Render Environment settings.")
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    data = _json.dumps(payload).encode('utf-8')
    req  = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = _json.loads(resp.read())
            return result['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        raise RuntimeError(f"OpenAI HTTP {e.code}: {body[:200]}")
    except Exception as e:
        raise RuntimeError(f"OpenAI API error: {type(e).__name__}: {e}")


# ═══════════════════════════════════════════════════════════════
#  1. SYMPTOM CHECKER CHATBOT
# ═══════════════════════════════════════════════════════════════

@ai_bp.route('/ai/symptom-checker')
@login_required
def symptom_checker():
    patients = Patient.query.filter_by(is_active=True).order_by(Patient.name).all()
    return render_template('ai/symptom_checker.html', patients=patients)


@ai_bp.route('/ai/symptom-checker/chat', methods=['POST'])
@login_required
def symptom_chat():
    data        = request.get_json()
    user_msg    = data.get('message', '').strip()
    history     = data.get('history', [])
    patient_id  = data.get('patient_id', '')
    language    = data.get('language', 'en')

    if not user_msg:
        return jsonify({'error': 'Empty message'}), 400

    # Build patient context
    patient_ctx = ""
    if patient_id:
        p = Patient.query.get(patient_id)
        if p:
            visits = p.visits.order_by(Visit.visited_at.desc()).limit(5).all()
            visit_summary = "; ".join([
                f"{v.visited_at.strftime('%b %Y')}: {v.diagnosis}" for v in visits
            ]) or "No visits"
            patient_ctx = f"""
PATIENT CONTEXT:
- Name: {p.name}, Age: {p.age}, Gender: {p.gender}
- Blood Group: {p.blood_group}
- Known conditions: {p.conditions or 'None'}
- Allergies: {p.allergies or 'None'}
- Current medications: {p.medications or 'None'}
- Recent visits: {visit_summary}
"""

    lang_instruction = (
        "Respond ONLY in Hindi (Devanagari script). Keep medical terms in English."
        if language == 'hi' else
        "Respond in clear, simple English suitable for rural healthcare workers."
    )

    system_prompt = f"""You are AarogyaAI, an advanced medical AI assistant for AarogyaLink — a rural health platform in India.

{patient_ctx}

YOUR ROLE:
- Analyze symptoms described by ASHA workers, doctors, or patients
- Suggest possible conditions (differential diagnosis) with likelihood levels
- Provide urgency assessment: 🟢 Routine | 🟡 Monitor | 🔴 Emergency
- Give practical next steps appropriate for rural India
- Consider limited hospital access, tropical diseases, and local health patterns
- NEVER replace professional medical advice — always recommend doctor consultation

RESPONSE FORMAT (always structured):
1. **Urgency Level** with colored indicator
2. **Possible Conditions** (list with brief explanation)
3. **Recommended Actions** (practical steps)
4. **Warning Signs** to watch for
5. **When to go to hospital IMMEDIATELY**

{lang_instruction}

Keep responses concise but complete. Use bullet points. Be empathetic."""

    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history (last 10 messages)
    for h in history[-10:]:
        messages.append({"role": h['role'], "content": h['content']})
    
    messages.append({"role": "user", "content": user_msg})

    try:
        reply = call_gpt(messages, max_tokens=800)
        return jsonify({'reply': reply, 'timestamp': datetime.utcnow().isoformat()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════
#  2. DRUG INTERACTION CHECKER
# ═══════════════════════════════════════════════════════════════

@ai_bp.route('/ai/drug-checker')
@login_required
def drug_checker():
    patients = Patient.query.filter_by(is_active=True).order_by(Patient.name).all()
    return render_template('ai/drug_checker.html', patients=patients)


@ai_bp.route('/ai/drug-checker/check', methods=['POST'])
@login_required
def check_drugs():
    data        = request.get_json()
    drugs       = data.get('drugs', [])        # list of drug names to check
    patient_id  = data.get('patient_id', '')
    new_drug    = data.get('new_drug', '')     # specific new drug being added

    if len(drugs) < 2 and not new_drug:
        return jsonify({'error': 'Need at least 2 drugs to check interactions'}), 400

    # Get patient context
    patient_ctx = ""
    allergy_ctx = ""
    if patient_id:
        p = Patient.query.get(patient_id)
        if p:
            patient_ctx = f"Patient: {p.name}, Age: {p.age}, Conditions: {p.conditions or 'None'}"
            allergy_ctx = f"Known allergies: {p.allergies or 'None'}"

    drugs_list = "\n".join([f"- {d}" for d in drugs])
    
    prompt = f"""You are a clinical pharmacology AI for AarogyaLink rural health platform.

{patient_ctx}
{allergy_ctx}

DRUGS TO CHECK:
{drugs_list}
{"NEW DRUG BEING ADDED: " + new_drug if new_drug else ""}

Analyze ALL drug-drug interactions, drug-disease interactions, and check against known allergies.

Respond ONLY in valid JSON with this exact structure:
{{
  "overall_risk": "SAFE" | "CAUTION" | "DANGEROUS",
  "overall_message": "one sentence summary",
  "interactions": [
    {{
      "drugs": ["drug1", "drug2"],
      "severity": "mild" | "moderate" | "severe",
      "effect": "what happens",
      "recommendation": "what to do",
      "mechanism": "why it happens (simple terms)"
    }}
  ],
  "allergy_alerts": [
    {{
      "drug": "drug name",
      "allergen": "what it contains",
      "risk": "description"
    }}
  ],
  "safe_combinations": ["list of drug pairs that are safe together"],
  "clinical_notes": "overall clinical recommendation for rural doctor",
  "alternatives": [
    {{
      "replace": "drug to replace",
      "with": "safer alternative",
      "reason": "why safer"
    }}
  ]
}}

Be accurate. Use standard pharmacology. Consider rural India context."""

    try:
        raw = call_gpt(
            [{"role": "user", "content": prompt}],
            max_tokens=1200,
            json_mode=True
        )
        result = json.loads(raw)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/ai/drug-checker/quick', methods=['POST'])
@login_required
def quick_drug_check():
    """Quick check when doctor adds a new prescription — check against patient's current meds."""
    data       = request.get_json()
    patient_id = data.get('patient_id')
    new_drug   = data.get('new_drug', '').strip()

    if not patient_id or not new_drug:
        return jsonify({'safe': True, 'message': 'No interactions found'})

    p = Patient.query.get(patient_id)
    if not p or not p.medications:
        return jsonify({'safe': True, 'message': 'No existing medications to check against'})

    existing = [m.strip() for m in p.medications.split(',') if m.strip()]
    if not existing:
        return jsonify({'safe': True, 'message': 'No existing medications'})

    all_drugs = existing + [new_drug]
    
    prompt = f"""Patient {p.name}, age {p.age}.
Current medications: {', '.join(existing)}
New drug being prescribed: {new_drug}
Known allergies: {p.allergies or 'None'}

Quick interaction check. Respond in JSON:
{{
  "safe": true/false,
  "risk_level": "SAFE"/"CAUTION"/"DANGEROUS",
  "message": "one clear sentence",
  "details": "brief explanation if not safe",
  "action": "what doctor should do"
}}"""

    try:
        raw = call_gpt([{"role": "user", "content": prompt}], max_tokens=300, json_mode=True)
        result = json.loads(raw)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'safe': True, 'message': 'Check skipped', 'error': str(e)})


# ═══════════════════════════════════════════════════════════════
#  3. HEALTH RISK SCORE
# ═══════════════════════════════════════════════════════════════

@ai_bp.route('/ai/risk-score')
@login_required
def risk_score_page():
    patients = Patient.query.filter_by(is_active=True).order_by(Patient.name).all()
    return render_template('ai/risk_score.html', patients=patients)


@ai_bp.route('/ai/risk-score/calculate', methods=['POST'])
@login_required
def calculate_risk():
    data       = request.get_json()
    patient_id = data.get('patient_id')
    lifestyle  = data.get('lifestyle', {})  # additional lifestyle data from form

    if not patient_id:
        return jsonify({'error': 'Patient ID required'}), 400

    p = Patient.query.get(patient_id)
    if not p:
        return jsonify({'error': 'Patient not found'}), 404

    # Build full patient picture
    visits = p.visits.order_by(Visit.visited_at.desc()).limit(10).all()
    visit_history = "\n".join([
        f"- {v.visited_at.strftime('%b %Y')}: {v.diagnosis}. Rx: {v.prescription or 'None'}"
        for v in visits
    ]) or "No recorded visits"

    prompt = f"""You are a preventive health AI for AarogyaLink rural India health platform.

PATIENT DATA:
- Name: {p.name}
- Age: {p.age} years
- Gender: {p.gender}
- Blood Group: {p.blood_group}
- Village: {p.village}, {p.district}, {p.state}
- Known Conditions: {p.conditions or 'None'}
- Known Allergies: {p.allergies or 'None'}
- Current Medications: {p.medications or 'None'}
- Total visits: {p.visit_count()}

VISIT HISTORY:
{visit_history}

LIFESTYLE FACTORS PROVIDED:
- Smoking: {lifestyle.get('smoking', 'unknown')}
- Alcohol: {lifestyle.get('alcohol', 'unknown')}
- Physical activity: {lifestyle.get('activity', 'unknown')}
- Diet type: {lifestyle.get('diet', 'unknown')}
- Water source: {lifestyle.get('water', 'unknown')}
- Occupation: {lifestyle.get('occupation', 'unknown')}
- Family history: {lifestyle.get('family_history', 'unknown')}

Calculate a comprehensive health risk score and analysis. Respond ONLY in valid JSON:
{{
  "overall_score": <integer 0-100, where 100 = highest risk>,
  "risk_category": "LOW" | "MODERATE" | "HIGH" | "CRITICAL",
  "risk_color": "#22c55e" | "#f59e0b" | "#ef4444" | "#dc2626",
  "summary": "2-3 sentence plain English summary of patient's health status",
  
  "domain_scores": {{
    "cardiovascular": {{"score": 0-100, "label": "brief reason"}},
    "metabolic": {{"score": 0-100, "label": "brief reason"}},
    "respiratory": {{"score": 0-100, "label": "brief reason"}},
    "infectious_disease": {{"score": 0-100, "label": "brief reason"}},
    "mental_health": {{"score": 0-100, "label": "brief reason"}},
    "lifestyle": {{"score": 0-100, "label": "brief reason"}}
  }},
  
  "top_risk_factors": [
    {{"factor": "risk factor name", "impact": "high/medium/low", "description": "explanation"}}
  ],
  
  "protective_factors": [
    "positive factor 1", "positive factor 2"
  ],
  
  "immediate_actions": [
    {{"action": "specific action", "urgency": "immediate/this_week/this_month", "reason": "why"}}
  ],
  
  "screening_recommendations": [
    {{"test": "test name", "frequency": "how often", "reason": "why needed"}}
  ],
  
  "5_year_outlook": "honest but sensitive 2-sentence prediction",
  
  "doctor_alert": true/false,
  "doctor_alert_reason": "reason if alert is true"
}}

Be clinically accurate. Consider rural India disease burden (TB, malaria, diabetes, hypertension). 
Be honest but compassionate in the language."""

    try:
        raw = call_gpt([{"role": "user", "content": prompt}], max_tokens=1500, json_mode=True)
        result = json.loads(raw)
        
        # Save score to session for display
        result['patient_name'] = p.name
        result['patient_id']   = p.id
        result['calculated_at'] = datetime.utcnow().isoformat()
        
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/ai/risk-score/batch', methods=['POST'])
@login_required
def batch_risk():
    """Get risk scores for all patients in ASHA's list — quick overview."""
    if not current_user.is_asha() and not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403

    patients = Patient.query.filter_by(
        registered_by=current_user.id, is_active=True
    ).all()

    results = []
    for p in patients[:20]:  # limit to 20
        age_risk    = min(100, max(0, (p.age - 30) * 1.5)) if p.age > 30 else 0
        cond_count  = len(p.conditions_list())
        cond_risk   = min(100, cond_count * 15)
        med_count   = len(p.medications_list())
        allergy_risk= 20 if p.allergies_list() else 0
        base_score  = int((age_risk * 0.4 + cond_risk * 0.4 + allergy_risk * 0.2))
        
        results.append({
            'id': p.id,
            'name': p.name,
            'age': p.age,
            'score': min(100, base_score),
            'conditions': cond_count,
        })

    results.sort(key=lambda x: x['score'], reverse=True)
    return jsonify({'success': True, 'patients': results})


# ═══════════════════════════════════════════════════════════════
#  AAROGYABOT — Advanced Voice AI Assistant
# ═══════════════════════════════════════════════════════════════

@ai_bp.route('/ai/chatbot/chat', methods=['POST'])
def chatbot_chat():
    """AarogyaBot — context-aware AI assistant. Privacy-first."""
    from flask import session
    data     = request.get_json()
    user_msg = data.get('message', '').strip()
    history  = data.get('history', [])
    language = data.get('language', 'auto')

    if not user_msg:
        return jsonify({'error': 'Empty message'}), 400

    # ── Determine who is asking (privacy gate) ──
    is_staff   = current_user.is_authenticated
    user_role  = current_user.role if is_staff else 'public'
    user_name  = current_user.name if is_staff else 'Guest'

    # ── Build patient context ONLY for authenticated staff ──
    patient_ctx = ""
    actions_ctx = ""

    if is_staff:
        if current_user.is_admin():
            my_patients = Patient.query.filter_by(is_active=True).limit(50).all()
        elif current_user.is_asha():
            my_patients = Patient.query.filter_by(registered_by=current_user.id, is_active=True).all()
        else:  # doctor — can access all active patients (they scan QR)
            my_patients = Patient.query.filter_by(is_active=True).limit(50).all()

        # Pending follow-ups
        followups = []
        for p in my_patients:
            lv = p.last_visit()
            if lv and lv.follow_up:
                try:
                    if lv.follow_up <= datetime.utcnow().date():
                        followups.append(p.name)
                except Exception:
                    pass

        patient_summary = []
        for p in my_patients[:30]:
            conds = ', '.join(p.conditions_list()) or 'None'
            allergies = ', '.join(p.allergies_list()) or 'None'
            patient_summary.append(
                f"- {p.name} (ID:{p.id}, {p.age}y, {p.gender}, {p.village}): "
                f"Conditions: {conds}; Allergies: {allergies}; Visits: {p.visit_count()}"
            )

        patient_ctx = f"""
═══ AUTHORIZED USER DATA (PRIVATE) ═══
You are speaking with {user_name}, a verified {user_role.upper()}.
They have access to {len(my_patients)} patients.

PATIENTS THIS USER CAN ACCESS:
{chr(10).join(patient_summary) if patient_summary else 'No patients registered yet.'}

PENDING FOLLOW-UPS TODAY: {', '.join(followups) if followups else 'None'}
"""
        actions_ctx = """
ACTIONS YOU CAN SUGGEST (tell user to click):
- Register patient → /patient/register
- Scan QR → /scan
- Symptom Checker → /ai/symptom-checker
- Drug Interaction Checker → /ai/drug-checker
- Health Risk Score → /ai/risk-score
- Dashboard → /dashboard
- Doctor slots → /consult/doctor/slots
"""
    else:
        patient_ctx = """
═══ PUBLIC USER (NOT LOGGED IN) ═══
This user is NOT authenticated. You must NEVER reveal any specific patient's
private data. You can only answer general questions about AarogyaLink,
how it works, health information, and guide them to register or login.
"""

    # ── Language instruction ──
    lang_map = {
        'hi': "Respond in Hindi (Devanagari). Keep medical terms in English.",
        'pa': "Respond in Punjabi (Gurmukhi script). Keep medical terms in English.",
        'en': "Respond in clear, simple English.",
        'auto': "Detect the language of the user's message (Hindi, Punjabi, or English) and respond in that SAME language. If Hindi use Devanagari, if Punjabi use Gurmukhi.",
    }
    lang_instruction = lang_map.get(language, lang_map['auto'])

    # ── System prompt ──
    system_prompt = f"""You are AarogyaBot 🌿 — the friendly, intelligent voice assistant for AarogyaLink, a rural health records and telemedicine platform in India.

ABOUT AAROGYALINK (you know everything about it):
- A platform giving every rural Indian a lifelong QR health card
- ASHA workers register patients (voice in Hindi, works offline, 2 min)
- Each patient gets a unique ID, QR code, and printable PDF health card (₹3 to print)
- Doctors scan the QR at any hospital → see full medical history instantly
- Doctors add visits with diagnosis, prescription, follow-up dates
- Telemedicine: patients book video consultations with verified doctors, pay via UPI, join Jitsi video calls
- AI Tools: Symptom Checker (Hindi/English chat), Drug Interaction Checker, Health Risk Score
- Three roles: ASHA Worker (registers), Doctor (treats), Admin (verifies & manages)
- DPDPA 2023 compliant, works offline, free for patients forever

{patient_ctx}
{actions_ctx}

CRITICAL PRIVACY RULES:
- If user is NOT logged in (public), NEVER reveal any real patient's name, disease, phone, or records
- ONLY discuss patients listed in the AUTHORIZED USER DATA above
- If asked about a patient NOT in the list, say you don't have access to that patient
- Never expose Aadhar numbers or phone numbers
- Keep all conversation private to this session

YOUR PERSONALITY:
- Warm, helpful, concise. Like a knowledgeable colleague.
- Use simple language suitable for rural healthcare workers
- For medical questions, give helpful info but always recommend consulting a doctor
- When user wants to do something, guide them to the right page/button
- Use occasional emojis (🌿💊📋) but don't overdo it

{lang_instruction}

Keep responses SHORT and conversational (2-4 sentences usually) since this is a voice chat. Only go longer if explaining something complex."""

    messages = [{"role": "system", "content": system_prompt}]
    for h in history[-8:]:
        messages.append({"role": h['role'], "content": h['content']})
    messages.append({"role": "user", "content": user_msg})

    try:
        reply = call_gpt(messages, max_tokens=500)
        return jsonify({'reply': reply, 'role': user_role})
    except Exception as e:
        print(f"[AarogyaBot error] {e}")
        return jsonify({'reply': f"⚠️ {str(e)}", 'error': str(e)}), 200