import torch
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import uvicorn

# --- 1. Configuration ---
MODEL_DIR = "mon_modele_distilbert_V5" # Le nom de votre dossier
app = FastAPI()

# C'est le "dictionnaire" de traduction
# DOIT être le même que celui de l'entraînement
LABEL_MAP = {
    0: "Bénin", 
    1: "Usurpation de Compte", 
    2: "Brute Force", 
    3: "SQL Injection"
}

# --- 2. Chargement du Modèle (au démarrage) ---
try:
    print(f"Chargement du tokenizer depuis  '{MODEL_DIR}'...")
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_DIR)
    
    print(f"Chargement du modèle depuis '{MODEL_DIR}'...")
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_DIR)
    
    # Mettre le modèle en mode évaluation
    model.eval()
    print("✅ Modèle chargé avec succès.")
except OSError:
    print(f"ERREUR: Dossier '{MODEL_DIR}' non trouvé.")
    print("Assurez-vous que le dossier du modèle est dans le même répertoire que api.py")
    exit()

# --- 3. Définir le format d'entrée (ce que l'API attend) ---
class LogSequenceRequest(BaseModel):
    sequence: str  # L'API attend un JSON avec une clé "sequence"

# --- 4. Créer l'endpoint de prédiction ---
@app.post("/predict")
async def predict(request: LogSequenceRequest):
    """
    Prend une séquence de logs, la tokenise et renvoie la prédiction du modèle.
    """
    
    # 1. Préparer la "phrase" pour le modèle
    inputs = tokenizer(
        request.sequence,
        return_tensors="pt", # Tenseurs PyTorch
        truncation=True,
        padding=True,
        max_length=256 # Doit être la même que l'entraînement
    )

    # 2. Faire la prédiction (sans calculer de gradient)
    with torch.no_grad():
        logits = model(**inputs).logits

    # 3. Obtenir la prédiction (l'ID du label le plus probable)
    predicted_class_id = logits.argmax().item()
    
    # 4. Traduire l'ID en nom de label
    predicted_label = LABEL_MAP.get(predicted_class_id, "Label Inconnu")
    
    # (Bonus) Obtenir le score de confiance
    probabilities = torch.nn.functional.softmax(logits, dim=-1)
    confidence_score = probabilities[0][predicted_class_id].item()

    # 5. Renvoyer le résultat
    return {
        "prediction_label": predicted_label,
        "prediction_id": predicted_class_id,
        "confidence": confidence_score
    }

# --- 5. Lancer le serveur (pour les tests locaux) ---
if __name__ == "__main__":
    print("Pour démarrer l'API, exécutez dans le terminal :")
    print("uvicorn api:app --reload")
    # uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)