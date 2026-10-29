# SpendWise — Presentation Outline (12 Slides)

**How to use this file**

- Each slide has **English slide content** (put this on the slide) and
  **Hindi speaker notes** (say this while presenting).
- Total: 12 slides. Keep each slide to 5–7 bullet points and one picture/diagram.
- Placeholders in `_[square brackets]_` must be replaced with your own details.
- For the "Results" slide, insert **your own** screenshots — never internet images.

---

## Slide 1 — Title

### Slide content

- **Project Title:** SpendWise — Personal Expense Tracker
- **Submitted by:** _[Your name]_ — Roll No. _[Your roll number]_
- **Course:** BCA — _[Semester / Year]_
- **Guide:** _[Guide's name]_
- **Department / College:** _[Department, College name]_
- **Academic Year:** _[2025–2026]_
- **Technology highlight:** Flask · SQLite · Bootstrap 5 · Chart.js · GitHub Actions · AWS EC2

**Visual:** the SpendWise logo, or a screenshot of your landing page.

### Hindi speaker notes

> "Respected sir/madam aur sabhi examiners, aaj main apna BCA capstone project
> **SpendWise — Personal Expense Tracker** present kar raha hoon. Ye ek web application
> hai jisme user apni income aur expenses record karta hai, aur dashboard par usse
> graphs aur totals milte hain. Is project me maine teen cheezein cover ki hain —
> capstone development, Amazon AWS par cloud deployment, aur GitHub Actions se DevOps
> automation. Sabse pehle main problem statement bataata hoon."

⏱ ~45 seconds

---

## Slide 2 — Problem Statement

### Slide content

- Students and salaried people track money in notebooks, chats or memory
- **No single record** → difficult to answer "how much did I spend on food this month?"
- Manual totalling is **error-prone**; a broken spreadsheet formula silently gives a wrong balance
- Plain lists give **no visual insight** into trends or top spending categories
- Paper / spreadsheets have **no access control** or search
- Many simple trackers use floating-point maths → `₹0.01` rounding errors
- **Need:** a simple, secure, server-backed tracker with exact money maths and a visual dashboard

**Visual:** a rough sketch — confused student with a notebook, a receipt pile, a question mark.

### Hindi speaker notes

> "Aaj ke samay me har vyakti ke paas income ek baar aati hai, lekin expense din bhar
> hota rehta hai — canteen, bus, recharge, books, dawaai. Ye sab log notebook me likhte
> hain ya bhool jaate hain. Problem ye hai ki notebook me total karna mushkil hai, galti
> hone ka dar rehta hai, search nahi kar sakte, aur chart bhi nahi banta. Kuch simple apps
> floating-point maths use karte hain jisse paisa ek paisa idhar-udhar ho jaata hai.
> Isliye mujhe ek aisa system chahiye tha jo sahi total nikaale, secure ho, aur mobile par
> bhi dikhe."

⏱ ~45 seconds

---

## Slide 3 — Objectives

### Slide content

**Primary**

1. Build a web app to record personal income and expenses
2. Secure registration, login, logout and profile management
3. Complete **CRUD** for transactions with server-side validation
4. Server-side reports: total income, total expense, balance, current-month totals, monthly series, category breakdown
5. Responsive dashboard with **Chart.js** visualisations
6. Enforce **ownership** — no user can see another user's data
7. Automated **pytest** test suite
8. **GitHub Actions CI** + documented **AWS EC2** deployment

**Secondary:** exact money storage (integer paise), professional UI, dependency-light

**Visual:** a simple numbered list; optionally icons for each objective.

### Hindi speaker notes

> "Mere project ke objectives ye hain — pehla, income aur expense record karne ka web app
> banana. Doosra, secure registration aur login. Teesra, poora CRUD — add, view, edit,
> delete — validation ke saath. Chautha, saare totals aur reports server par calculate
> karna. Paanchva, Chart.js se interactive graphs. Chhatha aur bahut important —
> ownership check, yaani ek user doosre ka data kabhi na dekh sake. Saatva, 99 automated
> tests. Aur aathva, GitHub Actions se CI aur AWS EC2 ka deployment guide."

⏱ ~50 seconds

---

## Slide 4 — Proposed Solution

### Slide content

- **SpendWise** — a browser-based personal expense tracker
- Register → log in → add income/expense → see dashboard
- **Three-tier architecture**: Presentation → Application → Data
- Money stored as **integer paise** (1 rupee = 100 paise) → no floating-point errors
- All reports computed **on the server** from the **logged-in user's own** records
- Filters: type, category, search text, date range + pagination
- Friendly messages, empty states, custom 400/403/404/500 pages
- Runs on Windows locally; same code deployable to Linux on AWS

**Visual:** the three-tier architecture diagram (from `ARCHITECTURE.md`).

### Hindi speaker notes

> "Mera solution hai SpendWise. User browser kholta hai, register karta hai, login karta
> hai, aur phir apni income aur expense entries add karta hai. Application teen parts me
> bani hai — frontend yaani dikhne wala part, backend yaani Flask ka logic, aur database
> yaani SQLite. Sabse important design decision — maine paisa integer paise me store
> kiya hai, rupee ka 100 gunaa. Isse 0.1 aur 0.2 jodne par jo 0.30000000000000004 jaisa
> error aata hai, wo kabhi nahi hota. Saare totals server par bante hain, sirf logged-in
> user ke records se."

⏱ ~50 seconds

---

## Slide 5 — Features

### Slide content

**Authentication**

- Register (unique email + password confirmation), login, logout (POST + CSRF)
- Profile edit, change password
- Passwords hashed with Werkzeug (PBKDF2-SHA256, salted)
- Every private page protected by `@login_required`

**Transactions**

- Add income / expense, view, edit, delete (POST only)
- Filter by type, category, search text and date range; 10 records per page

**Dashboard and reports**

- Total income, total expenses, remaining balance
- Current-month income and expenses
- Monthly income-vs-expense bar chart (last 6 months)
- Category-wise expense doughnut chart with percentages
- Monthly summary view for any month
- Empty states when there is no data

**Visual:** a 2×2 grid of your own dashboard screenshots (cards, bar chart, doughnut chart, list).

### Hindi speaker notes

> "Features ki baat karein. Authentication me registration, login, logout aur profile
> management hai. Password kabhi plain text me store nahi hota — Werkzeug se salted hash
> banta hai. Transaction side par poora CRUD hai — add, view, edit, delete — aur chaar
> tarah ke filters: type, category, search aur date range. Dashboard par chaar summary
> cards hain — total income, total expense, balance aur is mahine ke figures. Saath me do
> graphs — mahine ka bar chart aur category-wise doughnut chart. Agar naya user hai jiske
> paas data nahi hai, to khali chart ke bajaye ek friendly empty state dikhta hai."

⏱ ~60 seconds

---

## Slide 6 — Technology Stack

### Slide content

| Layer | Technology |
| --- | --- |
| Frontend | HTML5, CSS3, JavaScript, **Bootstrap 5.3.3**, Bootstrap Icons |
| Charts | **Chart.js 4.4.3** |
| Backend | **Python 3** + **Flask 3.0.3** |
| Database | **SQLite** |
| ORM | **Flask-SQLAlchemy 3.1.1** (SQLAlchemy 2.0) |
| Authentication | **Flask-Login 0.6.3** |
| Forms + CSRF | **Flask-WTF 1.2.1** / WTForms 3.1.2 |
| Password hashing | **Werkzeug 3.0.4** |
| Testing | **pytest 8.3.3** |
| Version control + CI | **Git / GitHub / GitHub Actions** |
| Production server | **Gunicorn 23.0.0** (Linux) |
| Reverse proxy | **Nginx** (optional) |
| Cloud | **Amazon AWS EC2** |

**Deliberately not used:** Docker, Kubernetes, paid services, payment gateways

**Visual:** technology logos in rows; add the sentence "100% free and open-source".

### Hindi speaker notes

> "Technology stack ye hai. Backend Python Flask me hai, kyunki Flask chhota aur samajhne
> me aasan hai — request aur response ka poora cycle clear rehta hai. Database SQLite hai
> kyunki isme kuch install karne ki zaroorat nahi, ek file me data rehta hai — college
> project ke liye perfect. ORM ke liye Flask-SQLAlchemy use kiya, isse main SQL likhta hi
> nahi, isliye SQL injection ka risk nahi rehta. Authentication Flask-Login, forms aur
> CSRF Flask-WTF, password hashing Werkzeug. Frontend Bootstrap 5 aur charts Chart.js se
> bane hain. Testing pytest se, aur CI GitHub Actions se. Production me Gunicorn aur Nginx
> use honge. Docker aur Kubernetes jaan-boojh kar use nahi kiya — ye project ke scope se
> bahar hai."

⏱ ~60 seconds

---

## Slide 7 — System Architecture

### Slide content

```
Browser (HTML5, Bootstrap 5, Chart.js)
        │
        ▼
Flask backend — application factory + blueprints
  ├── auth          /auth/*          (register, login, logout, profile)
  ├── dashboard     /dashboard/*     (cards, charts, monthly summary, JSON API)
  └── transactions  /transactions/*  (add, list, detail, edit, delete)
        │
        ▼
Authentication (Flask-Login) + Validation (Flask-WTF + CSRF)
        │
        ▼
Business logic (app/services.py) — all totals and reports
        │
        ▼
ORM (Flask-SQLAlchemy models) → SQLite database (users, transactions)
```

**Key design points**

- **Application factory** `create_app()` → testable and Gunicorn-friendly
- **Blueprints** separate the three feature areas
- **Services layer** keeps SQL out of the routes and makes report maths testable
- Every query filters on `user_id = current_user.id`

**Visual:** the Mermaid diagram from `ARCHITECTURE.md` (section 1) rendered as an image.

### Hindi speaker notes

> "Architecture ko dekhein. User ka browser frontend dikhata hai — HTML, CSS, Bootstrap
> aur Chart.js. Request Flask backend par aati hai. Backend ko maine teen blueprints me
> baanta hai — auth, dashboard aur transactions. Isse code saaf rehta hai. Request pehle
> authentication se guzarti hai, phir validation se, phir business logic se, aur aakhir me
> ORM ke through database me pahunchti hai. Application factory pattern use kiya hai —
> `create_app()` — isse testing me alag app instance bana sakte hain aur production me
> Gunicorn isi ko use karta hai. Sabse important baat — har query me `user_id =
> current_user.id` lagta hai, isliye ek user doosre ka data nahi dekh sakta."

⏱ ~60 seconds

---

## Slide 8 — Database and Security

### Slide content

**Database design (2 tables)**

- `users` — id, name, **email (UNIQUE)**, password_hash, created_at
- `transactions` — id, **user_id (FK)**, type, **amount_paise**, category, description, txn_date, created_at
- One-to-many: one user → many transactions (cascade delete)
- **Amounts stored as integer paise** — exact money maths
- Database-level CHECK constraints: `amount_paise > 0`, `type IN ('income','expense')`

**Security**

- Salted PBKDF2-SHA256 password hashing (never plain text)
- CSRF protection on every form; delete and logout are POST-only
- Server-side validation of every field
- **Ownership check on every record**: missing → 404, another user's → 403
- All queries use the ORM (no string-built SQL)
- Secrets from environment variables; `.env`, `*.db`, `*.pem` git-ignored
- Production: DEBUG off, `Secure` + `HttpOnly` + `SameSite=Lax` cookies
- Friendly 400/403/404/500 pages; no traceback shown to users

**Visual:** the ER diagram from `ARCHITECTURE.md` (section 5) + a small "security layers" icon row.

### Hindi speaker notes

> "Database me do tables hain. `users` table me user ki detail aur password ka hash.
> `transactions` table me har entry, aur `user_id` se pata chalta hai ki wo kis user ki
> hai — ye one-to-many relationship hai. Amount ko maine integer paise me rakha hai,
> isliye koi rounding error nahi. Security par maine bahut dhyan diya. Password salted
> hash me store hota hai. Har form par CSRF token lagta hai, aur delete aur logout sirf
> POST se hote hain — kisi simple link se data delete nahi ho sakta. Sabse important
> rule — jo transaction id URL me aata hai, usse kabhi blindly trust nahi karta. Agar
> record doosre user ka hai to 403 Forbidden, aur nahi mila to 404 Not Found. Secrets
> environment variables se aate hain, aur `.env`, database file, `.pem` files sab
> `.gitignore` me hain, isliye GitHub par kabhi nahi jaate."

⏱ ~70 seconds

---

## Slide 9 — AWS Deployment

### Slide content

```
User browser → AWS Security Group (22 = my IP, 80/443 = public)
             → EC2 Linux instance (t3.micro, 8 GiB gp3)
             → Nginx (reverse proxy, static files, HTTPS)
             → Gunicorn (127.0.0.1:8000, 3 workers)
             → Flask app (FLASK_CONFIG=production)
             → Persistent SQLite file on EBS + daily backups
```

**Steps followed**

1. Check the AWS account and region
2. Review existing EC2 instances — **reuse if practical**
3. Review costs: instance, EBS storage, public IPv4, data transfer
4. Free Tier check + monthly budget with e-mail alerts
5. Secure SSH; restrict port 22 to my own IP
6. Install Python, pip, git, nginx, sqlite3
7. Clone the repository; create the virtual environment; install `requirements-prod.txt`
8. Production environment variables in `/etc/spendwise/spendwise.env` (`chmod 600`)
9. `flask --app run.py init-db` + `create-user`
10. Gunicorn test → systemd service → Nginx → test the public URL
11. Daily `.backup` + cron; logs via `journalctl`

**Cost honesty:** a running `t3.micro` in Mumbai ≈ $0.0104/hour (≈ $7.6/month), plus EBS
(≈ $0.08/GiB-month) and a public IPv4 (≈ $0.005/hour) → roughly **$12/month** if left
running 24×7 outside the Free Tier. Free Tier gives 750 hours/month of `t2.micro`/
`t3.micro` for the first 12 months.

**Honest note:** SQLite is fine for a single-server academic demo but is **not** a
high-availability database; it needs persistent storage and backups. A real product would
use Amazon RDS.

**Visual:** the EC2 diagram from `ARCHITECTURE.md` (section 3) + a real screenshot of your
running site (only after you deploy).

### Hindi speaker notes

> "Cloud deployment ke liye maine AWS EC2 choose kiya, kyunki ye sabse simple aur Free
> Tier me aata hai. Flow ye hai — user ka browser security group se aata hai, wahan se
> EC2 instance par. EC2 par Nginx reverse proxy hai, uske peeche Gunicorn, aur uske peeche
> mera Flask app. Flask ka development server public internet par kabhi expose nahi karna
> chahiye — isliye production me Gunicorn use hota hai, jo systemd service se chalta hai,
> yaani server restart hone par app apne aap chalu ho jaata hai. Database file EC2 ke disk
> par persistent rehti hai aur uska daily backup hota hai. Cost ke baare me main honest
> hoon — ek t3.micro instance 24 ghante chalne par mahine ka takriban 12 dollar padta hai;
> Free Tier me pehle 12 mahine ke instance hours free hote hain, par storage aur public IP
> ka chhota charge rehta hai. Aur ek limitation — SQLite ek single file database hai, ye
> college demo ke liye theek hai par high availability nahi deta; bade system me Amazon RDS
> use hota hai."

⏱ ~75 seconds

---

## Slide 10 — DevOps and Testing

### Slide content

**Git workflow**

- `git init` → commits → GitHub repository → `git push`
- `.gitignore` protects: `.env`, `*.db`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `*.pem`, `*.key`, `.aws/`

**GitHub Actions CI** — `.github/workflows/tests.yml`

- Trigger: every **push** and every **pull request** (targeting `main` / `master`)
- Matrix: **Python 3.11 and 3.12** on `ubuntu-latest`
- Steps: checkout → set up Python (pip cache) → install `requirements.txt` → import check → **`pytest -v --tb=short`** → failure artifacts
- **No secrets, no AWS credentials** — fully self-contained
- Result visible on the **Actions** tab (green tick / red cross)

**Testing with pytest**

- 99 tests across 5 modules; isolated temporary SQLite database
- Modules: `test_auth.py` (25), `test_transactions.py` (32), `test_dashboard.py` (21), `test_security.py` (15), `test_errors.py` (6)

**Visual:** the CI pipeline diagram from `ARCHITECTURE.md` (section 2) + a screenshot of a
green Actions run.

### Hindi speaker notes

> "DevOps ke liye maine Git aur GitHub use kiya. Har change ka commit banaya, code GitHub
> par push kiya. `.gitignore` me `.env`, database file, `.venv`, cache aur `.pem` files
> daali hain, isliye koi secret ya asli data GitHub par nahi jaata. GitHub Actions me ek
> workflow likha hai jo har push aur pull request par apne aap chalta hai. Wo Ubuntu par
> Python 3.11 aur 3.12 set karta hai, dependencies install karta hai, aur `pytest` chalata
> hai. Isme koi AWS credential nahi chahiye. Agar test pass ho jaaye to green tick milta
> hai, warna red cross ke saath pura log milta hai. Testing me mere paas 99 tests hain,
> jo paanch files me baante hain — authentication, transactions, dashboard ka maths,
> security, aur error pages. Ye tests apna alag temporary database banate hain, isliye
> asli data kabhi touch nahi hota."

⏱ ~70 seconds

---

## Slide 11 — Results and Screenshots

### Slide content

**Test results (actual local run)**

```
tests/test_auth.py .........................                             [ 25%]
tests/test_dashboard.py .....................                            [ 46%]
tests/test_errors.py ......                                              [ 52%]
tests/test_security.py ...............                                   [ 68%]
tests/test_transactions.py ................................              [100%]

============================= 99 passed in 39.34s =============================
```

- Environment: Windows, Python 3.13.4, pytest 8.3.3, temporary SQLite database
- **99 passed, 0 failed**

**Implemented and working**

- Registration / login / logout, profile and password change
- Full transaction CRUD with 4 filters and pagination
- Dashboard totals, 2 Chart.js charts, monthly summary view
- Custom 400 / 403 / 404 / 500 pages
- GitHub Actions CI workflow
- Amazon EC2 deployment guide

**Screenshots to insert here:** dashboard with cards + charts, transaction list with
filters, add-transaction validation error, 403 page, `pytest` output, GitHub Actions green
run. _(Use only your own screenshots!)_

**Not claimed:** no cloud deployment has been performed yet, and no performance
measurement was taken.

**Visual:** a 2×3 grid of your screenshots.

### Hindi speaker notes

> "Result ki baat karein. Maine apne laptop par `pytest` chalaya — 99 tests the, aur
> sabke sab pass ho gaye, koi fail nahi hua. Isme authentication, transactions ka CRUD,
> dashboard ka maths, security aur error pages sab cover hain. Screenshots me aap dekh
> sakte hain — dashboard ke summary cards, do charts, transaction list with filters, ek
> validation error, aur GitHub Actions ka green run. Main ek baat saaf karna chahta hoon —
> maine AWS par abhi deployment nahi kiya hai, sirf uska poora cost aur security ke saath
> guide banaya hai. Jab examiner puche to main honestly bata sakta hoon ki kaam kahan tak
> hua hai."

⏱ ~60 seconds

---

## Slide 12 — Conclusion and Future Scope

### Slide content

**Conclusion**

- SpendWise is a complete, working personal expense tracker
- Secure authentication + full transaction CRUD
- All reports computed server-side from the user's own records
- Exact money maths using integer paise (INR formatting)
- 99 automated tests passing + GitHub Actions CI
- Cost-aware Amazon EC2 deployment plan (Gunicorn + systemd + Nginx)
- Same code base works locally on Windows and on Linux in the cloud

**Limitations**

- SQLite: single file, not for high concurrency / high availability
- No password reset by e-mail, no 2FA, no login rate limiting
- No budget planner, no recurring transactions, no multi-currency
- Deployment is manual (documented, not automated)

**Future scope**

1. Recurring transactions and monthly budgets with alerts
2. Savings goals and progress tracking
3. CSV / PDF export and printable monthly statements
4. Password reset by e-mail + login rate limiting + 2FA
5. Migrate SQLite → **Amazon RDS**; store receipts on **Amazon S3**
6. Automated deployment from GitHub Actions after CI passes

**Thank you — questions welcome**

**Visual:** a "before → after" mini timeline, or a summary icon row.

### Hindi speaker notes

> "Aakhir me — SpendWise ek complete aur working expense tracker hai. Secure
> authentication, poora CRUD, server par banaye gaye saare reports, integer paise se
> sahi money maths, 99 passing tests, GitHub Actions ki CI, aur AWS EC2 ka detail
> deployment plan — sab taiyaar hai. Limitations bhi maine honestly document ki hain —
> SQLite high availability nahi deta, password reset aur 2FA abhi nahi hai, aur
> deployment manual hai. Future me main recurring transactions, budget alerts, PDF
> export, aur SQLite se Amazon RDS par shift karna chahta hoon. Dhanyavaad — ab main
> aapke prashnon ka uttar dena chahta hoon."

⏱ ~60 seconds

---

## Presentation tips (Hindi)

1. **Total time ~11–12 minute.** Har slide ka time upar diya hai — isi ko follow karo.
2. **Live demo ke liye pehle se taiyari karo:** terminal me virtual environment activate
   kar lo, `flask --app run.py init-db` chala lo, `python scripts\seed_data.py` chala lo,
   aur browser me login karke dashboard khol ke rakho. Demo me time barbaad nahi hoga.
3. **Internet issue ho to:** charts Chart.js CDN se load hote hain — agar internet na ho,
   charts nahi dikhenge. Screenshots ready rakho as a backup.
4. **Do numbers yaad rakho:** **99 tests** aur **amount_paise (integer paise)**. Examiner
   inme se kisi ek par zaroor poochenge.
5. **Honest raho:** jo nahi kiya, uske baare me saaf bolo — jaise AWS deployment abhi nahi
   kiya. Isse examiner ka bharosa badhta hai.
6. **Slide par text kam, bolne me zyada.** Ek slide par 5–7 bullets se zyada na rakho.
7. **Screenshots apne hi banao.** Internet se liye gaye screenshots pakde jaane par project
   par sawal uth sakta hai.
