## FastAPI application that emulates payment service
<br/>

Runs on *Python 3.12.2*

Uses *FastAPI 0.115.12*, *SQLAlchemy 2.0.40*, *PostgreSQL 17*

Prepared to build with *Docker-compose*

All requirements are listed in [requirements.txt](/app/requirements.txt)

DB is prepopulated with test data from initial migrations

Task description for the API: [task_description.docx](/task_description.docx)

<br/><br/>

### Options to build the app

**Option 1 (most simple).** With docker-compose:

Start containers: `docker-compose up --build -d`

**Option 2 (requires a little setup).** Locally with installation script:

This option requires passwordless connection to psql for root user. If you set up your "postgres" PostgreSQL user to have trusted connection without password via pg_hba.conf ([guide](https://www.postgresql.org/docs/current/auth-trust.html)), you can simply install the app by executing:
- [setup.sh](/setup.sh) for Linux
- [setup.bat](/setup.bat) for Windows

**Option 3 (hardcore).** Locally with manual setup:

- Create PostgreSQL database and user according to [.env](/.env) file credentials
- Activate venv `source ./venv/bin/activate` for Linux; `.\venv\Scripts\activate` for Windows
- Install dependencies `pip install -r ./app/requirements.txt && pip install pip install -e .`
- Apply migrations `alembic upgrade head`
- Start the app `uvicorn app.main:app --host 0.0.0.0 --port 8000`

<br/>

**Open in browser to access SwaggerUI:** `http://localhost:8000/docs`

<br/>

### What you can do with the app

Log in as a test user: user@example.com userpassword
Log in as a test admin: admin@example.com adminpassword

Use endpoints according to the user role

Test a payment with this example request: 

{
  "transaction_id": "5eae174f-7cd0-472c-bd36-35660f00132b",
  "user_id": 1,
  "account_id": 1,
  "amount": 100,
  "signature": "7b47e41efe564a062029da3367bde8844bea0fb049f894687cee5d57f2858bc8"
}


Run autotests:
- docker exec -it app_payments pytest -v (in container)
- pytest -v (locally)

<br/>

**App shutdown:** 
- For docker: `docker-compose down -v`
- For local setup: `Ctrl+C` -> `deactivate`