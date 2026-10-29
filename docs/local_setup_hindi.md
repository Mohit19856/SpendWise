# SpendWise — Local Setup Guide (Windows) / लोकल सेटअप गाइड

Ye guide simple Hindi/Hinglish me hai. Source code, file names aur technical words
English me hi likhe gaye hain — isse college report aur viva me aasani hoti hai.

**Project folder ka poora path:**

```
C:\Users\ASUS\OneDrive\Documents\Trae\temp_20261029_01\spendwise
```

Isi folder ke andar se saare commands chalane hain.

---

## Step 0 — Sabse pehle ye samajh lo

| Cheez | Matlab |
| --- | --- |
| **Virtual environment (`.venv`)** | Is project ki apni alag Python "duniya". Isme jo library install karte ho, wo aapke laptop ke baaki projects ko disturb nahi karti. |
| **`.env` file** | Isme secret key aur settings rehti hain. Ye file **kabhi** GitHub par upload nahi karni. |
| **`.venv\Scripts\Activate.ps1`** | Virtual environment ko chalu karne ka command. Jab tak `(.venv)` prompt me na dikhe, samjho environment chalu nahi hai. |
| **`python run.py`** | Development server chalu karta hai. Sirf local testing ke liye — internet par public nahi karna. |

---

## Step 1 — Check karo ki Python installed hai ya nahi

PowerShell kholo (Start button → "PowerShell" type karo → Enter) aur chalao:

```powershell
python --version
```

**Expected result:**

```
Python 3.13.4
```

Agar `Python was not found` ya Microsoft Store khul jaaye, to
<https://www.python.org/downloads/windows/> se Python 3.11 ya usse naya install karo aur
install karte waqt **"Add python.exe to PATH"** wala checkbox zaroor tick karo.

Aage badhne se pehle `pip` bhi check kar lo:

```powershell
python -m pip --version
```

---

## Step 2 — Check karo ki Git installed hai ya nahi

```powershell
git --version
```

**Expected result** (kuch aisa):

```
git version 2.47.0.windows.1
```

Agar `The term 'git' is not recognized` aaye, to Git install karo:
<https://git-scm.com/download/win> (download karke default options ke saath Next-Next
karte jao, phir PowerShell **band karke naya** kholo).

> Is laptop par abhi Git installed nahi mila. Jab tak Git install nahi hota, tab tak
> GitHub wale steps (Step 16 ke baad ke) nahi chalenge — baaki pura app bina Git ke bhi
> chal jaata hai.

---

## Step 3 — Project ko VS Code me kholo

Option A — VS Code me: **File → Open Folder →** `spendwise` folder select karo.

Option B — PowerShell se:

```powershell
code "C:\Users\ASUS\OneDrive\Documents\Trae\temp_20261029_01\spendwise"
```

VS Code ke left panel me aapko `app`, `tests`, `docs`, `run.py`, `config.py` dikhne
chahiye.

---

## Step 4 — VS Code me terminal kholo

VS Code me: **Terminal → New Terminal** (shortcut `` Ctrl + ` ``).

Ye terminal automatically project folder me khulta hai. Confirm karne ke liye:

```powershell
Get-Location
```

**Expected result:** `...\temp_20261029_01\spendwise`

---

## Step 5 — Virtual environment banao

```powershell
python -m venv .venv
```

**Expected result:** Koi output nahi aata (chup-chaap ban jaata hai). Left panel me ek
naya `.venv` folder dikhne lagega.

---

## Step 6 — PowerShell me virtual environment chalu karo

```powershell
.\.venv\Scripts\Activate.ps1
```

**Expected result:** Prompt ke aage `(.venv)` likha aayega:

```
(.venv) PS C:\Users\ASUS\OneDrive\Documents\Trae\temp_20261029_01\spendwise>
```

### Agar error aaye: "running scripts is disabled on this system"

Ye Windows ki default security setting hai. Iska fix (sirf aapke user ke liye):

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Poocha jaaye `Do you want to change the execution policy?` to `Y` type karke Enter dabao.
Phir `.\.venv\Scripts\Activate.ps1` dobara chalao.

**Agar execution policy change karna allowed na ho**, to temporary option use karo:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

> Ye "missing package", "import error" aur "database error" ke 60% cases ka root cause
> hota hai — kyunki environment active nahi hota aur system Python use ho jata hai.
> **Har naye terminal me Step 6 dobara chalana padta hai.**

---

## Step 7 — Dependencies install karo

```powershell
pip install -r requirements.txt
```

**Expected result (last lines kuch aise):**

```
Successfully installed Flask-3.0.3 Flask-Login-0.6.3 Flask-SQLAlchemy-3.1.1
Flask-WTF-1.2.1 SQLAlchemy-2.0.35 WTForms-3.1.2 Werkzeug-3.0.4
email-validator-2.2.0 python-dotenv-1.0.1 pytest-8.3.3 ...
```

> `requirements-prod.txt` me Gunicorn hai. Wo **sirf Linux/EC2** par install hota hai —
> Windows par install karne ki koshish na karo.

---

## Step 8 — Local environment file banao (`.env`)

```powershell
Copy-Item .env.example .env
```

Ab is file me ek **asli secret key** daalni hai. Pehle random key generate karo:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

**Expected result:** 64 characters ka ek random string, jaise:

```
b3f1c9a4e7d2... (aisa hi kuch lamba random text)
```

Us value ko copy karke `.env` file me `SECRET_KEY=` ke aage paste kar do:

```ini
SECRET_KEY=b3f1c9a4e7d2...paste-your-generated-value-here
FLASK_CONFIG=development
DATABASE_URL=sqlite:///spendwise.db
PORT=5000
```

> `.env` already `.gitignore` me hai, isliye ye GitHub par upload nahi hogi.
> Ye key kabhi kisi ko chat/screenshot me na do.

---

## Step 9 — Database banao

```powershell
flask --app run.py init-db
```

**Expected result:**

```
[2026-10-29 23:40:35,109] INFO in __init__: SpendWise started (debug=True)
Database tables created.
```

Ab `instance\spendwise.db` file ban jaati hai. **Ye file `.gitignore` me hai**, isliye
GitHub par nahi jaayegi.

### (Optional) Demo data daalo

```powershell
python scripts\seed_data.py
```

**Expected result:**

```
Demo data created successfully.
   Email    : demo@spendwise.com
   Password : Demo@12345
   Records  : 64 transactions over the last 4 months
```

Ye script **idempotent** hai — dobara chalao to duplicate data nahi banega, sirf message
dikhega. Fresh demo data chahiye to:

```powershell
python scripts\seed_data.py --force
```

---

## Step 10 — Application start karo

```powershell
python run.py
```

**Expected result:**

```
[2026-10-29 23:45:02,001] INFO in __init__: SpendWise started (debug=True)
 * Serving Flask app 'app'
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

> Ye terminal **chalu hi rehna chahiye**. Naya command chalane ke liye VS Code me
> **doosra terminal** kholo (Terminal → New Terminal) aur usme `.\.venv\Scripts\Activate.ps1`
> chalao.

---

## Step 11 — Browser me website kholo

Browser me ye address daalo:

```
http://127.0.0.1:5000
```

**Expected result:** SpendWise ka landing page — purple/indigo theme, "SpendWise"
branding, "Create account" aur "Log in" buttons.

---

## Step 12 — Register aur login karo

**Option A — naya account banao:** `Create account` par click karo aur form bharo.

- Full name: `Riya Sharma` (2 se 80 characters)
- Email: `riya@example.com`
- Password: `Riya@12345` (kam se kam 8 characters)
- Confirm password: wahi password

Sahi form par: dashboard khul jaayega aur green message aayega
"Welcome to SpendWise, Riya! Your account is ready."

Galat form par: red message aur field ke neeche error, jaise:

- "This email is already registered. Please log in instead."
- "Both passwords must match."
- "Password must be at least 8 characters long."

**Option B — demo account use karo** (agar Step 9 me seed chalaya tha):

- Email: `demo@spendwise.com`
- Password: `Demo@12345`

Login hone ke baad dashboard par 4 summary cards dikhenge — Total Income, Total
Expenses, Balance aur is month ki details.

---

## Step 13 — Income aur expense add karo

Sidebar me **Add transaction** par click karo (`/transactions/add`).

**Income ka example:**

| Field | Value |
| --- | --- |
| Transaction type | Income (money coming in) |
| Amount (INR) | `25000` |
| Category | Salary |
| Transaction date | aaj ki date |
| Description | Monthly salary credited |

**Expense ka example:**

| Field | Value |
| --- | --- |
| Transaction type | Expense (money going out) |
| Amount (INR) | `450.50` |
| Category | Food |
| Transaction date | aaj ki date |
| Description | Dinner with friends |

Form submit karne par: green message "Expense of ₹450.50 added successfully." aur
transaction list khul jaati hai. Dashboard par total aur balance turant badal jaata hai.

**Kya-kya reject hoga (server side par bhi check hota hai):**

| Input | Result |
| --- | --- |
| Amount `0` ya `-100` | "Amount must be greater than 0." |
| Amount `abc` | "Please enter an amount." |
| Category `Salary` + Type `Expense` | "Please choose a category that matches the selected transaction type." |
| Date saal 2000 se pehle ya 2100 ke baad | "Date must be between the years 2000 and 2100." |
| 256 characters se lambi description | "Description cannot be longer than 255 characters." |

---

## Step 14 — Charts aur filters test karo

**Charts (Dashboard page par):**

1. **Monthly Income vs Expense** — bar chart, last 6 months. Mouse hover karne par
   `₹` me value dikhti hai.
2. **Expenses by Category** — doughnut chart, aur uske neeche category-wise list with
   percentage.

Charts hamesha **sirf logged-in user ke apne** transactions se bante hain.

**Filters (Transactions page par, `/transactions`):**

1. **Type** dropdown — `Expense` chuno, sirf expenses dikhne chahiye.
2. **Category** dropdown — `Food` chuno.
3. **Date from / Date to** — `2026-10-01` se `2026-10-31`.
4. **Search** — `salary` type karo, description ya category me match hone chahiye.
5. **Apply filters** par click karo. Table ke upar "Income / Expense" ka total bhi badalta hai.
6. **Clear** par click karke filters hata do.

**Agar date_from > date_to de do**, to app khud hi dono ko swap kar deta hai (error
nahi aata).

**Pagination:** 10 se zyada transactions ho to neeche `Next` / page numbers dikhte hain.

---

## Step 15 — Transaction edit aur delete karo

**Edit:** list me kisi row ke **Edit** (pencil icon) par click karo
(`/transactions/<id>/edit`). Amount `450.50` ko `500` kar do aur Save karo.
**Expected:** "Transaction updated successfully."

**Delete:** row ke **Delete** (trash icon) par click karo → confirmation modal aayega →
`Delete` confirm karo.
**Expected:** "Transaction deleted successfully." aur total turant kam ho jaata hai.

> Delete sirf POST request se hota hai (CSRF protected). Kabhi bhi ek simple link se data
> delete nahi hota. **Logout bhi POST hai** — isliye kisi doosri website se wo trigger
> nahi ho sakta.

**Ownership check (bahut important):** login karke kisi doosre user ke transaction ka id
URL me daal do, jaise `/transactions/999`:

| Situation | Result |
| --- | --- |
| Transaction exist hi nahi karta | **404** — "Page not found" |
| Transaction kisi doosre user ka hai | **403** — "Access denied" (aur server log me warning) |

---

## Step 16 — Profile dekho aur logout karo

Sidebar me **Profile** (`/auth/profile`):

- Naam badal ke **Update profile** dabao → "Your profile has been updated."
- **Change password** form me current password, naya password (8+ characters) aur confirm
  daal ke submit karo → "Your password has been changed successfully."
- Galat current password par: "Your current password is incorrect."

Logout: sidebar ke **Log out** button par click karo (POST request) → landing page khulega
aur message: "You have been logged out successfully."

Logout ke baad `/dashboard` kholne ki koshish karo → login page par redirect ho jaoge
message ke saath: "Please log in to open that page."

---

## Step 17 — Automated tests chalao

**Pehle app band karo** (`Ctrl + C`) — testing ke liye zaroori nahi, par saaf-suthra rehta
hai. Naya terminal kholo, `.\.venv\Scripts\Activate.ps1` chalao, phir:

```powershell
pytest
```

**Expected result (aakhir ki lines):**

```
============================= test session starts =============================
platform win32 -- Python 3.13.4, pytest-8.3.3, pluggy-1.x.x
rootdir: ...\spendwise
configfile: pytest.ini
testpaths: tests
collected 99 items

tests/test_auth.py .........................                             [ 25%]
tests/test_dashboard.py .....................                            [ 46%]
tests/test_errors.py ......                                              [ 52%]
tests/test_security.py ...............                                   [ 68%]
tests/test_transactions.py ................................              [100%]

============================= 99 passed in 39.34s =============================
```

Sirf ek file chalao:

```powershell
pytest tests\test_auth.py
```

Ek hi test chalao:

```powershell
pytest tests\test_auth.py::test_login_with_wrong_password_shows_error
```

> Tests **apna alag temporary SQLite database** banate hain (Windows ke temp folder me).
> Aapke `instance\spendwise.db` wale asli data ko ye kabhi touch nahi karte. Test run
> hone ke baad wo temporary file apne aap delete ho jaati hai.

---

## Step 18 — App ko band karo aur dobara chalu karo

| Kaam | Command |
| --- | --- |
| App band karo | Running terminal me `Ctrl + C` |
| App dobara chalu karo | `.\.venv\Scripts\Activate.ps1` phir `python run.py` |
| Port busy ho? | `Ctrl + C` se purana instance band karo, ya `.env` me `PORT=5001` karke `python run.py` |
| Database check karo | `python -c "from run import app; from app.models import Transaction; exec('with app.app_context():\n    print(Transaction.query.count())')"` |

**Persistence test:** app band karo → dobara `python run.py` chalao → browser refresh
karo. Aapke saare transactions wapas dikhne chahiye. SQLite data ko disk par save rakhta
hai, isliye restart par data kabhi nahi khota.

---

## Common Problems aur Unke Fix (Troubleshooting)

### 1. `python : The term 'python' is not recognized`

**Reason:** Python PATH me nahi hai.
**Fix:** Python dobara install karo aur **"Add python.exe to PATH"** tick karo. Ya
`py --version` try karo aur `py` use karo: `py -m venv .venv`.

---

### 2. `.\.venv\Scripts\Activate.ps1 ... running scripts is disabled on this system`

**Reason:** Windows PowerShell ki execution policy.
**Fix:**

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Emergency me (sirf us terminal ke liye):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Ya `cmd` me chalana ho to: `.venv\Scripts\activate.bat`

---

### 3. `ModuleNotFoundError: No module named 'flask'`

**Reason:** Virtual environment active nahi hai (ya galat Python use ho raha hai).
**Fix:** Prompt me `(.venv)` dikhna chahiye. Nahi dikh raha to:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -c "import flask, sys; print(flask.__version__, sys.executable)"
```

`sys.executable` me path `...\spendwise\.venv\Scripts\python.exe` hona chahiye.

---

### 4. `ModuleNotFoundError: No module named 'app'` ya `'config'`

**Reason:** Command galat folder se chal raha hai, ya `FLASK_APP` set nahi.
**Fix:** `Get-Location` se confirm karo ki aap `spendwise` folder me ho. Flask command me
hamesha `--app run.py` likho:

```powershell
flask --app run.py init-db
```

`pytest` ke liye `pytest.ini` me `pythonpath = .` already set hai — isliye us folder se
chalane par import theek ho jaate hain.

---

### 5. `OSError: [WinError 10048]` / `Only one usage of each socket address` / port 5000 busy

**Reason:** Port 5000 already kisi aur process ya purane app instance ne le liya hai.
**Fix:** Pehle purana terminal `Ctrl + C` se band karo. Phir:

```powershell
netstat -ano | findstr :5000
```

Jo PID mile usko dekh lo (`Get-Process -Id <PID>`), ya bas doosra port use karo —
`.env` me `PORT=5001` karke `python run.py` chalao aur
`http://127.0.0.1:5001` kholo.

---

### 6. `sqlalchemy.exc.OperationalError: no such table: users`

**Reason:** Database tables nahi bane.
**Fix:**

```powershell
flask --app run.py init-db
```

---

### 7. `sqlalchemy.exc.OperationalError: unable to open database file`

**Reason:** `instance` folder missing/permission issue, ya `DATABASE_URL` ka path galat.
**Fix:** `.env` me `DATABASE_URL=sqlite:///spendwise.db` rakho (relative path chalta
hai). Manual folder banao:

```powershell
New-Item -ItemType Directory -Force instance
flask --app run.py init-db
```

---

### 8. `RuntimeError: SECRET_KEY is not configured`

**Reason:** `.env` file nahi bani, ya usme `SECRET_KEY` khali hai — ye check sirf
production config me hota hai, par local me bhi `.env` hona chahiye.
**Fix:**

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

Us value ko `.env` me paste karo.

---

### 9. `jinja2.exceptions.TemplateNotFound`

**Reason:** `app/templates` folder delete/move ho gaya.
**Fix:** `app\templates` folder aur uske andar `auth`, `dashboard`, `transactions`,
`errors`, `partials` sub-folders hone chahiye. Project dobara checkout karo:

```powershell
git checkout -- .
```

---

### 10. `werkzeug.routing.exceptions.BuildError: Could not build url for endpoint`

**Reason:** Template me galat endpoint name, ya blueprint register nahi hua.
**Fix:** `pytest` chalao — tests is tarah ki galti turant pakad lete hain. Check karo ki
`app/__init__.py` ke `_register_blueprints` me teeno blueprint register hain:
`auth_bp`, `dashboard_bp`, `transactions_bp`.

---

### 11. Charts khali / `Chart is not defined`

**Reason:** Chart.js CDN load nahi hua (internet issue) ya block ho gaya.
**Fix:** Internet check karo. Aapka data tab bhi safe hai — charts sirf dikhne ka
problem hai. `View page source` me `cdn.jsdelivr.net` wali script dikhni chahiye.

---

### 12. Login par "Invalid email or password" (sahi password ke saath bhi)

**Reason:** Email me galti, ya demo account ka domain reserved hai.
**Fix:** Ye app reserved domains (`.local`, `.test`, `.invalid`) wale email reject karta
hai. Demo account `demo@spendwise.com` use karta hai. Naya account bana ke wahi use karo.

---

### 13. 500 error page dikh raha hai

**Reason:** Koi unexpected server error.
**Fix:** Us terminal me dekho jahan `python run.py` chal raha hai — Flask ne pura
traceback print kiya hoga. Wahi traceback padho. Aur `pytest` chalao taaki known galti
turant pakdi jaaye.

---

### 14. `pip install` fail / network error

**Fix:** Internet check karo, ya:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt --timeout 60
```

Company/college network ho to mobile hotspot try karo.

---

## Aage kya

| Kaam | Kahan dekho |
| --- | --- |
| Application flow, DevOps flow, EC2 architecture ke diagrams | [ARCHITECTURE.md](../ARCHITECTURE.md) |
| Amazon EC2 par deploy karne ka poora guide (cost + security ke saath) | [aws_deployment_guide.md](aws_deployment_guide.md) |
| Capstone report (abstract se conclusion tak) | [project_report.md](project_report.md) |
| Presentation ke 12 slides | [presentation_outline.md](presentation_outline.md) |
| Viva ke 30+ questions aur answers | [viva_questions.md](viva_questions.md) |
