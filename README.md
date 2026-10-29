# SpendWise — Personal Expense Tracker

SpendWise is a complete, working web application that lets a person record income and
expenses, see where the money goes, and understand the monthly picture through charts
and reports.

It was built as a **BCA Capstone Project** that brings three subjects together:

| Subject | How SpendWise covers it |
| --- | --- |
| Capstone Project Development | A full CRUD web application with authentication, validation, reports and tests |
| Cloud Development using Amazon AWS | Deployment guide for a Linux **Amazon EC2** instance (Gunicorn + Nginx + systemd) |
| DevOps using GitHub and GitHub Actions | Git repository + an automated **CI pipeline** that runs the pytest suite on every push and pull request |

> Everything in this repository was built and tested locally on **Windows** first.
> AWS is only *documented* here — no AWS resource is created automatically by this project.

---

## Table of contents

1. [Features](#1-features)
2. [Technology stack](#2-technology-stack)
3. [Folder structure](#3-folder-structure)
4. [Quick start (Windows)](#4-quick-start-windows)
5. [All commands at a glance](#5-all-commands-at-a-glance)
6. [Demo account](#6-demo-account)
7. [How money is stored](#7-how-money-is-stored)
8. [Security](#8-security)
9. [Automated tests](#9-automated-tests)
10. [Git and GitHub](#10-git-and-github)
11. [GitHub Actions CI](#11-github-actions-ci)
12. [AWS deployment](#12-aws-deployment)
13. [Documentation index](#13-documentation-index)
14. [Limitations](#14-limitations)

---

## 1. Features

**Authentication**

- Customer registration with unique-email validation and password confirmation
- Login / logout (logout is a POST request, so it is CSRF protected)
- Passwords hashed with Werkzeug (PBKDF2-SHA256, salted) — plain text is never stored
- Session-based authentication with Flask-Login
- Every private page is protected by `@login_required`
- Profile page (change name, change password)

**Income and expense management**

- Add income and add expense
- View transaction details
- Edit a transaction
- Delete a transaction (POST only, with a confirmation modal)
- Filters: transaction type, category, date range, and a free-text search on description/category
- Pagination (10 records per page)

**Dashboard and reports**

- Total income, total expenses and remaining balance (all-time)
- Current-month income and current-month expenses
- Recent transactions table
- Monthly income-vs-expense bar chart (last 6 months) — Chart.js
- Category-wise expense doughnut chart — Chart.js
- Dedicated monthly summary view with a month selector (`/dashboard/summary`)
- JSON endpoint `/dashboard/api/chart-data` for the chart data

**User experience**

- Bootstrap 5 layout with a collapsible sidebar (desktop, tablet and mobile)
- Friendly success / warning / danger messages after every action
- Empty states ("you have no transactions yet") instead of broken-looking charts
- Custom 400, 403, 404 and 500 error pages

---

## 2. Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5.3.3, Bootstrap Icons |
| Charts | Chart.js 4.4.3 (CDN) |
| Backend | Python 3.11+ , Flask 3.0.3 |
| Database | SQLite |
| ORM | Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.0) |
| Authentication | Flask-Login 0.6.3 |
| Forms + CSRF | Flask-WTF 1.2.1 / WTForms 3.1.2 |
| Password hashing | Werkzeug 3.0.4 |
| Testing | pytest 8.3.3 |
| Version control | Git + GitHub |
| CI | GitHub Actions |
| Production server | Gunicorn 23.0.0 (Linux only) |
| Reverse proxy | Nginx (optional) |
| Cloud | Amazon AWS EC2 |

No Docker, no Kubernetes and no paid service is required.

---

## 3. Folder structure

```
spendwise/
├── app/
│   ├── __init__.py            # application factory, extensions, error handlers, CLI
│   ├── constants.py           # categories, transaction types, chart colours
│   ├── models.py              # User + Transaction models
│   ├── forms.py               # WTForms forms (validation + CSRF)
│   ├── services.py            # all report/summary calculations
│   ├── utils.py               # paise <-> rupees conversion and INR formatting
│   ├── auth/routes.py         # /auth/register, /auth/login, /auth/logout, /auth/profile
│   ├── dashboard/routes.py    # /dashboard, /dashboard/summary, /dashboard/api/chart-data
│   ├── transactions/routes.py # /transactions (list, add, detail, edit, delete)
│   ├── templates/             # Jinja2 templates (base, auth, dashboard, transactions, errors)
│   └── static/                # css/, js/, images/
├── tests/                     # pytest suite (conftest.py + 5 test modules)
├── scripts/seed_data.py       # optional, idempotent demo data seeder
├── docs/                      # setup guide, AWS guide, report, slides, viva questions
├── .github/workflows/tests.yml
├── config.py                  # Development / Testing / Production configuration
├── run.py                     # local entry point
├── requirements.txt           # runtime + test dependencies
├── requirements-prod.txt      # + Gunicorn (Linux/EC2 only)
├── pytest.ini
├── .env.example
└── .gitignore
```

---

## 4. Quick start (Windows)

A detailed step-by-step guide in Hindi is available at
[docs/local_setup_hindi.md](docs/local_setup_hindi.md).

```powershell
# 1. go to the project folder
cd C:\Users\ASUS\OneDrive\Documents\Trae\temp_20261029_01\spendwise

# 2. create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. install the dependencies
pip install -r requirements.txt

# 4. create your local environment file and put a real secret key in it
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
#    -> copy the printed value into SECRET_KEY= inside .env

# 5. create the database tables
flask --app run.py init-db

# 6. (optional) insert 4 months of demo data
python scripts\seed_data.py

# 7. start the application
python run.py
```

Open <http://127.0.0.1:5000> in the browser.

> The Flask development server started by `python run.py` is for **local development
> and demonstration only**. It is bound to `127.0.0.1` and must never be exposed to the
> public internet — on EC2 the application runs behind Gunicorn (see the AWS guide).

---

## 5. All commands at a glance

| Goal | Command (run from the project folder, inside the virtual environment) |
| --- | --- |
| Activate the virtual environment | `.\.venv\Scripts\Activate.ps1` |
| Install dependencies | `pip install -r requirements.txt` |
| Create the database tables | `flask --app run.py init-db` |
| Create one user from the terminal | `flask --app run.py create-user` |
| Insert the demo data | `python scripts\seed_data.py` |
| Rebuild the demo data | `python scripts\seed_data.py --force` |
| Start the app locally | `python run.py` |
| Run all tests | `pytest` |
| Run one test file | `pytest tests/test_auth.py` |
| Run one test | `pytest tests/test_auth.py::test_register_creates_a_user` |
| Stop the app | `Ctrl + C` in the terminal |

---

## 6. Demo account

`python scripts\seed_data.py` creates one demo account with about four months of
realistic transactions:

```
Email    : demo@spendwise.com
Password : Demo@12345
```

The seeder is **idempotent** — running it twice does not duplicate anything. It prints a
message and stops. Use `--force` to delete and rebuild the demo data.

(The email validator rejects reserved domains such as `.local` / `.test` / `.invalid`,
which is why the demo account uses a normal-looking domain.)

---

## 7. How money is stored

Floating point numbers cannot represent `0.1 + 0.2` exactly, which is unacceptable for
money. SpendWise therefore stores every amount as an **integer number of paise**
(1 rupee = 100 paise) in `transactions.amount_paise`.

- Conversion and rounding (`ROUND_HALF_UP`) live in [app/utils.py](app/utils.py)
- Formatting uses the Indian grouping style: `₹1,23,45,678.90`
  (exposed to templates as the Jinja filter `{{ paise_value | inr }}`)
- `Transaction.amount` returns the value in rupees as a `Decimal` for display only

---

## 8. Security

| Concern | Implementation |
| --- | --- |
| Password storage | `generate_password_hash` / `check_password_hash` (salted PBKDF2-SHA256) |
| CSRF | `CSRFProtect` on the whole app + `form.hidden_tag()` in every form |
| Session cookies | `HttpOnly`, `SameSite=Lax`, and `Secure` in production |
| Secrets | Read from environment variables / `.env`; `.env` is git-ignored |
| Production safety | `ProductionConfig.validate()` refuses a missing or placeholder `SECRET_KEY`; `DEBUG` is off |
| Ownership | Every query filters on `user_id = current_user.id`; a transaction id from the URL is verified against the owner (403) or treated as not found (404) |
| SQL injection | Only SQLAlchemy query APIs are used; no string-built SQL |
| Redirects | The `next` parameter is validated, so open redirects are blocked |
| Login errors | The same message for "unknown email" and "wrong password" |
| Logging | Application events only — never passwords, tokens or secret keys |
| Error pages | Friendly 400 / 403 / 404 / 500 pages; no stack traces shown to users |

`.gitignore` excludes `.env`, `*.db`, virtual environments, caches, `*.pem` / `*.key`
and `.aws/`. Never commit real credentials or real financial records.

---

## 9. Automated tests

```powershell
pytest
```

- Configuration: [pytest.ini](pytest.ini) (`testpaths = tests`, `pythonpath = .`)
- Fixtures: [tests/conftest.py](tests/conftest.py) builds a temporary SQLite file inside
  the operating-system temp folder (`TEST_DATABASE_URL`) and deletes it when the run
  finishes, so tests **never** touch the real database.
- Result of the last local run: **99 passed** in about 39 seconds
  (details and the per-module breakdown are in
  [docs/project_report.md](docs/project_report.md)).

| Module | What it covers |
| --- | --- |
| `tests/test_auth.py` | public pages, registration (duplicate email, mismatch, short password, invalid email, case normalisation), login, logout, route protection, profile, change password, hash storage |
| `tests/test_transactions.py` | add income/expense, rounding, zero/negative/non-numeric amounts, invalid type/date/category/description, detail, edit, delete, cross-user 403, filters, date ranges, search, pagination |
| `tests/test_dashboard.py` | empty dashboard, all-time vs current-month totals, balance, no double counting, category percentages, monthly series, chart data, other-user isolation, monthly summary |
| `tests/test_security.py` | CSRF on/off, cookie flags, production secret validation, salted hashes, no plaintext passwords, injection-safe search, generic login error, open-redirect protection, repository hygiene |
| `tests/test_errors.py` | custom 400 / 403 / 404 / 500 pages, no leaked tracebacks |

---

## 10. Git and GitHub

Git is **not** installed on this machine yet — install it from
<https://git-scm.com/download/win> first, then:

```powershell
git --version                 # check the installation
git init                      # start the repository (run once)
git branch -M main

git add .
git commit -m "Add SpendWise expense tracker application"

git remote add origin https://github.com/<your-username>/spendwise.git
git push -u origin main
```

Before pushing, always confirm that `.env` and the database file are **not** in the list
shown by `git status`. They are already covered by `.gitignore`.

---

## 11. GitHub Actions CI

The workflow file is [.github/workflows/tests.yml](.github/workflows/tests.yml).

- Triggers: every push, and every pull request that targets `main` or `master`
- Matrix: Python 3.11 and 3.12 on `ubuntu-latest`
- Steps: checkout → set up Python (with pip cache) → install `requirements.txt` →
  import check → `pytest -v --tb=short` → upload the cache folder if a step fails
- No secrets and **no AWS credentials** are used — the tests use a temporary SQLite
  database, so the job is fully self-contained
- Results: open the **Actions** tab of the repository and click the latest run

---

## 12. AWS deployment

The complete, cost-aware guide for deploying SpendWise to **your own** Amazon EC2
instance is in [docs/aws_deployment_guide.md](docs/aws_deployment_guide.md).

Highlights:

- First check which EC2 instances you already have and reuse one if practical
- Review instance, storage, public IPv4 and data-transfer costs; set a billing alert
  **before** creating anything
- Deploy on an existing Linux (Amazon Linux / Ubuntu) instance — no need to install
  Ubuntu on your Windows laptop
- Run Flask through **Gunicorn** behind **Nginx**, managed by **systemd**
- Keep SQLite as a file on persistent storage (include it in your backups) — it is fine
  for an academic demonstration but it is **not** a high-availability database
- Never expose the Flask development server to the internet; restrict SSH to your own IP
- No AWS resource is created by this project, and AWS secret keys must never be pasted
  into source code, chat messages or screenshots

---

## 13. Documentation index

| Document | Purpose |
| --- | --- |
| [docs/local_setup_hindi.md](docs/local_setup_hindi.md) | Windows setup, step by step, in simple Hindi + troubleshooting |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Mermaid diagrams: application flow, DevOps flow, cloud deployment + Hindi explanation |
| [docs/project_report.md](docs/project_report.md) | Full capstone report (abstract → conclusion, ER diagram, use cases, testing results) |
| [docs/presentation_outline.md](docs/presentation_outline.md) | 12-slide presentation outline (English content + Hindi speaker notes) |
| [docs/viva_questions.md](docs/viva_questions.md) | 30+ viva questions with answers |
| [docs/aws_deployment_guide.md](docs/aws_deployment_guide.md) | Amazon EC2 deployment, costs, security groups, backups, updates |

---

## 14. Limitations

- SQLite is a single-file database: suitable for a small academic demonstration, not for
  many concurrent writers. It needs persistent storage and backups on EC2.
- No email verification, password reset by email, multi-currency support, recurring
  transactions or budget limits.
- Amounts are limited to `₹10,00,00,000` per transaction (a validation guard).
- The charts render the last 6 months; older data is available through the filters and
  the monthly summary view.
