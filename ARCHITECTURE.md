# SpendWise — Architecture

This document explains how SpendWise is put together, using three views:

1. **Application flow** — what happens when a user opens a page
2. **DevOps flow** — how the code travels from your laptop to GitHub and gets tested
3. **Cloud deployment** — how the same code runs on Amazon EC2

Every diagram uses [Mermaid](https://mermaid.js.org/) and is followed by a simple Hindi
explanation. Technical terms, file names and code stay in English.

---

## 1. Application flow

```mermaid
flowchart TD
    A["Browser<br/>(HTML5 + CSS3 + JS + Bootstrap 5)"] --> B["Frontend pages<br/>Jinja2 templates + Chart.js"]
    B --> C["Flask backend<br/>app/__init__.py : create_app()"]
    C --> D{"Authentication<br/>Flask-Login<br/>@login_required"}
    D -- "not logged in" --> E["Redirect to /auth/login"]
    D -- "logged in" --> F["Validation<br/>Flask-WTF forms + CSRF"]
    F --> G["Blueprint routes<br/>auth / dashboard / transactions"]
    G --> H["Business logic<br/>app/services.py"]
    H --> I["ORM<br/>Flask-SQLAlchemy models"]
    I --> J[("SQLite database<br/>instance/spendwise.db<br/>users + transactions")]
    J --> I
    I --> H
    H --> G
    G --> B
    B --> A
```

### Hindi explanation

| Component | Role (Hindi) |
| --- | --- |
| **Browser** | User ka phone ya laptop ka browser. Yahi se website khulti hai. |
| **Frontend** | HTML, CSS, Bootstrap aur JavaScript se bane pages. Chart.js graphs banata hai. Ye sirf dikhane ka kaam karta hai. |
| **Flask backend** | Asli dimaag. `create_app()` sab kuch taiyaar karta hai — database connection, login system, routes aur error pages. |
| **Authentication** | Flask-Login check karta hai ki user login hai ya nahi. Private page kholne se pehle `@login_required` rok deta hai aur login page par bhej deta hai. |
| **Validation** | Flask-WTF form ke saare fields check karta hai — amount, date, category, type. CSRF token se fake form submit nahi ho sakta. |
| **Blueprints** | Code ko teen hisson me baanta gaya hai — `auth` (login/register), `dashboard` (summary + charts), `transactions` (income/expense ka CRUD). |
| **Business logic** | `app/services.py` me saare jod-ghata (total income, total expense, balance, monthly series, category breakdown) hote hain — hamesha logged-in user ke hi records par. |
| **ORM** | Flask-SQLAlchemy Python code ko SQL me badalta hai. Hum SQL likhte hi nahi, isliye SQL injection ka risk nahi rehta. |
| **SQLite database** | Ek hi file me data — `users` aur `transactions` tables. App band karne par bhi data bacha rehta hai. |

---

## 2. DevOps flow (Git → GitHub → CI)

```mermaid
flowchart LR
    A["Developer<br/>(Windows laptop + VS Code)"] --> B["Git<br/>local commits"]
    B --> C["GitHub<br/>remote repository"]
    C --> D["GitHub Actions<br/>.github/workflows/tests.yml"]
    D --> E["Ubuntu runner<br/>Python 3.11 / 3.12"]
    E --> F["pip install<br/>-r requirements.txt"]
    F --> G["pytest<br/>tests/ (temporary SQLite)"]
    G -- "all tests pass" --> H["Green check on the commit"]
    G -- "any test fails" --> I["Red cross + full log"]
```

### Hindi explanation

| Component | Role (Hindi) |
| --- | --- |
| **Developer** | Aap apne Windows laptop aur VS Code me code likhte hain. |
| **Git** | Har change ka snapshot (commit) banata hai. Galti hone par purana version wapas mil sakta hai. |
| **GitHub** | Online cloud par code ka backup + team work + code review. |
| **GitHub Actions** | Jab bhi aap push karte ho ya pull request banate ho, GitHub khud hi ek machine (runner) uthata hai. |
| **pip install** | Runner par project ki saari libraries install hoti hain (`requirements.txt` se). |
| **pytest** | 99 automated tests chalte hain. Tests apna alag temporary SQLite database banate hain, isliye asli data safe rehta hai. |
| **Green / red status** | Sab test pass ho gaye to green tick, warna red cross ke saath pura error log milta hai. Isse bug main branch me jaane se pehle hi pakda jaata hai. |

**Important:** CI me koi AWS credential nahi chahiye, aur workflow koi deployment nahi
karta. Ye sirf code ko test karta hai.

---

## 3. Cloud deployment (Amazon AWS EC2)

```mermaid
flowchart TD
    A["User's browser<br/>http://EC2-public-IPv4"] --> B["AWS Security Group<br/>allow 22 from your IP, 80 / 443 from anywhere"]
    B --> C["AWS EC2 instance<br/>Amazon Linux / Ubuntu, t3.micro"]
    C --> D["Nginx<br/>port 80 / 443 reverse proxy"]
    D --> E["Gunicorn<br/>127.0.0.1:8000 (WSGI server)"]
    E --> F["Flask application<br/>run:app (FLASK_CONFIG=production)"]
    F --> G[("Persistent SQLite file<br/>e.g. /home/ec2-user/spendwise/instance/spendwise.db")]
    C --> H["systemd service<br/>spendwise.service (auto start / restart)"]
    H --> E
    I["Backup (cron / S3)"] --> G
```

### Hindi explanation

| Component | Role (Hindi) |
| --- | --- |
| **Browser** | Duniya me kahin se bhi user EC2 ke public IP par website khol sakta hai. |
| **Security Group** | AWS ka firewall. SSH (port 22) sirf aapke IP se, aur web traffic (80/443) sabse allowed. |
| **EC2 instance** | AWS ka virtual Linux server. Aapka Windows laptop par Ubuntu install karne ki zaroorat nahi — existing Linux instance use karein. |
| **Nginx** | Reverse proxy. User ki request pehle Nginx par aati hai, wo static files (CSS/JS) khud deta hai aur baaki request Gunicorn ko bhej deta hai. Isse HTTPS aur domain lagana aasan ho jaata hai. |
| **Gunicorn** | Production WSGI server. Flask ka development server sirf testing ke liye hai — public internet par nahi kholna chahiye. Gunicorn multiple requests sambhalta hai. |
| **Flask application** | Wahi code jo laptop par chala tha, bas `FLASK_CONFIG=production` ke saath: DEBUG off, secure cookies on, asli SECRET_KEY environment se. |
| **systemd** | Server restart hone par bhi app apne aap chalu ho jaata hai, aur crash hone par restart kar deta hai. |
| **Persistent SQLite** | Database file EC2 ke disk par rehti hai. Instance terminate karne par disk bhi chali jaati hai — isliye regular backup zaroori hai. |
| **Backup** | Cron job ya script se database file ki copy (S3 ya doosri jagah) rakhna. |

### Important honest note (Hindi)

SQLite ek single file database hai. College demonstration ya chhote project ke liye ye
bilkul theek hai aur free hai. Lekin ye **high availability** nahi deta — bahut saare users
ek saath likhne (write) lage to dikkat aa sakti hai, aur agar file delete ho gayi to data
chala jaayega. Isliye EC2 par persistent storage + regular backup zaroori hai. Bade
production system me iski jagah Amazon RDS (MySQL/PostgreSQL) use hota hai.

---

## 4. Request lifecycle example

Example: user *"Add Expense"* form submit karta hai.

```mermaid
sequenceDiagram
    participant U as Browser
    participant N as Nginx
    participant G as Gunicorn
    participant F as Flask route
    participant W as Flask-WTF
    participant S as services.py
    participant D as SQLite

    U->>N: POST /transactions/add (form data + CSRF token)
    N->>G: forward the request
    G->>F: call the view function
    F->>W: validate form and CSRF token
    W-->>F: OK / error messages
    F->>D: INSERT transaction with user_id = current_user.id
    D-->>F: new row id
    F->>S: recalculation is done later on the dashboard
    F-->>U: redirect to /transactions with a success flash message
    U->>N: GET /dashboard
    N->>G: forward
    G->>F: dashboard.home()
    F->>S: get_summary / monthly_series / category_breakdown
    S->>D: SELECT ... WHERE user_id = ?
    D-->>S: rows
    S-->>F: totals in paise
    F-->>U: HTML + chart JSON rendered by Chart.js
```

### Hindi explanation

1. Browser form ka data **aur** CSRF token bhejta hai.
2. Flask-WTF dono check karta hai. Galat token ho to request reject ho jaati hai.
3. Naya transaction **session** se mile `user_id` ke saath save hota hai — form se aaya
   user id kabhi trust nahi kiya jaata.
4. Save hone ke baad success message dikhta hai.
5. Dashboard dobara khulte hi server apne aap sab total dobara nikaalta hai aur charts
   ko naya data mil jaata hai.

---

## 5. Data model (ER diagram)

```mermaid
erDiagram
    USERS ||--o{ TRANSACTIONS : "owns"

    USERS {
        int     id PK
        string  name
        string  email UK "unique, indexed"
        string  password_hash "PBKDF2-SHA256, salted"
        datetime created_at
    }

    TRANSACTIONS {
        int      id PK
        int      user_id FK "-> users.id, ON DELETE CASCADE, indexed"
        string   type "income | expense (CHECK)"
        int      amount_paise "CHECK amount_paise > 0"
        string   category
        string   description
        date     txn_date "indexed"
        datetime created_at
    }
```

### Hindi explanation

- **Ek user ke bahut se transactions** ho sakte hain (one-to-many relationship).
- `email` par **unique** constraint hai — ek hi email se do account nahi ban sakte.
- `password_hash` me sirf hash jata hai, asli password kabhi store nahi hota.
- `amount_paise` **integer** hai (rupee × 100) — isse 0.1 + 0.2 jaise decimal errors
  nahi hote.
- Database level par do CHECK constraints hain: amount hamesha 0 se bada, aur type sirf
  `income` ya `expense`.
- `user_id` par foreign key aur index hai, isliye har query sirf us user ka data laati hai.

---

## 6. Layered file map

| Layer | Files |
| --- | --- |
| Presentation | `app/templates/**`, `app/static/css/style.css`, `app/static/js/*.js` |
| Routing | `app/auth/routes.py`, `app/dashboard/routes.py`, `app/transactions/routes.py` |
| Validation | `app/forms.py` |
| Business logic | `app/services.py`, `app/utils.py`, `app/constants.py` |
| Data | `app/models.py`, `app/__init__.py` (`db` object) |
| Configuration | `config.py`, `.env`, `.env.example` |
| Entry points | `run.py` (local + Gunicorn), Flask CLI commands (`init-db`, `create-user`) |
| Tests | `tests/conftest.py`, `tests/test_*.py` |
| Automation | `.github/workflows/tests.yml` |
| Automation script | `scripts/seed_data.py` |
