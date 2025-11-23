from flask import Flask, request, render_template, jsonify
import requests
import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
import random

# --- Configuration ---
app = Flask(__name__)
DB_USER = 'postgres'
DB_PASS = 'postgres'  # <-- TON MOT DE PASSE
DB_HOST = 'localhost'
DB_NAME = 'auth_logs_db'
app.config['SQLALCHEMY_DATABASE_URI'] = \
    f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?client_encoding=utf8'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# URL de ton API IA
API_IA_URL = "http://127.0.0.1:8000/predict"

# Base d'utilisateurs simulée
USER_DB = {
    "admin": "password123",
    "sara": "pass"
}

# --- Modèle de la table 'log' ---
class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now)
    ip = db.Column(db.String(45))
    userid = db.Column(db.String(255))
    status = db.Column(db.String(10))
    country = db.Column(db.String(50))
    device = db.Column(db.String(50))
    # risk_label codes: 'usur' (usurpation), 'brut' (brute force), 'benin' (benign), 'sql' (sql injection)
    risk_label = db.Column(db.String(50), default='benin')

# --- Détection Usurpation ---
def detect_hijacking(last_log, current_log):
    score = 0
    details = []

    WEIGHTS = {"ip": 40, "country": 40, "device": 30}

    if last_log.ip != current_log["ip"]:
        score += WEIGHTS["ip"]
        details.append("IP différente")
    if last_log.country != current_log["country"]:
        score += WEIGHTS["country"]
        details.append("Pays différent")
    if last_log.device != current_log["device"]:
        score += WEIGHTS["device"]
        details.append("Device différent")

    hijacking = score >= 60  # seuil critique
    return hijacking, score, details

# --- Routes ---
@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/simulate_bruteforce', methods=['POST'])
def simulate_bruteforce():
    print("\n[Backend] Génération de trafic suspect...")
    random_ip = f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
    sql_query = text(f"""
        INSERT INTO log (timestamp, ip, userid, status, country, device, risk_label)
        SELECT (NOW() - INTERVAL '50 seconds') + (n * INTERVAL '1 second'),
               '{random_ip}', 'admin', 'False', 'France', 'Mobile', 'brut'
        FROM generate_series(1, 50) AS n;
    """)
    try:
        db.session.execute(sql_query)
        db.session.commit()
        return jsonify({"message": "50 logs d'échec insérés dans la dernière minute."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"message": "Erreur simulation."}), 500

# --- Appel IA ---
def make_ia_prediction(sequence: str):
    try:
        response_ia = requests.post(API_IA_URL, json={"sequence": sequence})
        if response_ia.status_code == 200:
            return response_ia.json()
        else:
            print(f"[Backend] Erreur API IA (Code {response_ia.status_code})")
            return {"prediction_label": "Bénin", "confidence": 0.0}
    except Exception as e:
        print(f"[Backend] ERREUR Connexion API IA: {e}")
        return {"prediction_label": "Bénin", "confidence": 0.0}

@app.route('/handle_login', methods=['POST'])
def handle_login():
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')
    simulated_country = data.get('country', 'France')
    simulated_device = data.get('device', 'Desktop')
    ip_address = request.remote_addr

    print(f"\n[Backend] Nouvelle tentative : {username} ({simulated_country})")

    login_status = "True" if username in USER_DB and USER_DB[username] == password else "False"

    # --- 1. Vérification usurpation avant insertion ---
    try:
        last_valid_log = Log.query.filter_by(userid=username, status="True") \
                          .order_by(Log.timestamp.desc()).first()

        current_log = {
            "ip": ip_address,
            "country": simulated_country,
            "device": simulated_device
        }

        if last_valid_log:
            hijacking, score_hj, details_hj = detect_hijacking(last_valid_log, current_log)
            if hijacking:
                print(f"[Backend] ALERTE USURPATION: score={score_hj}, détails={details_hj}")
                # Enregistrer une entrée d'usurpation dans la BDD avant de bloquer
                try:
                    usurp_log = Log(
                        ip=current_log.get("ip"),
                        userid=username,
                        status=login_status,
                        country=current_log.get("country"),
                        device=current_log.get("device"),
                        risk_label='usur'
                    )
                    db.session.add(usurp_log)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"[Backend] Erreur BDD insertion usurpation: {e}")

                return jsonify({
                    "message": "⚠️ Suspicion d'usurpation de compte.",
                    "risk_score": score_hj,
                    "details": details_hj
                }), 401
    except Exception as e:
        print(f"[Backend] Erreur BDD lors détection usurpation: {e}")
        return jsonify({"message": "Erreur interne"}), 500

    # --- 2. Enregistrement du log ---
    try:
        new_log_entry = Log(
            ip=ip_address,
            userid=username,
            status=login_status,
            country=simulated_country,
            device=simulated_device
        )
        db.session.add(new_log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[Backend] Erreur BDD insertion: {e}")
        return jsonify({"message": "Erreur interne"}), 500

    # --- 3. Analyse IA (historique 1 min) ---
    try:
        time_threshold = datetime.datetime.now() - datetime.timedelta(minutes=1)
        recent_logs = Log.query.filter(
            (Log.timestamp >= time_threshold) &
            ((Log.userid == username) | (Log.ip == ip_address))
        ).order_by(Log.timestamp.asc()).all()

        print(f"[Backend] Logs analysés (1 min) : {len(recent_logs)}")

        sequence_logs = []
        current_log_string = ""

        for i, log in enumerate(recent_logs):
            safe_userid = log.userid.replace(" ", "_")
            raw_country = log.country if log.country else "Unknown"
            raw_device = log.device if log.device else "Unknown"

            ai_country = "Synth_B9" if raw_country in ["France", "Tunisia", "USA", "Unknown"] else raw_country
            ai_device = "Synth_B9" if raw_device in ["Desktop", "Mobile", "Unknown"] else raw_device

            log_string = (
                f"(STATUS={log.status}"
                f" USERID={safe_userid}"
                f" IP={log.ip}"
                f" COUNTRY={ai_country}"
                f" DEVICE={ai_device}"
                f" BROWSER=Synth_B9)"
            )
            sequence_logs.append(log_string)
            if i == len(recent_logs) - 1:
                current_log_string = log_string

        # --- Analyse contenu et historique ---
        result_sqli = make_ia_prediction(current_log_string)
        label_sqli = result_sqli.get("prediction_label")

        full_sequence = " ".join(sequence_logs)
        result_history = make_ia_prediction(full_sequence)
        label_history = result_history.get("prediction_label")

        # Normalize labels to short risk codes: 'sql', 'brut', 'usur', 'benin'
        risk_code = 'benin'
        if label_sqli and 'sql' in label_sqli.lower():
            risk_code = 'sql'
        elif label_history and 'brute' in label_history.lower():
            risk_code = 'brut'
        elif label_history and (('usurp' in label_history.lower()) or ('usurpation' in label_history.lower())):
            risk_code = 'usur'

        # Update the inserted log with the computed risk_label
        try:
            new_log_entry.risk_label = risk_code
            db.session.add(new_log_entry)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[Backend] Erreur BDD mise à jour risk_label: {e}")

        # React according to detection
        if risk_code == 'sql':
            print(f"[Backend] ALERTE MAX: SQL Injection détectée")
            return jsonify({"message": "ALERTE SÉCURITÉ : SQL Injection détectée. Accès bloqué."}), 403

        if risk_code == 'brut':
            print(f"[Backend] ALERTE: Brute Force détecté")
            return jsonify({"message": "ALERTE SÉCURITÉ : Brute Force détectée. Accès bloqué."}), 403

        if risk_code == 'usur':
            print(f"[Backend] ALERTE: Usurpation détectée (Contexte).")
            return jsonify({"message": "Activité suspecte (Usurpation). Vérification requise."}), 401

        if login_status == "False":
            return jsonify({"message": "Identifiants incorrects."}), 401

        print(f"[Backend] Verdict IA : {label_history} ({result_history.get('confidence'):.2f}) -> risk={risk_code}")
        return jsonify({"message": f"Bienvenue {username}. Connexion sécurisée.", "risk": risk_code}), 200

    except Exception as e:
        print(f"Erreur lors de l'analyse : {e}")
        return jsonify({"message": "Erreur traitement sécurité"}), 500

# --- Lancement ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5000, debug=True)
