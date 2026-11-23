import os
from datetime import date

from flask import Flask, abort, render_template, send_from_directory, session
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix
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

    ## Railway sits in front of the app and handles https. This makes Flask use the
    ## original https address in redirects instead of http (browsers block http on an https page).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    ## local development: settings come from instance/config.py (not in git)
    app.config.from_pyfile('config.py',silent=True)

    ## production (Railway): environment variables take priority over config.py
    if os.environ.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
    database_url = os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL')
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = _database_url(database_url)

    ## stop with a clear message instead of a confusing error further down
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        if 'DATABASE_URL' in os.environ:
            raise RuntimeError(
                'DATABASE_URL is set but empty: its reference did not resolve. '
                'Check that the MySQL service exists and that the name in ${{MySQL.MYSQL_URL}} '
                'matches the MySQL service name exactly (it is case-sensitive).')
        raise RuntimeError(
            'No database configured: DATABASE_URL is not set. On Railway, add '
            'DATABASE_URL=${{MySQL.MYSQL_URL}} to the rateflix service Variables and click Deploy. '
            'Locally, set SQLALCHEMY_DATABASE_URI in instance/config.py.')
    if not app.config.get('SECRET_KEY'):
        raise RuntimeError(
            'SECRET_KEY is not set. On Railway, add a SECRET_KEY variable to the rateflix service '
            '(any long random string) and click Deploy. Locally, set it in instance/config.py.')

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

    ## values every template can use: the signed-in member (or None) and the current year
    @app.context_processor
    def template_globals():
        from rateflix.models import Member
        member_id = session.get('member_id')
        member = db.session.get(Member, member_id) if member_id is not None else None
        return {'current_member': member, 'current_year': date.today().year}

    ## friendly pages instead of the plain browser error pages
    @app.errorhandler(CSRFError)
    def form_expired(error):
        return render_template('error.html', title='This form has expired',
                               message='The page was open too long or your session changed, so the form could not be verified. '
                                       'Go back, refresh the page and try again.',
                               detail=error.description), 400

    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', title='Page not found',
                               message='The page you were looking for does not exist or was removed.'), 404

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

    ## `flask --app rateflix seed-db` adds the demo movies in rateflix/seed.py (only adds, never deletes)
    @app.cli.command('seed-db')
    def seed_db():
        from rateflix.seed import seed_demo_data
        added = seed_demo_data()
        print(f'Demo data: added {added} movies.')

    return app

app = create_app()


def upload_path(subfolder, filename):
    ## full path to save an uploaded file to, e.g. upload_path('poster', 'abc.jpg')
    return os.path.join(app.config['UPLOAD_FOLDER'], subfolder, filename)


from rateflix import models,user_route,admin_route,forms
