#! /usr/bin/bash

set -Eeuo pipefail

cd /opt/star-burger/

git_result=$(git pull)
if [[ "$git_result" == "Already up to date." ]]
then
	echo $git_result
	exit 0
fi

source venv/bin/activate

pip install -r requirements.txt

/bin/dd if=/dev/zero of=/var/swap.1 bs=1M count=1024
/sbin/mkswap /var/swap.1
/sbin/swapon /var/swap.1

npm ci --force

python manage.py migrate

python manage.py collectstatic --noinput

./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

systemctl restart star-burger.service
systemctl reload nginx.service

/sbin/swapoff /var/swap.1

source .env
GIT_HASH=$(git rev-parse HEAD)
export ROLLBAR_HEADER="X-Rollbar-Access-Token: $ROLLBAR_TOKEN"
export USERNAME=MrDave
curl --request POST \
     --url https://api.rollbar.com/api/1/deploy \
     --header "$ROLLBAR_HEADER" \
     --header 'accept: application/json' \
     --header 'content-type: application/json' \
     --data "
{
  \"environment\": \"$ENVIRONMENT\",
  \"revision\": \"$GIT_HASH\",
  \"rollbar_username\": \"$USERNAME\"
}"
echo Finished!