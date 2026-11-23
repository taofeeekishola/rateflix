# Deploying RateFlix to Railway

This branch (`railway-deploy`) is set up to run on Railway with a MySQL database and a volume for uploads.

## What's in this branch

- Settings come from environment variables on Railway (`SECRET_KEY`, `DATABASE_URL`, `UPLOAD_FOLDER`). Locally, `instance/config.py` still works as before.
- The app runs on gunicorn (`railpack.json`, `gunicorn.conf.py`), and Python is pinned to 3.12 (`.python-version`).
- On every start, missing database tables are created automatically. You can also run `flask --app rateflix init-db` yourself.
- New uploads are saved to `UPLOAD_FOLDER` (a Railway volume), so they survive redeploys. The posters and trailers already in the repo are still served.
- The MySQL driver is now `mysql-connector-python`. The old `mysql-connector` package can't log in to MySQL 8+, which Railway uses.
- Admin passwords are checked as hashes. An admin you insert with a plain-text password can log in, and the password is replaced with a hash on that first login.

## 1. Create the services

1. In Railway, create a new project and choose **Deploy from GitHub repo**, then pick `rateflix`.
2. In the app service's **Settings → Source**, set the branch to `railway-deploy`.
3. In the same project, add a **MySQL** database.

## 2. Set the app's variables

In the app service's **Variables** tab, add:

| Variable | Value |
|---|---|
| `DATABASE_URL` | `${{MySQL.MYSQL_URL}}` (use your MySQL service's name if it isn't `MySQL`) |
| `SECRET_KEY` | a long random string, e.g. the output of `python -c "import secrets; print(secrets.token_hex(32))"` |
| `UPLOAD_FOLDER` | `/data/uploads` |

## 3. Add a volume for uploads

Create a volume, attach it to the app service, and set its mount path to `/data`.

## 4. Get a public URL

In the app service's **Settings → Networking**, generate a domain. When the deploy finishes, the logs should show `Database tables are ready.` and gunicorn listening on the port.

## 5. Bring over your data (optional)

To copy your local database, including movies, users and the admin, export it locally:

```bash
mysqldump -u root -p YOUR_LOCAL_DB_NAME > rateflix.sql
```

Then import it using the MySQL service's `MYSQL_PUBLIC_URL` (in its **Variables** tab) for the host, port, user and password:

```bash
mysql -h PUBLIC_HOST -P PUBLIC_PORT -u root -p railway < rateflix.sql
```

The dump replaces the empty tables created on the first start. The posters and trailers those movies point to are already in the repo, so they show up once the import is done.

## Demo movies (optional)

`rateflix/seed.py` holds 19 real movies, with genres, producers, studios and cast, that use the posters and trailers already in the repo. To add them on Railway, set `SEED_DEMO_DATA=1` on the app service and deploy. Remove the variable once the movies appear. Locally, run `flask --app rateflix seed-db`.

It only adds data: movies whose titles already exist are skipped, and genres, producers, studios and actors with the same name are reused, so running it again is safe.

## 6. Add an admin manually

Connect to the database in either of these ways:

- the MySQL service's **Data** tab
- MySQL Workbench or the `mysql` CLI, using `MYSQL_PUBLIC_URL`

Then insert a row:

```sql
INSERT INTO admin (admin_firstname, admin_lastname, admin_username, admin_email, admin_password)
VALUES ('First', 'Last', 'admin', 'you@example.com', 'your-password');
```

The plain-text password is hashed the first time that admin logs in. If you'd rather never store it in plain text, insert a hash instead:

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password'))"
```

## Local development after pulling this branch

Remove the old driver before installing, because both packages use the same `mysql.connector` module name:

```bash
pip uninstall -y mysql-connector
pip install -r requirements.txt
python starter.py
```

Your `instance/config.py` keeps working unchanged.
