from flask import render_template, request, jsonify
import datetime
import time
import traceback # Ajout de traceback pour les erreurs

from . import app, db
from .models import Log
from .utils import make_ia_prediction 
from .blockchain import add_log_to_chain


# Base d'utilisateurs simulée
USER_DB = {
    "admin": "password123",
    "sara": "pass"
}


@app.route('/login')
def login_page():
    return render_template('login.html')


# --- FONCTIONS EXTERNES DE TRAITEMENT ---

def _extract_request_data(request, data, login_status: str) -> dict:
    """Extrait et normalise toutes les données pertinentes de la requête."""
    
    user_agent = request.headers.get('User-Agent', 'Unknown')
    simulated_browser = "Unknown"
    if "Firefox" in user_agent: simulated_browser = "Firefox"
    elif "Chrome" in user_agent: simulated_browser = "Chrome"
    elif "Safari" in user_agent: simulated_browser = "Safari"
    elif "Edge" in user_agent: simulated_browser = "Edge"
    elif "Opera" in user_agent: simulated_browser = "Opera"
    
    if 'browser' in data:
        simulated_browser = data['browser']
        
    return {
        "userid": data.get('username', ''),
        "status": login_status,
        "ip": request.remote_addr,
        "country": data.get('country', 'Unknown'),
        "device": data.get('device', 'Unknown'),
        "browser": simulated_browser
    }


def _process_ia_and_blockchain(new_log_entry: Log):
    """Gère l'analyse IA, la mise à jour du risk_label, et l'envoi à la blockchain."""
    username = new_log_entry.userid
    ip_address = new_log_entry.ip
    
    try:
        # --- 1. Analyse IA (Préparation de la séquence) ---
        time_threshold = datetime.datetime.now() - datetime.timedelta(minutes=1)
        recent_logs = Log.query.filter(
            (Log.timestamp >= time_threshold) &
            ((Log.userid == username) | (Log.ip == ip_address))
        ).order_by(Log.timestamp.asc()).all()

        print(f"[Backend] Logs analysés par IA (1 min) : {len(recent_logs)}")

        sequence_logs = []
        prev_data = {}

        for i, log in enumerate(recent_logs):
            # Récupération des données brutes (avec fallback pour 'browser')
            # L'attribut temp_browser est utilisé pour le log qu'on vient d'ajouter
            raw_browser = getattr(log, 'browser', getattr(log, 'temp_browser', 'Unknown'))
            raw_country = log.country or "Unknown"
            raw_device = log.device or "Unknown"

            # Calcul CONTEXT_CHANGE pour l'IA
            context_change = "False"
            if prev_data:
                if (log.ip != prev_data['ip']) or (raw_country != prev_data['country']) or (raw_device != prev_data['device']):
                    context_change = "True"

            log_string = (
                f"(STATUS={log.status} USERID={log.userid.replace(' ', '_')} IP={log.ip}"
                f" COUNTRY={raw_country} DEVICE={raw_device} BROWSER={raw_browser}"
                f" CONTEXT_CHANGE={context_change})"
            )
            sequence_logs.append(log_string)
            
            # Mise à jour précédents pour le prochain tour
            prev_data = {'ip': log.ip, 'country': raw_country, 'device': raw_device}

        # --- 2. Prédiction et Décision ---
        full_sequence = " ".join(sequence_logs)
        current_log_string = sequence_logs[-1] if sequence_logs else ""
        
        # Prédictions
        result_sqli = make_ia_prediction(current_log_string)
        result_history = make_ia_prediction(full_sequence)
        
        # Logique de décision (Priorité: SQL > Brute > Usurpation)
        risk_code = 'benin'
        label_sqli = result_sqli.get("prediction_label", "").lower()
        label_history = result_history.get("prediction_label", "").lower()
        
        if 'sql' in label_sqli:
            risk_code = 'sql'
        elif 'brute' in label_history:
            risk_code = 'brut'
        elif 'usurp' in label_history:
            risk_code = 'usur'

        # Mise à jour BDD
        new_log_entry.risk_label = risk_code
        db.session.add(new_log_entry)
        db.session.commit()

        # --- 3. Envoi Blockchain (pour TOUS les logs analysés par l'IA) ---
        entry = {
            'userid': new_log_entry.userid, 'ip': new_log_entry.ip, 'country': new_log_entry.country, 
            'device': new_log_entry.device, 'browser': new_log_entry.browser,
            'risk': risk_code
        }
        ok = add_log_to_chain(entry)
        print(f"[blockchain] log sent: {ok}")
        
        return risk_code
    
    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de l'analyse IA/Blockchain : {e}")
        traceback.print_exc()
        return 'error'


@app.route('/handle_login', methods=['POST'])
def handle_login():
    """Gère la tentative de connexion et applique la logique de sécurité basée UNIQUEMENT sur l'IA."""
    
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')
    
    # Vérification initiale de l'authentification
    login_status = "True" if username in USER_DB and USER_DB[username] == password else "False"
    
    # --- A. Extraction et Normalisation des Données ---
    current_log_data = _extract_request_data(request, data, login_status)
    print(f"\n[Backend] Nouvelle tentative : {username} | Pays: {current_log_data['country']} | Browser: {current_log_data['browser']}")

    # --- B. Enregistrement du log (Pré-IA) ---
    try:
        new_log_entry = Log(
            ip=current_log_data['ip'], userid=username, status=login_status,
            country=current_log_data['country'], device=current_log_data['device'],
            browser=current_log_data['browser'] 
        )
        # Nécessaire pour l'IA immédiate (jusqu'à ce que la BDD soit mise à jour)
        new_log_entry.temp_browser = current_log_data['browser'] 
        db.session.add(new_log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[Backend] Erreur BDD insertion: {e}")
        return jsonify({"message": "Erreur interne (Log)"}), 500

    # --- C. Analyse IA, Mise à jour BDD et Blockchain ---
    risk_code = _process_ia_and_blockchain(new_log_entry)
    
    if risk_code == 'error':
        return jsonify({"message": "Erreur traitement sécurité"}), 500

    # --- D. Actions de Blocage (Post-IA) ---
    # Le blocage est maintenant basé uniquement sur le risque prédit par l'IA.
    
    if risk_code == 'sql':
        print(f"[Backend] ALERTE MAX: SQL Injection détectée (IA)")
        return jsonify({"message": "ALERTE SÉCURITÉ : SQL Injection détectée."}), 403

    if risk_code == 'brut':
        print(f"[Backend] ALERTE: Brute Force détecté (IA)")
        return jsonify({"message": "ALERTE SÉCURITÉ : Brute Force détectée."}), 403

    if risk_code == 'usur':
        print(f"[Backend] ALERTE: Usurpation détectée (IA).")
        return jsonify({"message": "Usurpation détectée."}), 401

    # --- E. Réponse Standard ---
    if login_status == "False":
        return jsonify({"message": "Identifiants incorrects."}), 401

    return jsonify({"message": f"Bienvenue {username}.", "risk": risk_code}), 200