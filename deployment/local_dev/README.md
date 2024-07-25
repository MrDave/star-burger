# Running with Compose on local machine

## Setting up

### Environmental variables

Create `.env` file with env variables in the same folder as `compose.yaml` file (and where this `README.md` is). Fill it with neccessary data:

#### Django settings
- `SECRET_KEY` - [A key to provide cryptographic signing, and should be set to a unique, unpredictable value.](https://docs.djangoproject.com/en/4.2/ref/settings/#secret-key)
- `YANDEX_API_KEY` - API key to use Yandex services used in location handling
- `DEBUG` - Debug mode, "False" by default
- `DB_URL` - Database settings (e.g. host, username, etc) in [URL format](https://github.com/jazzband/dj-database-url#url-schema), for PostgreSQL: `postgres://USER:PASSWORD@HOST:PORT/NAME`
- `ALLOWED_HOSTS` - A list of strings representing the host/domain names that this Django site can serve. [See Django docs.](https://docs.djangoproject.com/en/4.2/ref/settings/#allowed-hosts)
- `CSRF_TRUSTED_ORIGINS` - Set to `http://localhost:8000` to ensure that you''l be able to make POST requests (e.g. use Django Admin page)

#### PostgreSQL settings
- `POSTGRES_DB` - Database name
- `POSTGRES_USER` - DB user with admin privileges.
- `POSTGRES_PASSWORD` - Password for the user

#### (Optional) Rollbar settings
If provided, these will be used to connect to Rollbar and send error and deployment logs.
- `ROLLBAR_TOKEN` - Rollbar access token
- `ENVIRONMENT` - Name of environment, e.g. "local-ubuntu"

### NGINX configs

Create `star-burger.conf` file which will serve as NGINX config file:
```nginx
server {
    server_name localhost 127.0.0.1;
    location /bundles/ {
        alias /opt/star-burger/bundles/; # path to where "bundles" volume is mounted
    }
    location /media/ {
        alias /opt/star-burger/media/; # path to where "media" volume is mounted
    }
    location /static/ {
        alias /opt/star-burger/staticfiles/; # path to where "static" volume is mounted
    }
    location / {
	proxy_pass http://backend:8080/;
    }
}
```

## Running project

Note: all commands including `docker compose` must be run from the directory with `compose.yaml` file.

After setting the project up, run `docker compose up`. This will launch database, build frontend files, collect static and launch gunicorn and NGINX.

The website can now be accessed at http://localhost:8000/ and admin panel at http://localhost:8000/admin/

### First launch
When launching project for the first time, you need to migrate database and create new superuser (See below).

### Using django-admin and manage.py

To use built-in Django commands such as `migrate` or `createsuperuser`, run a new container from `backend` service using `docker compose run`:

```sh
docker compose run --rm --entrypoint=/bin/bash backend
```

Then, once inside the container, run the desired commands:

```sh
python manage.py migrate
python manage.py createsuperuser
```

