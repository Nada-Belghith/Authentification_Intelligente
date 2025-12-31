# 🔐 Système d'Authentification Intelligente Sécurisée

Un système d'authentification avancé qui combine **machine learning**, **blockchain** et **analyse comportementale** pour détecter et prévenir les tentatives d'accès frauduleux aux systèmes médicaux.

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture du projet](#architecture-du-projet)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Comment ça marche](#comment-ça-marche)
6. [Utilisation](#utilisation)
7. [Structure des fichiers](#structure-des-fichiers)
8. [Technologies utilisées](#technologies-utilisées)
9. [Fonctionnalités principales](#fonctionnalités-principales)

---

## 🎯 Vue d'ensemble

Ce projet est un **système d'authentification de nouvelle génération** qui:

- ✅ **Authentifie les utilisateurs** via un formulaire de connexion sécurisé
- 🧠 **Analyse le comportement** en temps réel à l'aide d'IA (DistilBERT)
- 🔗 **Enregistre chaque accès** sur une blockchain Ethereum (via Ganache)
- 🚨 **Détecte les menaces** : usurpation d'identité, brute force, injections SQL
- 📊 **Sauvegarde les logs** dans une base de données PostgreSQL
- 💾 **Persiste les risques** sur la blockchain pour l'immuabilité

---

## 🏗️ Architecture du projet

```
AuthentificationIntelligente/
├── app_backend.py                 # Point d'entrée Flask
├── requirements.txt               # Dépendances Python
├── backend/                       # Package backend principal
│   ├── __init__.py               # Configuration Flask/SQLAlchemy
│   ├── config.py                 # Variables d'environnement
│   ├── routes.py                 # Endpoints API
│   ├── models.py                 # Modèles de base de données
│   ├── blockchain.py             # Intégration Ethereum/Ganache
│   └── utils.py                  # Fonctions utilitaires (appels IA)
├── templates/                    # Frontend HTML
│   ├── login.html               # Page de connexion
│   └── home.html                # Page d'accueil
├── eth-security-logger/          # Smart contract Ethereum
│   ├── contracts/
│   │   └── SecurityLogger.sol    # Contrat de logging blockchain
│   ├── migrations/               # Scripts de déploiement
│   ├── build/                    # Artifacts compilés
│   └── truffle-config.js         # Configuration Truffle
├── mon_modele_distilbert_V5/    # Modèle IA pré-entraîné
│   ├── config.json
│   ├── model.safetensors
│   ├── tokenizer_config.json
│   └── vocab.txt
├── dataset_synthetique_Robust_V5.csv # Données d'entraînement
└── api.py                        # API IA séparée 
```

---

## 📦 Installation

### Prérequis

- **Python 3.8+** (testé avec 3.12.2)
- **PostgreSQL** (pour la base de données)
- **Ganache CLI** (pour la blockchain Ethereum locale)
- **Node.js/Npm** (pour Truffle)

### Étapes d'installation

#### 1️⃣ Cloner et préparation

```bash
cd AuthentificationIntelligente
python -m venv .venv
```

#### 2️⃣ Activer l'environnement virtuel

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

#### 3️⃣ Installer les dépendances

```bash
pip install -r requirements.txt
```

#### 4️⃣ Extraire le modèle IA ⚠️ IMPORTANT

Le modèle DistilBERT est compressé pour réduire la taille. **Vous DEVEZ le dézipper** avant de lancer le projet:

```bash
# Depuis le répertoire racine du projet
cd mon_modele_distilbert_V5

# Windows - Clic droit sur le fichier .zip → Extraire tout
# Ou en PowerShell:
Expand-Archive "mon_modele_distilbert_V5.zip" -DestinationPath "."

# Linux/Mac:
unzip mon_modele_distilbert_V5.zip
```

**✅ Après extraction, vous devriez avoir:**
```
mon_modele_distilbert_V5/
├── config.json
├── model.safetensors          ← Ce fichier (volumineux) doit être présent
├── tokenizer_config.json
├── vocab.txt
└── (autres fichiers du modèle)
```

#### 5️⃣ Configurer la base de données PostgreSQL

Créer une base de données PostgreSQL:
```sql
CREATE DATABASE auth_logs_db;
```

#### 6️⃣ Créer un fichier `.env` 

À la racine du projet:
```env
DB_USER=postgres
DB_PASS=votre_mot_de_passe
DB_HOST=localhost
DB_NAME=auth_logs_db

API_IA_URL=http://127.0.0.1:8000/predict

GANACHE_URL=http://127.0.0.1:7545
CHAIN_ACCOUNT_ADDRESS=votre_adresse_ganache
CHAIN_PRIVATE_KEY=votre_clé_privée_ganache
```

---

## ⚙️ Configuration

### Configuration PostgreSQL

```python
# backend/config.py
DB_USER=postgres
DB_PASS=votre_mot_de_passe
DB_HOST=localhost
DB_NAME=auth_logs_db
```

### Configuration Blockchain

```python
GANACHE_URL = 'http://127.0.0.1:7545'          # URL Ganache
CHAIN_ACCOUNT_ADDRESS = '0x...'                # Adresse du compte
CHAIN_PRIVATE_KEY = '0x...'                    # Clé privée
CONTRACT_DATA_FILE = 'eth-security-logger/...' # ABI du contrat
```

### Configuration IA

```python
API_IA_URL = 'http://127.0.0.1:8000/predict'  # Endpoint de l'API IA
```

---

## 🚀 Comment ça marche

### Flux d'authentification

```
┌──────────────────────────────────────────────────────────────┐
│ 1. UTILISATEUR SE CONNECTE (login.html)                     │
│    - Entre username + password                               │
│    - Envoie IP, device, country, browser                    │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│ 2. BACKEND VALIDE LES CREDENTIALS                           │
│    - Vérifie le mot de passe                               │
│    - Extrait les infos requête (IP, User-Agent, etc.)      │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│ 3. CRÉATION DU LOG (models.Log)                             │
│    - Enregistre: IP, userid, status, device, browser       │
│    - Timestamp automatique                                  │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│ 4. ANALYSE IA (utils.make_ia_prediction)                    │
│    - Récupère les logs des 1 dernière minute               │
│    - Crée une séquence: (STATUS=... USERID=... IP=...)     │
│    - Envoie à l'API IA pour prédiction                     │
│    - API retourne: label_risque + confiance                │
│      • "benin" → benin (inoffensif)                        │
│      • "usur" → usurpation d'identité                      │
│      • "brut" → brute force                                │
│      • "sql" → injection SQL                               │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│ 5. UPDATE LOG + BLOCKCHAIN (blockchain.add_log_to_chain)   │
│    - Met à jour risk_label dans la base                    │
│    - Appelle le smart contract Ethereum                    │
│    - Enregistre hash + code de risque sur chaîne           │
│    - Immuabilité garantie                                  │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│ 6. RÉPONSE UTILISATEUR                                      │
│    - Redirection vers home.html si succès                  │
│    - Message d'erreur si détection menace                  │
└──────────────────────────────────────────────────────────────┘
```

### Détail du modèle IA

Le modèle **DistilBERT** analyse une **séquence comportementale**:

```
Exemple de séquence envoyée à l'IA:
(STATUS=success USERID=admin IP=192.168.1.100 COUNTRY=France DEVICE=Windows BROWSER=Chrome CONTEXT_CHANGE=False)
(STATUS=success USERID=admin IP=192.168.1.100 COUNTRY=France DEVICE=Windows BROWSER=Chrome CONTEXT_CHANGE=False)
```

**Catégories de risques détectées:**
- `benin`: Authentification normale et sûre
- `usur`: Usurpation d'identité (même compte depuis contextes différents)
- `brut`: Brute force (tentatives multiples rapides)
- `sql`: Injection SQL ou payload malveillant

---

## 🎮 Utilisation

### Démarrer le système complet

#### Étape 1: Démarrer Ganache (Blockchain)

```bash
# Ouvrir un terminal
ganache-cli -p 7545 --deterministic
# Ou depuis l'interface Ganache GUI
```

#### Étape 2: Démarrer l'API IA (optionnel mais recommandé)

```bash
# Dans un autre terminal
python api.py
# Démarre sur http://127.0.0.1:8000
```

#### Étape 3: Démarrer le serveur Flask

```bash
# Activez le venv d'abord
python app_backend.py
# Démarre sur http://127.0.0.1:5000
```

#### Étape 4: Accéder à l'application

Ouvrir dans votre navigateur:
```
http://127.0.0.1:5000/login
```

### Identifiants de test

Utilisateurs pré-configurés dans [backend/routes.py](backend/routes.py):

```python
USER_DB = {
    "admin": "password123",
    "sara": "pass"
}
```

**Connexion:**
- Username: `admin`
- Password: `password123`

---

## 📁 Structure des fichiers

### `app_backend.py`
Point d'entrée principal du serveur Flask. Initialise la base de données et lance le serveur sur le port 5000.

```python
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crée les tables SQL
    app.run(port=5000, debug=True)
```

### `backend/__init__.py`
Configure Flask et SQLAlchemy:
- Initialise l'app Flask
- Connecte la base de données PostgreSQL
- Enregistre les blueprints (routes, modèles)

### `backend/routes.py`
Gère les endpoints HTTP:
- `GET /login` → Affiche le formulaire de connexion
- `GET /home` → Affiche la page d'accueil
- `POST /api/authenticate` → Traite les authentifications
- `GET /api/logs` → Retourne les logs en JSON

### `backend/models.py`
Définit le modèle `Log` pour la base de données:

```python
class Log(db.Model):
    id              # Identifiant unique
    timestamp       # Quand la tentative s'est produite
    ip              # Adresse IP
    userid          # Nom d'utilisateur
    status          # 'success' ou 'failure'
    country         # Pays estimé
    device          # Type d'appareil (Windows, MacOS, etc.)
    browser         # Navigateur utilisé
    risk_label      # 'benin', 'usur', 'brut', 'sql'
```

### `backend/blockchain.py`
Intégration avec Ethereum via Web3.py:
- Charge le smart contract SecurityLogger
- Envoie les logs à la blockchain
- Garantit l'immuabilité des enregistrements

### `backend/utils.py`
Utilitaires pour appeler l'API IA:
- `make_ia_prediction(sequence)` → Envoie une séquence au modèle IA
- Gère les erreurs de connexion

### `templates/login.html`
Page de connexion élégante avec:
- Formulaire d'authentification
- Détection du navigateur/appareil
- Sélection du pays (géolocalisation simulée)
- Validation côté client

### `templates/home.html`
Page d'accueil après connexion réussie:
- Affiche les informations de l'utilisateur
- Bouton de déconnexion
- Tableau des logs d'authentification

### `eth-security-logger/`
Dossier Smart Contract:
- **contracts/SecurityLogger.sol** → Contrat Solidity pour logger les accès
- **build/contracts/** → ABI et bytecode compilés
- **truffle-config.js** → Configuration Truffle

### `mon_modele_distilbert_V5/`
Modèle IA pré-entraîné:
- **model.safetensors** → Poids du modèle compressés
- **config.json** → Configuration du modèle
- **vocab.txt** → Vocabulaire DistilBERT
- Utilisé pour classifier les séquences comportementales

---

## 🛠️ Technologies utilisées

| Technologie | Rôle |
|------------|------|
| **Flask** | Framework web backend |
| **SQLAlchemy** | ORM pour PostgreSQL |
| **PostgreSQL** | Base de données relationnelle |
| **Web3.py** | Intégration blockchain Ethereum |
| **Ganache** | Blockchain Ethereum locale |
| **Truffle** | Framework smart contract |
| **DistilBERT** | Modèle NLP/ML pour analyse comportementale |
| **Transformers** | Libraire Hugging Face pour IA |
| **HTML/CSS/JS** | Frontend responsive |

---

## ✨ Fonctionnalités principales

### 1. 🔐 Authentification Sécurisée
- Validation des credentials
- Extraction des métadonnées (IP, device, browser)
- Sessions utilisateur

### 2. 🧠 Analyse Comportementale IA
- Analyse de séquences historiques (1 minute)
- Détection des anomalies
- Classification multi-classe (4 types de risques)
- Score de confiance

### 3. 🔗 Enregistrement Blockchain
- Immutabilité des logs
- Audit trail immuable
- Smart contract SecurityLogger
- Traçabilité légale complète

### 4. 📊 Dashboard de Logs
- Visualisation des tentatives d'accès
- Filtrage par utilisateur/IP
- Affichage du risque détecté
- Timestamps précis

### 5. 🚨 Détection de Menaces

| Menace | Code | Indicateurs |
|--------|------|-------------|
| Usurpation | `usur` | Changement IP/Pays/Device fréquent |
| Brute Force | `brut` | Tentatives échouées répétées |
| Injection SQL | `sql` | Payloads malveillants en input |
| Bénin | `benin` | Comportement normal et sûr |

---

## 💡 Exemples pratiques avec Interface

**⚠️ IMPORTANT - Avant de tester:**
1. **Dézipper le modèle IA:** Voir section Installation, Étape 4
2. **Démarrer Ganache:** `ganache-cli -p 7545`
3. **Démarrer l'API IA:** `python api.py`
4. **Démarrer le serveur Flask:** `python app_backend.py`
5. **Accéder à:** `http://127.0.0.1:5000/login`

---

### 1️⃣ BENIN - Authentification Normale ✅

**Scénario:** Un utilisateur légitime se connecte normalement depuis son environnement habituel.

#### Étape 1 - Interface de connexion:

```
┌─────────────────────────────────────────────────────┐
│  🏥 SYSTÈME D'AUTHENTIFICATION MÉDICALE SÉCURISÉE  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Username:  [admin                              ]  │
│  Mot de passe: [••••••••••••••]                     │
│                                                     │
│  Pays: [France ▼]                                   │
│  Appareil: [Windows ▼]                              │
│  Navigateur: [Chrome ▼]                             │
│                                                     │
│               [Connexion]  [Annuler]               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### Étape 2 - Données POST envoyées:

```json
POST /api/authenticate
{
  "username": "admin",
  "password": "password123",
  "country": "France",
  "device": "Windows",
  "browser": "Chrome"
}
```

**Séquence comportementale envoyée à l'IA:**
```
(STATUS=success USERID=admin IP=192.168.1.100 COUNTRY=France DEVICE=Windows BROWSER=Chrome CONTEXT_CHANGE=False)
(STATUS=success USERID=admin IP=192.168.1.100 COUNTRY=France DEVICE=Windows BROWSER=Chrome CONTEXT_CHANGE=False)
```

**Résultat IA:**
```json
{
  "prediction_label": "Bénin",
  "confidence": 0.98,
  "risk_label": "benin"
}
```

**Log en base de données:**
```
id: 1
timestamp: 2025-12-31 14:30:45
ip: 192.168.1.100
userid: admin
status: success
country: France
device: Windows
browser: Chrome
risk_label: benin
```

**Action:** ✅ Authentification réussie → Redirection vers /home

---

### 2️⃣ SQL - Injection SQL 🔓

**Scénario:** Un attaquant tente une injection SQL en utilisant `' OR '1'='1` dans le champ username.

**Données soumises:**
```
POST /api/authenticate
{
  "username": "admin' OR '1'='1",
  "password": "password123",
  "country": "France",
  "device": "Windows",
  "browser": "Firefox"
}
```

**Analyse du backend:**
- La séquence contient un caractère spécial SQL (`'`)
- Pattern reconnu: `' OR '1'='1`
- Le modèle IA détecte la syntaxe suspecte

**Séquence comportementale:**
```
(STATUS=failure USERID=admin__OR__1__1 IP=192.168.1.105 COUNTRY=France DEVICE=Windows BROWSER=Firefox CONTEXT_CHANGE=False)
```

**Résultat IA:**
```json
{
  "prediction_label": "SQL Injection",
  "confidence": 0.96,
  "risk_label": "sql"
}
```

**Log en base de données:**
```
id: 2
timestamp: 2025-12-31 14:31:20
ip: 192.168.1.105
userid: admin' OR '1'='1
status: failure
country: France
device: Windows
browser: Firefox
risk_label: sql
```

**Action:** 🚫 Authentification bloquée + Enregistrement blockchain + Alerte sécurité

---

### 3️⃣ USUR - Usurpation d'Identité 👤

**Scénario:** Même username mais changement simultané de pays, navigateur et localisation = tentative d'usurpation.

**Historique des 3 tentatives (1 minute):**

**Tentative 1 (14:32:00):**
```
POST /api/authenticate
{
  "username": "sara",
  "password": "pass",
  "country": "France",
  "device": "MacOS",
  "browser": "Safari"
}
```
Status: success | IP: 192.168.1.50 | Pays: France | Device: MacOS | Browser: Safari

**Tentative 2 (14:32:15):** [⚠️ Changement détecté]
```
POST /api/authenticate
{
  "username": "sara",
  "password": "pass",
  "country": "Chine",
  "device": "iPhone",
  "browser": "WeChat"
}
```
Status: success | IP: 58.123.45.67 | Pays: Chine | Device: iPhone | Browser: WeChat

**Tentative 3 (14:32:30):** [⚠️⚠️ Changement supplémentaire]
```
POST /api/authenticate
{
  "username": "sara",
  "password": "pass",
  "country": "Russie",
  "device": "Android",
  "browser": "Chrome"
}
```
Status: success | IP: 195.68.89.34 | Pays: Russie | Device: Android | Browser: Chrome

**Séquence comportementale envoyée à l'IA:**
```
(STATUS=success USERID=sara IP=192.168.1.50 COUNTRY=France DEVICE=MacOS BROWSER=Safari CONTEXT_CHANGE=False)
(STATUS=success USERID=sara IP=58.123.45.67 COUNTRY=Chine DEVICE=iPhone BROWSER=WeChat CONTEXT_CHANGE=True)
(STATUS=success USERID=sara IP=195.68.89.34 COUNTRY=Russie DEVICE=Android BROWSER=Chrome CONTEXT_CHANGE=True)
```

**Résultat IA:**
```json
{
  "prediction_label": "Usurpation d'Identité",
  "confidence": 0.94,
  "risk_label": "usur"
}
```

**Logs en base de données:**
```
id: 3 | timestamp: 14:32:00 | userid: sara | ip: 192.168.1.50   | country: France | device: MacOS   | browser: Safari | risk_label: benin
id: 4 | timestamp: 14:32:15 | userid: sara | ip: 58.123.45.67   | country: Chine  | device: iPhone  | browser: WeChat | risk_label: usur
id: 5 | timestamp: 14:32:30 | userid: sara | ip: 195.68.89.34   | country: Russie | device: Android | browser: Chrome | risk_label: usur
```

**Action:** 🚨 Compte compromis → Blocage immédiat → Notification utilisateur → Enregistrement blockchain immuable

---

### 4️⃣ BRUT - Brute Force Attack 🔨

**Scénario:** Même username (correct) mais mot de passe faux multiple fois (attaque par force brute).

**Historique rapide (30 secondes):**

**Tentative 1 (14:33:00):**
```
POST /api/authenticate
{
  "username": "admin",
  "password": "wrongpass1"
}
```
Status: **failure** | IP: 203.45.67.89

**Tentative 2 (14:33:05):**
```
POST /api/authenticate
{
  "username": "admin",
  "password": "wrongpass2"
}
```
Status: **failure** | IP: 203.45.67.89

**Tentative 3 (14:33:10):**
```
POST /api/authenticate
{
  "username": "admin",
  "password": "wrongpass3"
}
```
Status: **failure** | IP: 203.45.67.89

**Tentative 4 (14:33:15):**
```
POST /api/authenticate
{
  "username": "admin",
  "password": "password123"
}
```
Status: **success** | IP: 203.45.67.89

**Séquence comportementale:**
```
(STATUS=failure USERID=admin IP=203.45.67.89 COUNTRY=USA DEVICE=Linux BROWSER=Python CONTEXT_CHANGE=False)
(STATUS=failure USERID=admin IP=203.45.67.89 COUNTRY=USA DEVICE=Linux BROWSER=Python CONTEXT_CHANGE=False)
(STATUS=failure USERID=admin IP=203.45.67.89 COUNTRY=USA DEVICE=Linux BROWSER=Python CONTEXT_CHANGE=False)
(STATUS=success USERID=admin IP=203.45.67.89 COUNTRY=USA DEVICE=Linux BROWSER=Python CONTEXT_CHANGE=False)
```

**Résultat IA:**
```json
{
  "prediction_label": "Brute Force",
  "confidence": 0.97,
  "risk_label": "brut"
}
```

**Logs en base de données:**
```
id: 6  | timestamp: 14:33:00 | userid: admin | status: failure | ip: 203.45.67.89 | risk_label: benin
id: 7  | timestamp: 14:33:05 | userid: admin | status: failure | ip: 203.45.67.89 | risk_label: brut
id: 8  | timestamp: 14:33:10 | userid: admin | status: failure | ip: 203.45.67.89 | risk_label: brut
id: 9  | timestamp: 14:33:15 | userid: admin | status: success | ip: 203.45.67.89 | risk_label: brut
```

**Action:** 🔒 Compte temporairement verrouillé après 3 tentatives échouées → IP blacklistée → Enregistrement blockchain du pattern malveillant

---

## �🔍 Dépannage

### La page de connexion ne s'affiche pas
```
Erreur: Flask ne trouve pas les templates
Solution: Vérifier que le dossier templates/ existe à la racine
```

### Erreur de connexion PostgreSQL
```
psycopg2.OperationalError: connection failed
Solution: 
- Vérifier que PostgreSQL est démarré
- Vérifier les variables d'environnement DB_*
- Créer la base: createdb auth_logs_db
```

### L'API IA ne répond pas
```
Erreur: Connexion refusée sur http://127.0.0.1:8000
Solution:
- Démarrer api.py dans un autre terminal
- Vérifier que le modèle est chargé
```

### Ganache ne se connecte pas
```
Erreur: No contract found at 0x...
Solution:
- Démarrer Ganache: ganache-cli -p 7545
- Redéployer le contrat: cd eth-security-logger && truffle migrate --reset
```

---

## 📝 Fichiers de configuration

### `.env` (optionnel)
```env
# PostgreSQL
DB_USER=postgres
DB_PASS=your_password
DB_HOST=localhost
DB_NAME=auth_logs_db

# API IA
API_IA_URL=http://127.0.0.1:8000/predict

# Blockchain
GANACHE_URL=http://127.0.0.1:7545
CHAIN_ACCOUNT_ADDRESS=0x...
CHAIN_PRIVATE_KEY=0x...
```

### `requirements.txt`
```
flask                    # Framework web
flask_sqlalchemy         # ORM
sqlalchemy              # SQL Toolkit
requests                # Appels HTTP
web3                    # Ethereum integration
py-solc-x              # Compilateur Solidity
```

---

## 🎓 Concepts clés

### Séquence Comportementale
Format standardisé pour l'IA:
```
(STATUS=success USERID=admin IP=192.168.1.1 COUNTRY=FR DEVICE=Windows BROWSER=Chrome CONTEXT_CHANGE=False)
```

### CONTEXT_CHANGE
Indicateur IA pour détecter les changements rapides:
- IP différente → True
- Pays différent → True
- Appareil différent → True

### Risk Labels
4 catégories mutuellement exclusives:
- `benin`: Safe (normal usage)
- `usur`: Account takeover (usurpation)
- `brut`: Brute force attack
- `sql`: SQL injection/malware


---

## 📄 Licence

Ce projet est à usage éducatif et de démonstration.

---

## 🎉 Résumé

Ce projet démontre une **architecture moderne de sécurité** combinant:
- ✅ **Machine Learning** pour l'analyse comportementale
- ✅ **Blockchain** pour l'audit immuable
- ✅ **Architecture microservices** (Frontend/Backend/IA/Blockchain)
- ✅ **Best practices** en authentification sécurisée

Parfait pour des cas d'usage critiques comme les systèmes médicaux! 🏥
