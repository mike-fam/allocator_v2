set -ex

SSH_CONFIG="Host *.eait.uq.edu.au
  StrictHostKeyChecking no
Host *.zones.eait.uq.edu.au
  ProxyJump $UQ_USERNAME@$UQ_NETWORK_HOST
  ForwardAgent yes
"


pullAndDeploy() {
	cd /var/www/uwsgi/tutor-allocate
  git reset HEAD --hard
  git checkout development
  git pull
  /var/www/uwsgi/tutor-allocate/venv/bin/pip install -r requirements.txt
  /var/www/uwsgi/tutor-allocate/venv/bin/python allocator_2/manage.py migrate
	echo "$UQ_PW" | sudo -S systemctl restart uwsgi-allocator
	history -c
}

echo "$SSH_CONFIG" >>~/.ssh/config
eval "$(ssh-agent -s)"
ssh-add /opt/atlassian/pipelines/agent/ssh/id_rsa

# shellcheck disable=SC2029
ssh "$UQ_USERNAME@$PRODUCTION_ZONE" "
	set -ex
	$(declare -f pullAndDeploy)
	$(declare -p UQ_PW ENV_FILE)
	pullAndDeploy
"