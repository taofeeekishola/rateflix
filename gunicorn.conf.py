## gunicorn settings for production (Railway). Not used when running starter.py locally.
import os
import subprocess
import sys

## Railway tells the app which port to listen on through $PORT
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = int(os.environ.get('WEB_CONCURRENCY', '2'))

## trailer uploads can be large, so allow more than the default 30 seconds per request
timeout = 120

## log requests and errors to the deploy logs
accesslog = '-'
errorlog = '-'


def on_starting(server):
    ## create any database tables that don't exist yet, once, before the workers start
    subprocess.run([sys.executable, '-m', 'flask', '--app', 'rateflix', 'init-db'], check=True)

    ## with SEED_DEMO_DATA=1 set, add the demo movies too. A failure here is logged but
    ## doesn't stop the site from starting.
    if os.environ.get('SEED_DEMO_DATA', '').strip().lower() in ('1', 'true', 'yes'):
        result = subprocess.run([sys.executable, '-m', 'flask', '--app', 'rateflix', 'seed-db'])
        if result.returncode != 0:
            print('Seeding demo data failed; see the error above.', flush=True)
