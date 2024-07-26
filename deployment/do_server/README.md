# Running with Compose on a server

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


#### (Optional) Rollbar settings
If provided, these will be used to connect to Rollbar and send error and deployment logs.
- `ROLLBAR_TOKEN` - Rollbar access token
- `ENVIRONMENT` - Name of environment, e.g. "local-ubuntu"

### NGINX configs

Edit `star-burger.conf` (NGINX config file) if needed to point to correct places for media and static files:
```nginx
server {
    location /media/ {
        alias /opt/star-burger/media/;
    }
    location /static/ {
        alias /opt/star-burger/staticfiles/;
    }
    location / {
    include '/etc/nginx/proxy_params';
    proxy_pass http://127.0.0.1:8080/;
    }

    # ...
    # Certbot settings
    # ...
}
```
Also be sure to have your own [certbot](https://certbot.eff.org/) settings.

## Running project

Note: all commands including `docker compose` must be run from the directory with `compose.yaml` file.

After setting the project up, run `docker compose up`. This will build frontend files, collect static and launch Django backend via gunicorn. Use [deployment script](#deployment-script) for the first launch.

The website can now be accessed as per your usual server ip / domain settings.

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

### Deployment script

The deployment script `deploy_docker.sh` can be used after setting up, but should be configured - or at the very least checked for validity of commands - for every deployment environment, specifically regarding volume system and bind paths as well as config files' names.

```sh
#!/bin/bash

docker compose up -d
mkdir -p /opt/star-burger/media/
mkdir -p /opt/star-burger/staticfiles/
mount --bind /var/lib/docker/volumes/do_server_static/_data/ /opt/star-burger/staticfiles/
mount --bind /var/lib/docker/volumes/do_server_media/_data/ /opt/star-burger/media/
cp star-burger.conf /etc/nginx/sites-available
ln -sf /etc/nginx/sites-available/star-burger.conf /etc/nginx/sites-enabled
nginx -s reload
```
