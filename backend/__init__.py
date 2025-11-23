from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import DB_USER, DB_PASS, DB_HOST, DB_NAME, API_IA_URL

# Create app and configure
# Keep templates folder at project root
app = Flask(__name__, template_folder='../templates')
app.config['SQLALCHEMY_DATABASE_URI'] = \
    f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?client_encoding=utf8'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['API_IA_URL'] = API_IA_URL

# Initialize extensions
db = SQLAlchemy(app)

# Import modules to register models and routes
from . import models  # noqa: E402
from . import routes  # noqa: E402
