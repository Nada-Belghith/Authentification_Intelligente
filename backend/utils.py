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


