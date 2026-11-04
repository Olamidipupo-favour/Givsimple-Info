# GivSimple

Dynamic NFC redirect service. Each NFC tag carries a token; tapping it opens the
owner's payment link. A Flask backend handles redirects, tag activation, and an
admin console for managing tags and users.

## Stack

- Python 3.11+, Flask
- SQLAlchemy and Alembic
- PostgreSQL in production, SQLite for local development
- Flask-WTF CSRF protection, Flask-Limiter rate limiting
- Redis for shared rate-limit state (falls back to memory)
- Docker Compose
- pytest

## Features

- Token redirects with active, unassigned, and blocked states
- Activation page and JSON activation API
- Cash App, PayPal, Venmo, Zelle, and allowlisted custom URLs
- Admin console for tags, blocking, and CSV import/export
- Email confirmation on activation
- Audit log
- Rate limiting per IP

## Setup

```bash
cp env.example .env
# set SECRET_KEY, ADMIN_EMAIL, and ADMIN_PASSWORD before the first run
make install
make init-db
make run
```

The app listens on `http://localhost:8000`. The admin console is at `/admin`.

`make install` uses `uv`; plain `pip install -r requirements.txt` works too.

### Docker

```bash
docker compose up -d
docker compose exec web flask db upgrade
```

MailDev runs at `http://localhost:1080` in the Compose setup.

## Configuration

| Variable | Purpose |
| -------- | ------- |
| `FLASK_ENV` | `development`, `production`, or `testing` |
| `SECRET_KEY` | Flask session signing key |
| `DATABASE_URL` | SQLAlchemy connection string |
| `REDIS_URL` | Rate-limit storage; memory is used if Redis is unavailable |
| `MAIL_HOST` `MAIL_PORT` `MAIL_USERNAME` `MAIL_PASSWORD` | SMTP settings |
| `MAIL_DEFAULT_SENDER` | From address for activation email |
| `ADMIN_EMAIL` `ADMIN_PASSWORD` | First admin account; set these before boot |
| `ALLOWED_PAYMENT_DOMAINS` | Comma-separated allowlist for custom URLs |
| `RATELIMIT_DEFAULT` `RATELIMIT_PER_IP` | Limiter thresholds |

Do not reuse the example admin password outside local development.

## Routes

| Method | Path | Purpose |
| ------ | ---- | ------- |
| `GET` | `/<token>` or `/t/<token>` | Redirect an active tag |
| `GET` | `/activate` | Activation form |
| `POST` | `/api/activate` | Activate a token |
| `GET` | `/api/health` | Health check |
| `GET` | `/admin` | Admin dashboard |
| `GET` | `/admin/tags` | Tag list |
| `POST` | `/admin/tags/<id>/block` | Block a tag |
| `GET` `POST` | `/admin/import` | CSV import |
| `GET` | `/admin/export` | CSV export |

## Tests

```bash
make test
# or
pytest
```

Test coverage is focused on token normalization, redirects, and the activation
flow.
