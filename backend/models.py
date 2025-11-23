import datetime
from . import db


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now)
    ip = db.Column(db.String(45))
    userid = db.Column(db.String(255))
    status = db.Column(db.String(10))
    country = db.Column(db.String(50))
    device = db.Column(db.String(50))
    browser = db.Column(db.String(50), default="Unknown")
    # risk_label codes: 'usur' (usurpation), 'brut' (brute force), 'benin' (benign), 'sql' (sql injection)
    risk_label = db.Column(db.String(50), default='benin')
