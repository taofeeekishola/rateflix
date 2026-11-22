import os

from flask import Flask, abort, send_from_directory
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from werkzeug.security import safe_join

from rateflix.models import db

csrf= CSRFProtect()

## folders inside the upload folder that the app saves files into
UPLOAD_SUBFOLDERS = ('poster', 'trailers', 'actors', 'profile_pic')


def _database_url(url):
    ## Railway gives a url like mysql://user:pass@host:3306/railway
    ## SQLAlchemy needs the driver name in it, so turn it into mysql+mysqlconnector://
    if url.startswith('mysql://'):
        return 'mysql+mysqlconnector://' + url[len('mysql://'):]
    return url


def create_app():
    app = Flask(__name__,instance_relative_config=True)

    ## local development: settings come from instance/config.py (not in git)
    app.config.from_pyfile('config.py',silent=True)

    ## production (Railway): environment variables take priority over config.py
    if os.environ.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
    if os.environ.get('DATABASE_URL'):
        app.config['SQLALCHEMY_DATABASE_URI'] = _database_url(os.environ['DATABASE_URL'])

    ## check connections before using them, and replace them before MySQL closes idle ones
    app.config.setdefault('SQLALCHEMY_ENGINE_OPTIONS', {'pool_pre_ping': True, 'pool_recycle': 280})

    ## uploads: the files that are in the repo live in rateflix/static/uploads.
    ## On Railway, UPLOAD_FOLDER points at a volume so new uploads survive redeploys.
    app.config['BUNDLED_UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['UPLOAD_FOLDER'] = (os.environ.get('UPLOAD_FOLDER')
                                   or app.config.get('UPLOAD_FOLDER')
                                   or app.config['BUNDLED_UPLOAD_FOLDER'])
    for subfolder in UPLOAD_SUBFOLDERS:
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], subfolder), exist_ok=True)

    db.init_app(app)
    migrate = Migrate(app,db)
    csrf.init_app(app)

    ## serves /static/uploads/... from the upload folder first, then from the files in the repo,
    ## so the templates can keep using /static/uploads/... paths
    @app.route('/static/uploads/<path:filename>')
    def uploaded_file(filename):
        for folder in (app.config['UPLOAD_FOLDER'], app.config['BUNDLED_UPLOAD_FOLDER']):
            path = safe_join(folder, filename)
            if path and os.path.isfile(path):
                return send_from_directory(folder, filename)
        abort(404)

    ## `flask --app rateflix init-db` creates any tables that don't exist yet (safe to run again)
    @app.cli.command('init-db')
    def init_db():
        db.create_all()
        print('Database tables are ready.')

    return app

app = create_app()


def upload_path(subfolder, filename):
    ## full path to save an uploaded file to, e.g. upload_path('poster', 'abc.jpg')
    return os.path.join(app.config['UPLOAD_FOLDER'], subfolder, filename)


from rateflix import models,user_route,admin_route,forms
