from flask import Flask
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from rateflix.models import db

csrf= CSRFProtect()
def create_app():
    app = Flask(__name__,instance_relative_config=True)
    app.config.from_pyfile('config.py',silent=True)

    db.init_app(app)
    migrate = Migrate(app,db)
    csrf.init_app(app)

    return app

app = create_app()

from rateflix import models,user_route,admin_route,forms
