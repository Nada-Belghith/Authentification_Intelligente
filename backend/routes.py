from flask import render_template, request, jsonify
from sqlalchemy.sql import text
import random
import datetime

from . import app, db
from .models import Log
from .utils import make_ia_prediction, detect_hijacking


# Base d'utilisateurs simulée
USER_DB = {
    "admin": "password123",
    "sara": "pass"
}


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


@app.route('/handle_login', methods=['POST'])
def handle_login():
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')

    # --- 1. Récupération des VRAIES données (Crucial pour IA V5) ---
    simulated_country = data.get('country', 'Unknown')
    simulated_device = data.get('device', 'Unknown')
    
    # Extraction intelligente du navigateur via le User-Agent
    user_agent = request.headers.get('User-Agent', 'Unknown')
    simulated_browser = "Unknown"
    if "Firefox" in user_agent: simulated_browser = "Firefox"
    elif "Chrome" in user_agent: simulated_browser = "Chrome"
    elif "Safari" in user_agent: simulated_browser = "Safari"
    elif "Edge" in user_agent: simulated_browser = "Edge"
    elif "Opera" in user_agent: simulated_browser = "Opera"
    # Si le front envoie explicitement le browser (simulation), on l'écrase
    if 'browser' in data:
        simulated_browser = data['browser']

    ip_address = request.remote_addr

    print(f"\n[Backend] Nouvelle tentative : {username} | Pays: {simulated_country} | Browser: {simulated_browser}")

    login_status = "True" if username in USER_DB and USER_DB[username] == password else "False"

    # --- 2. Vérification Usurpation (Règles strictes) ---
    try:
        last_valid_log = Log.query.filter_by(userid=username, status="True") \
                                  .order_by(Log.timestamp.desc()).first()

        current_log_dict = {
            "ip": ip_address,
            "country": simulated_country,
            "device": simulated_device,
            "browser": simulated_browser
        }

        if last_valid_log:
            # Assurez-vous d'avoir mis à jour detect_hijacking pour prendre en compte le browser
            hijacking, score_hj, details_hj = detect_hijacking(last_valid_log, current_log_dict)
            
            if hijacking:
                print(f"[Backend] ALERTE USURPATION (Règles): score={score_hj}, détails={details_hj}")
                # Enregistrement de l'alerte
                try:
                    usurp_log = Log(
                        ip=ip_address, userid=username, status=login_status,
                        country=simulated_country, device=simulated_device,
                        risk_label='usur',
                        browser=simulated_browser 
                    )
                    db.session.add(usurp_log)
                    db.session.commit()
                except Exception:
                    db.session.rollback()

                return jsonify({
                    "message": "⚠️ Suspicion d'usurpation de compte (Règles).",
                    "risk_score": score_hj,
                    "details": details_hj
                }), 401
    except Exception as e:
        print(f"[Backend] Erreur détection usurpation: {e}")

    # --- 3. Enregistrement du log courant ---
    try:
        new_log_entry = Log(
            ip=ip_address,
            userid=username,
            status=login_status,
            country=simulated_country,
            device=simulated_device,
            browser=simulated_browser # Activez ceci si vous avez migré la BDD
        )
        # Stockage temporaire pour l'IA immédiate
        new_log_entry.temp_browser = simulated_browser
        
        db.session.add(new_log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[Backend] Erreur BDD insertion: {e}")
        return jsonify({"message": "Erreur interne"}), 500

    # --- 4. Analyse IA (Format compatible V5) ---
    try:
        time_threshold = datetime.datetime.now() - datetime.timedelta(minutes=1)
        recent_logs = Log.query.filter(
            (Log.timestamp >= time_threshold) &
            ((Log.userid == username) | (Log.ip == ip_address))
        ).order_by(Log.timestamp.asc()).all()

        print(f"[Backend] Logs analysés (1 min) : {len(recent_logs)}")

        sequence_logs = []
        current_log_string = ""
        
        # Variables pour CONTEXT_CHANGE
        prev_ip = None
        prev_country = None
        prev_device = None

        for i, log in enumerate(recent_logs):
            safe_userid = log.userid.replace(" ", "_")
            
            # Récupération Données Brutes (Plus de Synth_B9 !)
            raw_country = log.country if log.country else "Unknown"
            raw_device = log.device if log.device else "Unknown"
            
            # Gestion Browser (BDD vs Temp)
            raw_browser = "Unknown"
            if hasattr(log, 'temp_browser'): 
                raw_browser = log.temp_browser
            elif hasattr(log, 'browser') and log.browser: 
                raw_browser = log.browser
            
            # Calcul CONTEXT_CHANGE
            context_change = "False"
            if prev_ip is not None:
                if (log.ip != prev_ip) or (raw_country != prev_country) or (raw_device != prev_device):
                    context_change = "True"

            log_string = (
                f"(STATUS={log.status}"
                f" USERID={safe_userid}"
                f" IP={log.ip}"
                f" COUNTRY={raw_country}"
                f" DEVICE={raw_device}"
                f" BROWSER={raw_browser}"
                f" CONTEXT_CHANGE={context_change})"
            )
            sequence_logs.append(log_string)
            
            # Mise à jour précédents
            prev_ip = log.ip
            prev_country = raw_country
            prev_device = raw_device
            
            if i == len(recent_logs) - 1:
                current_log_string = log_string

        # Analyse IA
        full_sequence = " ".join(sequence_logs)
        
        # Prédiction SQLi (sur le log actuel uniquement)
        result_sqli = make_ia_prediction(current_log_string)
        label_sqli = result_sqli.get("prediction_label")

        # Prédiction Historique (sur toute la séquence)
        result_history = make_ia_prediction(full_sequence)
        label_history = result_history.get("prediction_label")

        # Logique de décision (Risk Score)
        risk_code = 'benin'
        
        # Priorité 1 : SQL Injection
        if label_sqli and 'sql' in label_sqli.lower():
            risk_code = 'sql'
        # Priorité 2 : Brute Force
        elif label_history and 'brute' in label_history.lower():
            risk_code = 'brut'
        # Priorité 3 : Usurpation IA
        elif label_history and (('usurp' in label_history.lower()) or ('usurpation' in label_history.lower())):
            risk_code = 'usur'

        # Mise à jour du label en BDD
        try:
            new_log_entry.risk_label = risk_code
            db.session.add(new_log_entry)
            db.session.commit()
        except Exception:
            db.session.rollback()

        # --- Actions de Blocage ---
        if risk_code == 'sql':
            print(f"[Backend] ALERTE MAX: SQL Injection détectée")
            return jsonify({"message": "ALERTE SÉCURITÉ : SQL Injection détectée."}), 403

        if risk_code == 'brut':
            print(f"[Backend] ALERTE: Brute Force détecté")
            return jsonify({"message": "ALERTE SÉCURITÉ : Brute Force détectée."}), 403

        if risk_code == 'usur':
            print(f"[Backend] ALERTE: Usurpation détectée (IA).")
            return jsonify({"message": "Activité suspecte détectée."}), 401

        if login_status == "False":
            return jsonify({"message": "Identifiants incorrects."}), 401

        return jsonify({"message": f"Bienvenue {username}.", "risk": risk_code}), 200

    except Exception as e:
        print(f"Erreur lors de l'analyse : {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"message": "Erreur traitement sécurité"}), 500