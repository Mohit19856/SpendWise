# SpendWise — Viva Questions and Answers

**How to use this file**

- 40 questions with answers, grouped by topic.
- Each answer is written the way you should **say** it out loud — short, simple, honest.
- Learn the **bold** parts first; they are the keywords an examiner listens for.
- Answers marked _(project-specific)_ refer to actual code and files in this project.

---

## A. Flask and the backend

### Q1. What is Flask, and why did you choose it?

**Flask** is a lightweight **Python web framework** — a library that handles HTTP
requests, routes, sessions and templates. I chose it because it is **minimal and
explicit**: nothing happens "magically", so a beginner can see the full request/response
cycle. It also has a small dependency footprint, which keeps the project easy to run and
easy to grade.

### Q2. What is a virtual environment, and why is it needed?

A **virtual environment** (`venv`) is an isolated Python installation inside the project
folder. Packages installed in it do not affect other projects on the machine, and the
project always uses the exact versions listed in `requirements.txt`. It prevents the
classic "it works on my laptop but not on the server" problem. In this project it is the
`.venv` folder, activated with `.\.venv\Scripts\Activate.ps1` on Windows.

### Q3. What is the application factory pattern?

Instead of creating the Flask app at import time, the project defines a function
`create_app(config_name)` in [app/\_\_init\_\_.py](file:///C:/Users/ASUS/OneDrive/Documents/Trae/temp_20261029_01/spendwise/app/__init__.py)
that builds and returns a configured app. Benefits: tests can create **many independent
app instances** with different settings, and Gunicorn can load `run:app` cleanly. It also
avoids circular imports.

### Q4. What is a blueprint, and how many does your project have?

A **blueprint** is a way to organise a group of related routes into a separate Python
module. SpendWise has **three**: `auth_bp` (`/auth/*`), `dashboard_bp` (`/dashboard/*`) and
`transactions_bp` (`/transactions/*`). They are registered in `_register_blueprints()`
inside the application factory.

### Q5. Explain the request lifecycle in your application.

1. The browser sends an HTTP request.
2. Flask matches the URL to a view function through the routing table.
3. `@login_required` (Flask-Login) checks the session; if there is no logged-in user, the
   visitor is redirected to the login page.
4. The form (Flask-WTF) validates the data and the CSRF token.
5. The view calls helper functions in `app/services.py` and the SQLAlchemy models.
6. Jinja renders an HTML template (or `jsonify` returns JSON).
7. The browser receives the response and Chart.js draws the charts.

### Q6. What does `if __name__ == "__main__":` do in `run.py`?

It makes sure `app.run()` — the Flask development server — only starts when the file is
executed **directly** (`python run.py`), and not when the module is imported (for example
by Gunicorn or pytest).

### Q7. Why is the development server not used in production?

Flask's built-in server is **single-threaded and not security-hardened**; the Flask
documentation itself warns that it is for development only. On EC2 the application runs
under **Gunicorn**, a real WSGI server with multiple worker processes, behind **Nginx**.
The dev server is also bound to `127.0.0.1`, so it is not even reachable from outside the
laptop.

### Q8. What is the difference between `@app.route` and a blueprint route?

`@app.route` registers a route directly on the application object, which is fine for one
or two simple pages (used here for the public landing page `/`). Blueprint routes are
registered on a blueprint and only become live when the blueprint is registered on the
app — that makes the code modular and the URL prefix easy to change in one place.

---

## B. Frontend and backend

### Q9. Which frontend technologies did you use, and why Bootstrap?

**HTML5, CSS3, vanilla JavaScript and Bootstrap 5.3.3**, plus **Bootstrap Icons** and
**Chart.js 4.4.3**. Bootstrap was chosen because it provides a **responsive grid** and
ready-made components (cards, tables, badges, alerts, modals), so the application looks
professional on desktop, tablet and mobile without writing a large custom CSS framework.
A custom `style.css` sits on top of it for the SpendWise look.

### Q10. How does the frontend get its data?

Two ways. **Server-side rendering**: the Flask view computes the numbers and passes them
to the Jinja template, which produces HTML. **JSON for charts**: the same data is embedded
in a `data-chart` attribute of the page and is also available from the endpoint
`/dashboard/api/chart-data`, which returns JSON. `charts.js` reads that JSON and draws the
charts. No separate front-end framework or build step is needed.

### Q11. How are the charts generated and where does the data come from?

With **Chart.js**. `charts.js` receives an object containing month labels, income values,
expense values and category values. Those values are in **paise**, so the script divides
by 100 and formats them in Indian rupee style for the tooltips. Crucially, the data comes
only from the **authenticated user's own transactions** — the queries in
`app/services.py` always filter by `user_id`.

### Q12. What is a responsive design, and how did you achieve it?

A responsive design adapts to different screen sizes. SpendWise uses the Bootstrap grid
(`col-12 col-md-6 col-xl-3` for the stat cards), a sidebar that becomes a collapsible
off-canvas drawer on small screens (toggled by `app.js`), and CSS media queries in
`style.css`. Verified with the browser DevTools device toolbar.

### Q13. Why did you not use React or Angular?

The project brief required **HTML/CSS/JavaScript with Bootstrap**. Server-rendered Jinja
templates plus a small amount of JavaScript keep the project simple, dependency-light and
easy to explain, with no build tooling — and it fully satisfies the functional
requirements.

### Q14. What is XSS, and does your application protect against it?

**Cross-Site Scripting** is when an attacker injects JavaScript that other users' browsers
execute. **Jinja2 auto-escapes** template variables by default, so a description like
`<script>alert(1)</script>` is rendered as harmless text. The application never marks user
input as safe (`|safe` is not used on user data), so this protection stays intact.

---

## C. Database, SQLite and ORM

### Q15. Why SQLite instead of MySQL or PostgreSQL?

SQLite stores the whole database in a **single file** and needs **zero configuration**,
so the project runs anywhere with just Python. For a single-user academic application it
is perfect. For a real product with many concurrent writers, or where high availability is
needed, I would move to a client-server database such as MySQL, PostgreSQL or
**Amazon RDS**.

### Q16. What is an ORM, and why use Flask-SQLAlchemy?

**ORM** = Object-Relational Mapper. It maps Python classes to database tables so you work
with objects (`transaction.amount`) instead of SQL strings. Benefits: readable code, no
manual SQL, less chance of **SQL injection**, and the same code can later target SQLite,
MySQL or PostgreSQL with almost no changes.

### Q17. Explain your database schema.

Two tables. **`users`** — `id` (primary key), `name`, `email` (unique, indexed),
`password_hash`, `created_at`. **`transactions`** — `id` (primary key), `user_id`
(foreign key to `users.id`, indexed, ON DELETE CASCADE), `type` (income/expense),
`amount_paise` (integer), `category`, `description`, `txn_date` (indexed), `created_at`.
It is a **one-to-many** relationship: one user, many transactions.

### Q18. Why do you store the amount as integer paise instead of a decimal or a float?

Because **binary floating point cannot represent decimal fractions exactly**:
`0.1 + 0.2` gives `0.30000000000000004`. For money that is unacceptable. Storing
`amount × 100` as an **integer** makes all addition exact. The conversion helpers
`rupees_to_paise()` and `paise_to_rupees()` live in [app/utils.py](file:///C:/Users/ASUS/OneDrive/Documents/Trae/temp_20261029_01/spendwise/app/utils.py)
and use `Decimal` with `ROUND_HALF_UP`, so a value like `₹250.50` is stored as exactly
`25050` paise.

### Q19. What is a primary key, a foreign key and a unique constraint?

**Primary key** — a column that uniquely identifies each row (`id`). **Foreign key** —
a column that points to the primary key of another table (`transactions.user_id →
users.id`); it enforces referential integrity. **Unique constraint** —
`users.email` is unique, so the database itself prevents two accounts with the same email,
even if application-level validation were bypassed.

### Q20. What are the CHECK constraints in your tables?

Two, on `transactions`: `amount_paise > 0` (no zero or negative amounts can ever be
stored) and `type IN ('income','expense')` (no other transaction type is possible). They
act as a last line of defence at the database level, independent of the application code.

### Q21. What does `cascade="all, delete-orphan"` do?

It means that if a `User` is deleted, all their `Transaction` rows are deleted
automatically. This prevents orphan records that point to a user who no longer exists.

### Q22. What is `db.create_all()` and when is it called?

It creates the tables that do not exist yet, based on the models. It is called by the CLI
command `flask --app run.py init-db`. It never drops or alters existing tables, so running
it repeatedly is safe.

### Q23. How does your seed script avoid duplicate data?

`scripts/seed_data.py` first looks for the demo account by email. If it exists and
`--force` was not given, it prints *"Demo account already exists … Nothing was added, so
records were not duplicated."* and exits. So running the script many times can never
duplicate records.

---

## D. Authentication and authorization

### Q24. What is the difference between authentication and authorization?

**Authentication** = *who are you?* — verifying identity (email + password at login).
**Authorization** = *what are you allowed to do?* — the permission check. In SpendWise,
authenticated users can add transactions, but authorization ensures a user can only
**read, edit or delete their own** records. Both are implemented; they are not the same
thing.

### Q25. How is authentication implemented in your application?

With **Flask-Login**. On successful login, `login_user(user)` stores the user id in a
signed **session cookie**. On each request, the `@login_manager.user_loader` callback
reloads the user, and `current_user` becomes available in every view. Private views are
decorated with `@login_required`, which redirects anonymous visitors to the login page.

### Q26. You have a URL like `/transactions/<id>/edit`. What if I change the id to someone else's transaction?

That is the **insecure direct object reference** attack, and it is prevented. Every such
route first calls `get_owned_transaction_or_404()` in
[app/transactions/routes.py](file:///C:/Users/ASUS/OneDrive/Documents/Trae/temp_20261029_01/spendwise/app/transactions/routes.py):
if the record does not exist → **404 Not Found**; if it exists but `transaction.user_id !=
current_user.id` → **403 Forbidden** and a warning is written to the log. The id from the
URL is therefore never trusted on its own, and automated tests prove this.

### Q27. How are passwords stored? Show me that the plain password is not in the database.

Only a **salted hash** is stored, produced by Werkzeug's `generate_password_hash()`
(PBKDF2-SHA256). `set_password()` hashes it, `check_password()` verifies a login attempt
with `check_password_hash()`. The plain password never touches the database, is never
logged, and is never rendered in a template. `tests/test_security.py` asserts that the
stored value is not equal to the plain password and that the hash contains a salt.

### Q28. What is salting, and why is it important?

A **salt** is random data added to the password before hashing, and it is stored with the
hash. Two users with the same password therefore get **different** hashes, so an attacker
cannot pre-compute a lookup table (**rainbow table**) or see "these 40 users share a
password". Werkzeug generates the salt automatically for every call.

### Q29. How does logout work, and why is it a POST request?

Logout calls `logout_user()`, which removes the user from the session. It is deliberately a
**POST** route with a CSRF token instead of a plain `GET` link, so that a malicious page
cannot log the user out by simply embedding an image or link pointing at `/auth/logout`.

### Q30. Why do unknown email and wrong password produce the same error message?

To prevent **account enumeration** — if the app said "this email is not registered", an
attacker could discover which email addresses have accounts. SpendWise always replies
*"Invalid email or password. Please try again."*

---

## E. Security (CSRF and others)

### Q31. What is CSRF, and how does your application prevent it?

**Cross-Site Request Forgery**: a malicious website makes the victim's browser submit a
request to your application while they are logged in, using their session cookie. The
defence is a **CSRF token**: `CSRFProtect` (Flask-WTF) generates a random token per
session, every form includes it through `form.hidden_tag()`, and the server rejects any
POST that does not carry a matching token (with a friendly 400 page via the `CSRFError`
handler). All state-changing actions (add, edit, delete, profile update, logout) are POST.

### Q32. Which security measures are in place besides CSRF and hashing?

Server-side validation on every field; ownership checks on every record; only ORM queries
(no string-built SQL) to prevent injection; a validated `next` parameter to prevent open
redirects; `HttpOnly`, `SameSite=Lax` and (in production) `Secure` session cookies; the
`ProductionConfig.validate()` check that refuses to start with a placeholder secret key;
`DEBUG` disabled in production; environment-variable secrets with `.env` git-ignored;
friendly error pages that never expose tracebacks; and logging that never records
passwords or secrets.

### Q33. Where do you store the secret key, and what happens if it leaks?

It lives only in the **environment** — locally in the git-ignored `.env` file, and in
production in `/etc/spendwise/spendwise.env` with `chmod 600`, read by the systemd unit.
The secret key signs session cookies and CSRF tokens, so it must never be committed. If it
leaked, an attacker could forge cookies; the fix is to rotate the key immediately (which
invalidates all existing sessions) and to move it into a managed secret store.

### Q34. What would happen if a user's account is deleted?

Because of `cascade="all, delete-orphan"` on the relationship and
`ON DELETE CASCADE` on the foreign key, that user's transactions are deleted with the
account, so no orphan rows remain.

### Q35. What security features are still missing?

Honestly: **login rate limiting / account lockout** (to slow down brute-force attempts),
**two-factor authentication**, **e-mail verification**, **password reset by e-mail**, and
an **audit log** of sensitive actions. These are listed in the Future Scope section of the
report.

---

## F. CRUD and reports

### Q36. Explain the CRUD operations in your project.

**Create** — `POST /transactions/add` inserts a new income or expense (`user_id` comes from
`current_user.id`, never from the form). **Read** — `GET /transactions/` (paginated,
filtered history) and `GET /transactions/<id>` (single record details).
**Update** — `GET/POST /transactions/<id>/edit` updates the record after the ownership
check. **Delete** — `POST /transactions/<id>/delete`, POST-only with a confirmation modal
so a plain link can never delete data.

### Q37. How are the dashboard totals calculated? Are they all-time or current-month?

| Metric | Meaning |
| --- | --- |
| Total income, Total expenses, Balance | **All time** — every transaction of the user, ever |
| Current-month income / expenses / balance | Only the **current calendar month** |
| Monthly chart | The **last six calendar months**, grouped by year-month |
| Category breakdown | All time by default; a date range is passed in the monthly summary view |

The maths lives in `app/services.py`; the all-time and month figures are labelled
separately in the UI so there is no confusion. If there are no transactions, the cards show
`₹0.00` and an empty state is displayed instead of broken charts.

### Q38. How do you avoid double counting and floating-point errors in the totals?

Double counting is impossible because every query starts from `Transaction.user_id ==
user_id` and uses `SUM(amount_paise)` grouped by type, and the monthly series is bucketed
by `(year, month)` — each row is counted exactly once. Floating-point errors are impossible
because all sums are performed on **integers (paise)**; conversion to rupees happens only
for display, through the `inr` filter.

### Q39. What filters does the transaction history support?

Transaction **type** (income/expense), **category**, a free-text **search** over the
description and category, a **date range** (`date_from` / `date_to`) and **pagination**
(10 per page). If the user provides a reversed date range, the two dates are swapped
automatically instead of showing an error.

---

## G. Testing

### Q40. How is the test suite organised, and does it touch real user data?

The suite is in `tests/` — `conftest.py` plus `test_auth.py` (25 tests),
`test_transactions.py` (32), `test_dashboard.py` (21), `test_security.py` (15) and
`test_errors.py` (6) — **99 tests in total**. `conftest.py` sets `TEST_DATABASE_URL` to a
SQLite file inside the operating system's **temporary folder** and deletes it in the
`pytest_sessionfinish` hook, so the real database in `instance/spendwise.db` is never
opened or modified. Fixtures such as `make_user`, `make_transaction`, `login` and `logout`
keep the tests short and readable.

### Q41. What is a fixture in pytest?

A **fixture** is a function that prepares something a test needs and is requested simply by
naming it as a parameter. For example, `def test_x(client, make_user):` gives the test a
Flask test client and a fresh user. Fixtures reduce repetition and make the tests
independent of one another.

### Q42. Do you have a test that proves a user cannot see another user's data?

Yes — several. `test_cannot_view_another_users_transaction`,
`test_cannot_edit_another_users_transaction`,
`test_cannot_delete_another_users_transaction` and
`test_transaction_history_is_isolated_between_users` all create two users, then check that
the first user gets **403** (or an empty list) when touching the second user's data.

---

## H. Git, GitHub and CI

### Q43. Why use Git in a college project?

Git records a **history** of every change, so you can go back to an earlier working version
if something breaks. It lets you work on a feature in a branch without disturbing the main
code, it doubles as an off-site backup when pushed to GitHub, and it is the standard tool
in industry — so it is also good practice for the student.

### Q44. What files should never be committed, and how do you prevent it?

Never: `.env` (secret key), `*.db` / `instance/` (real user financial records),
`.venv/` (huge, machine-specific), `__pycache__/` and `.pytest_cache/` (generated),
`*.pem` / `*.key` and `.aws/` (credentials). They are all listed in `.gitignore`, and
`tests/test_security.py` even asserts that these patterns are present, so a future change
cannot silently remove the protection.

### Q45. What is CI, and what does your GitHub Actions workflow do?

**Continuous Integration** means every code change is automatically built and tested on a
clean machine. The workflow `.github/workflows/tests.yml` runs on every **push** and every
**pull request**: it checks out the code, sets up **Python 3.11 and 3.12** on
`ubuntu-latest` with pip caching, installs `requirements.txt`, performs an import check,
and runs `pytest -v --tb=short`. A new push cancels the previous run for that branch
(`concurrency`). It needs **no secrets and no AWS credentials**.

### Q46. Does your CI pipeline deploy the application?

**No.** The pipeline only installs dependencies and runs the tests. No automated
deployment is implemented, and I do not claim one — the AWS deployment is a documented,
manual process performed by the student on their own account. Automated deployment after a
green build is listed in Future Scope.

### Q47. What is a pull request, and how does CI help with it?

A **pull request** asks to merge one branch into another, and it shows the diff for review.
GitHub runs the CI workflow on the PR, so if a test fails the merge button clearly shows
that something is broken — bugs are caught before the code reaches `main`.

---

## I. AWS, Gunicorn, Nginx and deployment

### Q48. What is Amazon EC2, and why did you choose it?

**EC2 (Elastic Compute Cloud)** is a **rented virtual machine** in the AWS cloud. I chose
it because it is the simplest and cheapest way to run a Flask application publicly, it
suits the AWS **Free Tier** (`t2.micro` / `t3.micro`, 750 hours per month for the first 12
months), and it gives full control over the operating system — so the same Linux commands
work as on any server. Alternatives such as Elastic Beanstalk or ECS add abstraction and
complexity that this project does not need.

### Q49. What is Gunicorn, and why can't you use it locally on Windows?

**Gunicorn** is a **production WSGI server**: it starts several worker processes, so the
app can handle multiple requests at the same time, and it recovers from worker crashes.
Flask's built-in server is single-threaded and not hardened, so it must not face the
public internet. Gunicorn does **not run on Windows** (it depends on Unix features), which
is why it lives in a separate `requirements-prod.txt` and is installed only on the EC2
instance. The command is:

```bash
gunicorn --bind 127.0.0.1:8000 --workers 3 run:app
```

### Q50. What is Nginx, and why put it in front of Gunicorn?

**Nginx** is a fast web server and **reverse proxy**. It receives the request on port
80/443, serves static files such as CSS, JavaScript and images directly (which is much
faster than going through Python), forwards everything else to Gunicorn on
`127.0.0.1:8000`, handles HTTPS certificates, buffers slow clients and adds the
`X-Forwarded-For` / `X-Forwarded-Proto` headers. Gunicorn stays bound to localhost, so it is
never directly exposed to the internet.

### Q51. Why do you need systemd in the deployment?

**systemd** keeps the application running as a managed service (`spendwise.service`). It
starts the app at boot, restarts it automatically if it crashes (`Restart=always`), reads
the environment file with the secret key, and gives you logs and control through standard
commands: `systemctl status|start|stop|restart spendwise` and
`journalctl -u spendwise -f`.

### Q52. What is a security group, and which rules did you set?

A **security group** is a virtual firewall attached to an EC2 instance. My rules: SSH
(port 22) from **my own IP only** (`/32`); HTTP (port 80) from anywhere; HTTPS (port 443)
from anywhere once a certificate exists. Ports 5000 and 8000 are **not** open — the app is
only reachable through Nginx. Keeping SSH restricted is important because otherwise every
scanner on the internet can attempt password guesses against the server.

### Q53. How much does this hosting cost, and what happens after the Free Tier ends?

For a `t3.micro` in the Mumbai region, roughly: instance ≈ **$0.0104/hour**
(≈ $7.6/month), EBS storage ≈ **$0.08/GiB-month** for 8 GiB (≈ $0.64/month), and a
**public IPv4 address ≈ $0.005/hour** (≈ $3.6/month). So about **$12 per month
(≈ ₹1,000)** if left running 24×7. Inside the first 12 months, a Free Tier account gets
**750 hours per month of `t2.micro`/`t3.micro`** free, but the storage and IPv4 charges
still apply. Stopping an instance stops the instance charge but **not** the EBS charge; I
set a **monthly budget with an e-mail alert** before creating anything to avoid a surprise
bill.

### Q54. Why is SQLite acceptable for this project but not for high availability?

SQLite writes to a single file and locks it during a write, so it does not support many
concurrent writers and has no replication or failover. For a single-user academic
demonstration it is excellent (zero configuration, no extra cost). Where high availability
is needed, you would use a managed database such as **Amazon RDS** with Multi-AZ. The
backup recipe in the deployment guide — `sqlite3 ... ".backup"` scheduled by cron — exists
because losing that one file means losing all the data.

### Q55. How would you update the application on the server?

Stop the service, take a database backup, `git pull` the new code, reinstall dependencies
if they changed, run `flask --app run.py init-db` only if the schema changed, then start
the service again and check `systemctl status` and the logs. To roll back, check out the
previous commit and restart. That whole sequence is written out in section 18 of
`docs/aws_deployment_guide.md`.

---

## J. Limitations and future improvements

### Q56. What are the main limitations of your project?

SQLite scalability (single file, single writer, no high availability); no password reset by
e-mail, no e-mail verification and no two-factor authentication; no login rate limiting;
manual data entry only (no bank/UPI/SMS import); single currency (INR); no budgets,
savings goals or recurring transactions; the charts show the last six months; the AWS
deployment is manual and documented rather than automated; and cloud screenshots must still
be captured by me after deploying.

### Q57. If you had more time, what would you improve first?

I would add, in this order: (1) **budget per category with alerts**, because it changes the
app from a record-keeper to a decision-support tool; (2) **recurring transactions**, since
rent and salary repeat every month; (3) **CSV/PDF export and a printable monthly
statement**; (4) **login rate limiting and password reset by e-mail**; and (5) migration
from **SQLite to Amazon RDS** for concurrency and managed backups.

### Q58. What did you learn from this project?

Technically: the Flask **application factory and blueprints**, server-side validation with
Flask-WTF, **session-based authentication with ownership checks**, why money must be stored
as **integer paise**, writing **99 automated tests against an isolated temporary
database**, and how a **CI pipeline on GitHub Actions** catches regressions. Practically:
that security cannot be bolted on at the end — CSRF, ownership checks and safe redirects
have to be designed in from the first route — and that documenting the cost and security
implications of a cloud deployment is as much a part of the work as writing code.

---

## Quick revision sheet (last-minute)

| Keyword | One-line answer |
| --- | --- |
| Flask | Lightweight Python web framework |
| Application factory | `create_app()` builds the app — testable, Gunicorn friendly |
| Blueprint | Groups related routes (auth, dashboard, transactions) |
| SQLite | Single-file, zero-configuration database |
| ORM / Flask-SQLAlchemy | Python classes ↔ database tables; no hand-written SQL |
| Integer paise | Money stored as `rupees × 100` → no float rounding errors |
| Werkzeug hashing | Salted PBKDF2-SHA256; plain password never stored |
| Flask-Login | Session authentication, `current_user`, `@login_required` |
| Authentication vs authorization | Who you are vs what you may do |
| Ownership check | Missing → 404; another user's → 403 (never trust the URL id) |
| CSRF | `CSRFProtect` + `hidden_tag()` on every form; POST-only delete/logout |
| CRUD | Create, Read, Update, Delete for transactions |
| pytest | 99 tests, isolated temporary database, CSRF re-enabled in security tests |
| Git | Commit history + branches; `.gitignore` keeps secrets out |
| GitHub Actions / CI | Auto install + `pytest` on every push and PR (Python 3.11 & 3.12) |
| Gunicorn | Production WSGI server, multi-worker, Linux only |
| Nginx | Reverse proxy; static files, HTTPS, forwards to Gunicorn |
| systemd | Auto-start and auto-restart of the app service |
| Security group | EC2 firewall: 22 = my IP, 80/443 = public |
| Cost | ≈ $12/month for a 24×7 `t3.micro`; Free Tier gives 750 h/month of `t2/t3.micro` |
| SQLite limitation | Not high availability; needs persistent storage + backups |
| Test count (remember this) | **99 passed** |
