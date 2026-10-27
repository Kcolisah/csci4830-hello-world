# T3: Motorcycle Maintenance Tracker Lite

Small individual Flask + SQLite web application for CSCI 4830 T3. Displays a maintenance log, allows adding entries, and saves them persistently in SQLite. Intended as a lightweight classroom demo, not the production Motorcycle Maintenance Tracker.

## Technology / requirements

- Web framework: Flask (`app.py`)
- Database: SQLite (`data/maintenance.sqlite3` is generated on first run)
- Cloud: Ubuntu AWS EC2 with Apache reverse proxy and Gunicorn
- Version control: existing `Kcolisah/csci4830-hello-world` GitHub repository, in `/t3`

## Fastest deployment from Windows PowerShell

1. Download/extract the ZIP. Keep the files together in the extracted folder.
2. Confirm your **original AWS EC2 instance** from T2 is **running** and you still have its `.pem` private-key file. If it has a different Public IPv4 address, use the new address.
3. In PowerShell, enter the extracted folder and run:

```powershell
.\deploy.ps1 -KeyPath "C:\path\to\your-t2-key.pem" -ServerIp "3.138.119.161"
```

The script clones the existing T2 repository, commits only the new `t3/` folder and pushes it to GitHub, copies the three required deployment files to EC2 over SSH, installs Flask/Gunicorn/Apache, starts a systemd service, and configures HTTP port 80. It backs up the prior default Apache site config before changing it. It **does replace the old Hello World page at port 80**; the old GitHub files remain intact.

SSH (TCP 22) and HTTP (TCP 80) must be allowed by your EC2 security group. This script assumes the default Ubuntu `ubuntu` SSH account; override using `-SshUser` if needed. It needs `git`, `ssh`, `scp`, your AWS PEM key, and GitHub git-push access on Windows.

> **Caution:** Intended for your dedicated T2 EC2 instance. Do not run the setup script on a server hosting other websites because it replaces Apache's `000-default.conf` site.

## Verify

- Open `http://YOUR_EC2_PUBLIC_IP/` and add a test maintenance entry.
- Refresh to verify the entry persists in the database.
- Open `http://YOUR_EC2_PUBLIC_IP/health`; look for `"status":"ok"` and `"database":"sqlite"`.
- Confirm the `t3/` folder is visible in GitHub.

Canvas submission requires only the website URL and repository URL, but the actual app must run.

## Local development / tests

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest -v test_app.py
.\.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:5000/`.

## Limitations

This is a public classroom demo with no user authentication. Anyone with its public URL can add a test record. Do not enter real private information. Delete the demonstration server after grading if you no longer need it.
