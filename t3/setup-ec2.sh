#!/usr/bin/env bash
set -euo pipefail

# Assumes dedicated Ubuntu EC2 instance with Apache (the existing T2 server).
APP_USER="$(id -un)"
APP_DIR="$HOME/csci4830-t3"
SERVICE_NAME="csci4830-mt-lite"

if [[ ! -f "$APP_DIR/app.py" || ! -f "$APP_DIR/requirements.txt" ]]; then
  echo "Missing app.py or requirements.txt in $APP_DIR" >&2
  exit 1
fi

echo "[1/6] Installing Python and Apache packages"
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv apache2

echo "[2/6] Preparing Python environment"
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/python" -m pip install -q -r "$APP_DIR/requirements.txt"
mkdir -p "$APP_DIR/data"

echo "[3/6] Creating service"
sudo tee "/etc/systemd/system/$SERVICE_NAME.service" >/dev/null <<EOF
[Unit]
Description=CSCI 4830 Flask SQLite Motorcycle Maintenance Lite
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 app:app
Restart=on-failure
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME" >/dev/null
sudo systemctl restart "$SERVICE_NAME"

echo "[4/6] Backing up old T2 Apache site and enabling proxy"
APACHE_SITE="/etc/apache2/sites-available/000-default.conf"
if [[ -f "$APACHE_SITE" ]]; then
  sudo cp "$APACHE_SITE" "$APACHE_SITE.backup-$(date +%Y%m%d-%H%M%S)"
fi
sudo a2enmod proxy proxy_http >/dev/null
sudo tee "$APACHE_SITE" >/dev/null <<'EOF'
<VirtualHost *:80>
    ServerName localhost
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
    ErrorLog ${APACHE_LOG_DIR}/csci4830-error.log
    CustomLog ${APACHE_LOG_DIR}/csci4830-access.log combined
</VirtualHost>
EOF
sudo a2ensite 000-default >/dev/null
sudo apache2ctl configtest
sudo systemctl reload apache2

echo "[5/6] Checking Flask and SQLite"
for _ in 1 2 3 4 5; do
  if curl -fsS http://127.0.0.1:8000/health; then
    echo
    break
  fi
  sleep 1
done

echo "[6/6] Checking Apache on port 80"
curl --fail --silent --show-error http://127.0.0.1/health
echo
echo "Deployment completed. Use http://YOUR_EC2_PUBLIC_IP/"
echo "If outside access fails, check EC2 security group inbound HTTP (TCP 80)."
