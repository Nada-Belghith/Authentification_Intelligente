"""Central configuration loaded from environment variables.

This module will try to read a `.env` file if `python-dotenv` is installed
so you can keep local secrets in a `.env` file (which should be gitignored).
"""
import os
from pathlib import Path

# Try to load .env if python-dotenv is installed (optional)
try:
	from dotenv import load_dotenv
	# load .env from project root (one level up from backend/)
	project_root = Path(__file__).resolve().parents[1]
	dotenv_path = project_root / '.env'
	if dotenv_path.exists():
		load_dotenv(dotenv_path)
except Exception:
	# dotenv not installed or failed to load; continue using os.environ
	pass

# Database configuration
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'auth_logs_db')

# URL of the IA API
API_IA_URL = os.getenv('API_IA_URL', 'http://127.0.0.1:8000/predict')

# Blockchain / Ganache settings
GANACHE_URL = os.getenv('GANACHE_URL', 'http://127.0.0.1:7545')
CHAIN_ACCOUNT_ADDRESS = os.getenv('CHAIN_ACCOUNT_ADDRESS', '')
CHAIN_PRIVATE_KEY = os.getenv('CHAIN_PRIVATE_KEY', '')
# Path to the contract ABI+address file used by the backend
# Default points to Truffle build artifact relative to project root
_default_contract = os.getenv('CONTRACT_DATA_FILE', 'eth-security-logger/build/contracts/SecurityLogger.json')
# Make path absolute relative to project root if it's a relative path
_proj_root = Path(__file__).resolve().parents[1]
CONTRACT_DATA_FILE = str((_proj_root / _default_contract).resolve())
