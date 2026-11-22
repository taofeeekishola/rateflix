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
