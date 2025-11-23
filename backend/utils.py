import requests
from . import app


def make_ia_prediction(sequence: str):
    try:
        response_ia = requests.post(app.config.get('API_IA_URL'), json={"sequence": sequence})
        if response_ia.status_code == 200:
            return response_ia.json()
        else:
            app.logger.warning(f"Erreur API IA (Code {response_ia.status_code})")
            return {"prediction_label": "Bénin", "confidence": 0.0}
    except Exception as e:
        app.logger.error(f"ERREUR Connexion API IA: {e}")
        return {"prediction_label": "Bénin", "confidence": 0.0}


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
