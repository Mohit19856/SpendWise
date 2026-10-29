# SpendWise — Amazon AWS Deployment Guide (EC2)

> **Read this box before doing anything.**
>
> 1. This guide **documents** a deployment. It does **not** create any AWS resource for
>    you, and nothing in this repository runs automatically against AWS.
> 2. **Before any step that can cost money, stop and confirm.** Every such step in this
>    guide is marked with **⚠️ PAID / BILLABLE** and explains *what it is*, *why it is
>    needed* and *what it can cost*. Do not proceed until you have read it and approved it.
> 3. **Never** paste an AWS **Secret Access Key** or any password into a chat, source file,
>    screenshot or document. Access keys belong only on your own machine, in
>    `~/.aws/credentials` or in the environment of the server.
> 4. Everything here uses tools that already exist in Windows PowerShell and in the AWS
>    Console. You do **not** need to install Ubuntu on your Windows laptop.

---

## 0. What you will end up with

```
User's browser
      │  http://<EC2 public IPv4>          (or https://your-domain)
      ▼
AWS Security Group          22 = your IP only, 80/443 = everyone
      ▼
EC2 Linux instance          Amazon Linux 2023 or Ubuntu (your existing server)
      ▼
Nginx  (port 80/443)        serves static files, proxies everything else
      ▼
Gunicorn (127.0.0.1:8000)   production WSGI server, 3 workers
      ▼
Flask app  "run:app"        FLASK_CONFIG=production
      ▼
SQLite file on disk         instance/spendwise.db  (needs backups!)
```

---

## 1. Check the AWS account and region

1. Sign in to the **AWS Management Console**: <https://console.aws.amazon.com/>
2. Top-right corner → make sure you are in the correct **account** (not a colleague's).
3. Top-right also shows the **Region** (for example `ap-south-1` = Mumbai, or
   `us-east-1` = N. Virginia).

**Write down your region:** `________________`

> **Tip:** Choose the region closest to you. For India, `ap-south-1` (Mumbai) usually gives
> the lowest latency. Prices are the same for most regions but **not all** — always check
> the price page for *your* region.

**Optional — if the AWS CLI is already installed and configured** on your laptop:

```powershell
aws --version
aws sts get-caller-identity
```

`aws sts get-caller-identity` prints **who** you are (Account, UserId, Arn) and therefore
is the safe way to prove your credentials work. It does **not** print your secret key.
Expected output looks like:

```json
{
    "UserId": "AIDAIEXAMPLEEXAMPLE",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-name"
}
```

If the command says `Unable to locate credentials`, configure it **on your own machine**:

```powershell
aws configure
# AWS Access Key ID     : (paste, it is hidden from the report)
# AWS Secret Access Key : (paste, never share this)
# Default region name   : ap-south-1
# Default output format : json
```

> If the AWS CLI is not available, do everything from the **AWS Console** — the steps
> below are written so that the Console is always enough.

---

## 2. Review the EC2 instances you already have (reuse if practical)

**Console → EC2 → Instances.**

For every instance note down:

| What | Where to find it | Why it matters |
| --- | --- | --- |
| Instance ID | `i-0123456789abcdef0` | You will need it later |
| State | running / stopped | Stopped instances still charge for disk! |
| Instance type | `t2.micro`, `t3.micro`, `t3.small` … | Decides the price |
| Platform | Amazon Linux, Ubuntu, Windows | **Windows cannot run our stack the same way** — prefer Linux |
| Public IPv4 | e.g. `13.234.56.78` | Needed for the app URL |
| Security groups | `sg-...` | Firewall rules |
| Storage | EBS volume size (e.g. 8 GiB gp3) | Billed separately |
| Key pair | `*.pem` on your laptop | Needed for SSH |

**Decision table**

| You found… | What to do |
| --- | --- |
| A running **Linux** instance you can use | ✅ Reuse it. Go to section 4. No new cost. |
| A **stopped** Linux instance | ✅ You may start it, but note: stopped instances still charge for **EBS storage** and an attached public IPv4 may not stay the same. Go to section 4. |
| Only a **Windows** instance | ⚠️ Not suitable for this stack. Prefer creating a small Linux instance (section 3) — but confirm the cost first. |
| No instance at all | You need one. Read section 3 **fully** (including the ⚠️ cost warning) and approve it before creating anything. |

> **Important:** an instance you already created may be *outside* the AWS Free Tier. Log
> in to **Billing → Free Tier** to check your current usage and remaining limits.

---

## 3. ⚠️ PAID / BILLABLE — understand the costs **before** creating an instance

**Nothing in this section may be done without your explicit confirmation.**

What is it? An **EC2 instance** is a rented virtual Linux server in an AWS data centre.
You rent it by the hour (billed per second, with a 60-second minimum), even if you are not
using it — as long as it is in the `running` state.

What can it cost? (Approximate USD list prices for the **Mumbai / ap-south-1** region,
on-demand, Linux. **Always verify on the AWS pricing page for your own region and date** —
prices change.)

| Component | Typical size | Approximate price | Notes |
| --- | --- | --- | --- |
| EC2 instance | `t3.micro` (2 vCPU, 1 GiB) | ≈ **$0.0104 per hour** → ≈ **$7.6/month** if left running 24×7 | A Free Tier account with under 12 months of age gets **750 hours/month of `t2.micro`/`t3.micro` free**. |
| EBS storage | 8 GiB `gp3` | ≈ **$0.08 per GiB/month** → ≈ **$0.64/month** | Charged **even when the instance is stopped**. Deleting the instance without deleting the volume still bills you. |
| Public IPv4 address | 1 address attached to the instance | ≈ **$0.005 per hour** → ≈ **$3.6/month** | AWS started charging for public IPv4 addresses **including** attached ones. |
| Data transfer out | First 100 GB/month free, then ≈ $0.09/GB | usually ≈ **$0.00** for a college demo | A small project will not come close to 100 GB. |
| Snapshots (backups) | a few GiB | ≈ **$0.05 per GiB/month** | Optional but recommended. |

**Rough total for a 24×7 `t3.micro` in Mumbai outside the Free Tier: about $12 per month
(≈ ₹1,000).** Inside the Free Tier (first 12 months of the account) the instance hours are
free, but the public IPv4 and EBS storage may still cost a small amount.

### Your approval checklist — answer these before creating anything

| Question | Your answer |
| --- | --- |
| Do I understand that a **running** instance is billed every hour? | ☐ yes / ☐ no |
| Do I understand that **EBS storage is billed even when the instance is stopped**? | ☐ yes / ☐ no |
| Do I understand that a **public IPv4 address** has a small hourly charge? | ☐ yes / ☐ no |
| Am I inside the **Free Tier** period, and do I have Free Tier hours left? | ☐ yes / ☐ no / ☐ not sure |
| Which **region** will I use? | `____________` |
| What **monthly cost** am I willing to accept? | `____________` |
| Do I want to create a new instance, or reuse an existing one? | ☐ new / ☐ reuse |

**If the answer to any cost question is "no" or "not sure", stop — set up the budget and
billing alert in section 4 first.**

---

## 4. Free Tier eligibility, budgets and billing alerts (do this FIRST)

1. **Check Free Tier status:** Console → search **"Billing"** → **Free Tier**. Read the
   remaining hours for EC2 and the remaining GB for EBS.
2. **Create a budget with an alert** (free of charge):
   - Console → **Billing and Cost Management** → **Budgets** → **Create budget**
   - Choose **Use a template** → **Monthly cost budget**
   - Budget amount: e.g. **$5** (a small number you are comfortable with)
   - E-mail: your own address
   - Set an **alert at 80% of the budget** and at 100%.
3. **Optional but recommended:** also turn on a **CloudWatch billing alarm** for
   estimated charges, so you get mail even if you forget the budget page.
4. **Verify the region one more time.** Resources are per-region, and a forgotten instance
   in another region still costs money.

**Nothing in this section creates any charge.** Never skip it.

---

## 5. Create the instance (only after you approved section 3)

**Console → EC2 → Instances → Launch instance.**

| Setting | Recommended value | Why |
| --- | --- | --- |
| Name | `spendwise-server` | Easy to find later |
| AMI | **Amazon Linux 2023** (or Ubuntu 24.04 LTS) | Both support Python 3, Gunicorn, Nginx. Do **not** pick Windows. |
| Instance type | `t3.micro` (or `t2.micro` if you are in the Free Tier) | 1 GiB RAM is enough for this project |
| Key pair | **Create new key pair** → RSA → `.pem` → download it | This is your only way to SSH in. Guard the file. |
| Network settings | Allow **SSH from "My IP"**, allow **HTTP** | More restrictive = safer |
| Configure storage | 8 GiB `gp3` | Minimum is enough; the database is tiny |
| Advanced details → User data | leave empty | (Optional: you can paste an install script later) |

After it launches, note down:

```
Instance ID        : i-________________
Public IPv4 address: ____.____.____.____
Region             : ________________
Key pair file      : C:\Users\ASUS\Downloads\spendwise-key.pem
```

> **Never commit the `.pem` file to GitHub.** `.gitignore` in this repository already
> excludes `*.pem` and `*.key`. Keep the file in a safe folder and never send it to anyone.

**If you reuse an existing instance:** skip this section and just write down its public
IPv4, key pair and platform.

---

## 6. Secure access to the EC2 instance (SSH)

### 6a. Fix the permissions of the `.pem` file on Windows

PowerShell (one time):

```powershell
$key = "$env:USERPROFILE\Downloads\spendwise-key.pem"

icacls $key /inheritance:r
icacls $key /grant:r "$($env:USERNAME):(R)"

icacls $key
```

Expected: only your user name appears with `(R)`.

### 6b. Connect

```powershell
ssh -i "$env:USERPROFILE\Downloads\spendwise-key.pem" ec2-user@<EC2-PUBLIC-IP>
# Ubuntu AMI uses "ubuntu" instead of "ec2-user":
# ssh -i "..." ubuntu@<EC2-PUBLIC-IP>
```

The first time you will be asked `Are you sure you want to continue connecting?` → type
`yes`.

**Expected result:**

```
   ,     #_
   ~\_  ####_        Amazon Linux 2023
  ...
[ec2-user@ip-172-31-xx-xx ~]$
```

### 6c. Create a normal user (good practice, optional)

```bash
sudo useradd -m spendwise
sudo passwd spendwise
sudo usermod -aG wheel spendwise      # 'sudo' group on Ubuntu
su - spendwise
```

### 6d. Restrict SSH to your IP only

**Console → EC2 → Security Groups → your group → Inbound rules → Edit.**

| Type | Port | Source | Meaning |
| --- | --- | --- | --- |
| SSH | 22 | **My IP** (`x.x.x.x/32`) | Only your home/college internet can connect |
| HTTP | 80 | `0.0.0.0/0` | Public website |
| HTTPS | 443 | `0.0.0.0/0` | Only once you have TLS (section 15) |

> **Never** use `0.0.0.0/0` for port **22**. That exposes SSH to every scanner on the
> internet. If your IP changes, update the rule. Do not open ports 5000 or 8000 — the app
> does not need them publicly.

---

## 7. Install the dependencies on the server

Connect by SSH (section 6), then run the block for your platform.

### Amazon Linux 2023

```bash
sudo dnf update -y
sudo dnf install -y python3 python3-pip python3-devel git nginx sqlite
python3 --version
```

### Ubuntu 24.04

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx sqlite3
python3 --version
```

**Expected result:** `Python 3.9.x` (Amazon Linux 2023) or `Python 3.12.x` (Ubuntu).
Anything 3.9+ is fine for this project.

---

## 8. Upload or clone the application

### Option A — clone from GitHub (recommended, and it is your DevOps evidence)

```bash
cd ~
git clone https://github.com/<your-username>/spendwise.git
cd spendwise
```

A private repository needs a token. **Do not paste a personal access token into chat.**
Create it in GitHub → Settings → Developer settings → Personal access tokens, and use it
only on the server (Git will ask for it as the "password").

### Option B — upload from Windows with `scp`

```powershell
# create a zip on Windows first (exclude .venv and instance)
Compress-Archive -Path app, tests, scripts, docs, .github, config.py, run.py, `
  requirements.txt, requirements-prod.txt, pytest.ini, .env.example, README.md, `
  ARCHITECTURE.md -DestinationPath spendwise.zip -Force

scp -i "$env:USERPROFILE\Downloads\spendwise-key.pem" `
  .\spendwise.zip ec2-user@<EC2-PUBLIC-IP>:~/
```

Then on the server:

```bash
sudo dnf install -y unzip     # or: sudo apt install -y unzip
unzip -o ~/spendwise.zip -d ~/spendwise
cd ~/spendwise
```

> Never upload `.env`, `.venv`, `instance/spendwise.db` or `.pem` files from your laptop.

---

## 9. Create the virtual environment and install the packages

```bash
cd ~/spendwise

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements-prod.txt
```

**Expected result:** the last line says something like
`Successfully installed ... gunicorn-23.0.0 ...`

> `requirements-prod.txt` = `requirements.txt` **plus** Gunicorn. Gunicorn does not run on
> Windows, which is why it is kept in a separate file.

---

## 10. Configure the production environment variables

Generate a **new** secret key on the server (never reuse the one from your laptop):

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Create the file **outside the Git repository** so it can never be committed:

```bash
sudo mkdir -p /etc/spendwise
sudo tee /etc/spendwise/spendwise.env > /dev/null <<'EOF'
FLASK_CONFIG=production
SECRET_KEY=PASTE_YOUR_GENERATED_SECRET_KEY_HERE
DATABASE_URL=sqlite:////home/ec2-user/spendwise/instance/spendwise.db
PORT=8000
EOF

sudo chmod 600 /etc/spendwise/spendwise.env
sudo chown root:root /etc/spendwise/spendwise.env
sudo cat /etc/spendwise/spendwise.env     # verify (do not share this output)
```

Notes

- The `DATABASE_URL` has **four** slashes before the absolute path
  (`sqlite:////home/...`) — that is the correct SQLAlchemy form for an absolute path.
- Adjust the path if your user is `spendwise` or if you use Ubuntu (`/home/ubuntu/...`).
- In production the app **refuses to start** if `SECRET_KEY` is missing or still the
  placeholder value, and `DEBUG` stays off. Both are intentional safety features.
- Real environment variables win over the `.env` file, so you may also delete the local
  `.env` on the server to avoid confusion.

---

## 11. Prepare the database

```bash
cd ~/spendwise
source .venv/bin/activate

mkdir -p instance
export FLASK_CONFIG=production
export SECRET_KEY="paste-the-same-secret-here"

flask --app run.py init-db
```

**Expected result:** `Database tables created.`

Create your real account with the CLI command (no demo data on a public server):

```bash
flask --app run.py create-user
# Name: Your Name
# Email: you@example.com
# Password: (8+ characters, hidden while typing)
# Repeat for confirmation
```

**Expected result:** `Created user you@example.com (id=1)`

> Do **not** run `scripts/seed_data.py` on a public server — the demo password
> `Demo@12345` is public knowledge.
>
> The `instance/` folder is owned by the user that runs the app. If you created it with
> `sudo`, fix it: `sudo chown -R ec2-user:ec2-user ~/spendwise`.

---

## 12. Persistent database storage and backups

**Where does the data live?**
`/home/ec2-user/spendwise/instance/spendwise.db` — a single SQLite file on the EC2 **EBS**
volume. It survives a reboot, a `systemctl restart` and an application update. It does
**not** survive the instance being **terminated**.

**Backup script** — create it once:

```bash
sudo tee /usr/local/bin/spendwise-backup.sh > /dev/null <<'EOF'
#!/bin/bash
# Safe online backup of the SQLite database using the .backup command.
set -euo pipefail

APP_DIR=/home/ec2-user/spendwise
BACKUP_DIR=/home/ec2-user/spendwise-backups
STAMP=$(date +%Y-%m-%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
sqlite3 "$APP_DIR/instance/spendwise.db" ".backup '$BACKUP_DIR/spendwise-$STAMP.db'"

# keep only the 14 newest backups
ls -1t "$BACKUP_DIR"/spendwise-*.db | tail -n +15 | xargs -r rm --

echo "Backup written: $BACKUP_DIR/spendwise-$STAMP.db"
EOF

sudo chmod 755 /usr/local/bin/spendwise-backup.sh
sudo /usr/local/bin/spendwise-backup.sh
```

**Schedule it daily at 02:00** (crontab is free):

```bash
crontab -e
# add this line:
0 2 * * * /usr/local/bin/spendwise-backup.sh >> /home/ec2-user/spendwise-backups/cron.log 2>&1
```

**Optional off-server copy** (survives the loss of the whole instance):

```bash
aws s3 cp /home/ec2-user/spendwise-backups/ s3://<your-bucket>/spendwise/ --recursive
```

> ⚠️ An S3 bucket is a separate AWS resource and may be **billable** (storage + requests).
> A few megabytes are effectively free, but confirm the cost and your approval before
> creating a bucket, exactly like section 3.

**Restore from a backup:**

```bash
sudo systemctl stop spendwise
cp /home/ec2-user/spendwise-backups/spendwise-2026-10-29_020000.db \
   /home/ec2-user/spendwise/instance/spendwise.db
sudo systemctl start spendwise
sudo systemctl status spendwise --no-pager
```

> **Honest limitation:** SQLite is a single-file database. It is perfectly adequate for a
> college demonstration, but it is **not** a high-availability database, and it does not
> like many concurrent writers. For a real product you would move to **Amazon RDS**
> (managed MySQL/PostgreSQL), which adds its own cost.

---

## 13. Test Gunicorn manually

```bash
cd ~/spendwise
source .venv/bin/activate

export FLASK_CONFIG=production
export SECRET_KEY="paste-the-same-secret-here"

gunicorn --bind 127.0.0.1:8000 --workers 3 --access-logfile - "run:app"
```

**Expected result:**

```
[INFO] Starting gunicorn 23.0.0
[INFO] Listening at: http://127.0.0.1:8000
[INFO] Booting worker with pid: ...
```

From a **second** SSH session, verify it locally:

```bash
curl -I http://127.0.0.1:8000/
```

**Expected result:** `HTTP/1.1 200 OK`

Stop it with `Ctrl + C`. Binding to `127.0.0.1` means the port is **not** reachable from
the internet — that is exactly what we want; Nginx will be the public door.

---

## 14. systemd service (auto-start + auto-restart)

```bash
sudo tee /etc/systemd/system/spendwise.service > /dev/null <<'EOF'
[Unit]
Description=SpendWise Flask application (Gunicorn)
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/spendwise
EnvironmentFile=/etc/spendwise/spendwise.env
ExecStart=/home/ec2-user/spendwise/.venv/bin/gunicorn \
          --workers 3 \
          --bind 127.0.0.1:8000 \
          --access-logfile - \
          --error-logfile - \
          run:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

Enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable spendwise
sudo systemctl start spendwise
sudo systemctl status spendwise --no-pager
```

**Expected result:** `Active: active (running)`.

Useful commands:

| Task | Command |
| --- | --- |
| Status | `sudo systemctl status spendwise --no-pager` |
| Start / stop / restart | `sudo systemctl start\|stop\|restart spendwise` |
| Live logs | `sudo journalctl -u spendwise -f` |
| Last 50 lines | `sudo journalctl -u spendwise -n 50 --no-pager` |

---

## 15. Nginx reverse proxy (and optional HTTPS)

```bash
sudo tee /etc/nginx/conf.d/spendwise.conf > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 5M;

    location /static/ {
        alias /home/ec2-user/spendwise/app/static/;
        expires 7d;
        access_log off;
    }

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
EOF

sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
```

**Expected result of `nginx -t`:**

```
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

`X-Forwarded-Proto` matters: in production the app uses `Secure` session cookies, so it
must know that the browser is really talking HTTPS when a TLS certificate is in place.

### Optional — HTTPS with Let's Encrypt (only if you have a domain)

You need a domain name whose **A record** points to your EC2 public IPv4.

```bash
sudo dnf install -y certbot python3-certbot-nginx    # Ubuntu: sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d spendwise.example.com
sudo systemctl status certbot-renew.timer --no-pager   # auto-renewal
```

With HTTPS in place, also add port **443** to the security group and keep port 80 for the
redirect that Certbot creates.

> No domain? Skip HTTPS for now and use `http://<EC2-PUBLIC-IP>`. Just remember that a
> plain-HTTP demo should not be used with real personal financial data.

---

## 16. Test the public application URL

From your Windows laptop browser:

```
http://<EC2-PUBLIC-IP>/
```

**Checklist**

- ☐ Landing page loads with the SpendWise branding and CSS
- ☐ You can register a new account
- ☐ You can log in and see the dashboard cards
- ☐ Adding an income and an expense works and the message appears
- ☐ Charts render (Chart.js is loaded from the CDN — the server needs outbound HTTPS)
- ☐ Filters and search work
- ☐ Edit and delete work
- ☐ Logout works and `/dashboard` redirects back to the login page
- ☐ `http://<EC2-PUBLIC-IP>/static/css/style.css` returns CSS (so Nginx is serving static
  files)

If something fails, go to section 17.

---

## 17. Logs and troubleshooting

| Symptom | Where to look | Likely fix |
| --- | --- | --- |
| `502 Bad Gateway` from Nginx | `sudo journalctl -u spendwise -n 60 --no-pager` | Gunicorn is not running or crashed. Check `EnvironmentFile`, the secret key and the database path. |
| `502` and the log says `ModuleNotFoundError` | same | You forgot `source .venv/bin/activate` when installing, or installed for the wrong user. Install as the same user that runs the service. |
| `RuntimeError: SECRET_KEY is not configured` | same | `SECRET_KEY` is missing/placeholder in `/etc/spendwise/spendwise.env`. |
| `Permission denied: .../instance/spendwise.db` | same | `sudo chown -R ec2-user:ec2-user ~/spendwise` |
| Page loads but there is **no CSS** | browser Network tab | Nginx `location /static/` alias path is wrong, or you are using the wrong `alias` (it must end with `/`). |
| 500 error page | `sudo journalctl -u spendwise -n 80 --no-pager` | Read the traceback printed by the app. The custom 500 page hides it from users by design. |
| Site not reachable at all | Security group inbound rules | Port 80 open to `0.0.0.0/0`? Is Nginx running (`systemctl status nginx`)? |
| Cannot SSH | Security group | Your IP changed — update the SSH rule to "My IP". |
| Slow first load | `t3.micro` has 2 CPU credits baseline | Normal for burstable instances; not a bug. |

Handy one-liners:

```bash
sudo tail -n 50 /var/log/nginx/error.log
sudo tail -n 50 /var/log/nginx/access.log
sudo journalctl -u spendwise --since "10 min ago" --no-pager
sudo -u ec2-user /home/ec2-user/spendwise/.venv/bin/python -c "import flask; print(flask.__version__)"
```

---

## 18. Updating the application

```bash
cd ~/spendwise
sudo systemctl stop spendwise

# keep a safety copy of the database first
/usr/local/bin/spendwise-backup.sh

git pull origin main          # or upload the new files with scp
source .venv/bin/activate
pip install -r requirements-prod.txt

# only if the schema changed — this command is safe to run again
export FLASK_CONFIG=production
export SECRET_KEY="paste-the-same-secret-here"
flask --app run.py init-db

sudo systemctl start spendwise
sudo systemctl status spendwise --no-pager
sudo journalctl -u spendwise -n 30 --no-pager
```

Rollback: `git checkout <previous-commit>` and restart the service.

---

## 19. Stop or terminate resources you no longer need (cost control)

| Action | What happens | Cost |
| --- | --- | --- |
| **Stop instance** | Instance shuts down; EBS and (usually) the public IPv4 are kept | EBS + IPv4 still billed. A stopped instance can be started again. |
| **Terminate instance** | Instance is destroyed permanently | Billing for the instance stops. **EBS volumes are deleted too unless `Delete on termination` is off** — your database is gone. Take a backup first! |
| **Release the Elastic IP / public IPv4** | Frees the address | Stops the hourly IPv4 charge |
| **Delete unused EBS volumes and snapshots** | Frees storage | Console → EC2 → Volumes / Snapshots → Delete |
| **Delete the security group / key pair** | Nothing changes at runtime | Free |

Terminate safely:

```bash
# 1. make a final backup and copy it somewhere safe
/usr/local/bin/spendwise-backup.sh
ls -lh /home/ec2-user/spendwise-backups/
```

Then Console → EC2 → Instances → select → **Instance state → Terminate instance**.

**Console verification that nothing is left:**

- EC2 → Instances: no instance in `running` state that you forgot
- EC2 → Volumes: no unattached volume (`available`)
- EC2 → Elastic IPs: no address that is not attached
- Billing → **Cost Explorer**: check the daily cost for the last 7 days

> **Free Tier reminder:** when the 12-month Free Tier period ends (or if you exceed the
> free hours/GB), the same resources start being billed normally. Re-check
> Billing → Free Tier every few months.

---

## 20. What was actually verified, and what is not

Be honest in your report and viva:

| Item | Status |
| --- | --- |
| Application built and tested locally on Windows | ✅ done (see [project_report.md](project_report.md) for the real pytest results) |
| Local SQLite database initialised and demo data seeded | ✅ done locally |
| CI workflow file written and committed | ✅ done (see `.github/workflows/tests.yml`) — first real run happens after you push to GitHub |
| AWS resources created | ❌ **none** — by design. Nothing was created, and no cost has been incurred. |
| Application deployed on EC2 and reachable from the internet | ❌ **not yet** — this guide is the plan; the deployment happens on *your* account, with *your* approval. |
| Screenshots of the running AWS site | ❌ still to be captured by you after deployment |

Do **not** write "deployed successfully on AWS" in your report until you have actually
followed sections 5–16 and opened the public URL in your browser.
