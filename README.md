# GivSimple - Dynamic NFC Redirect Service

A secure, containerized Flask backend with admin console for managing dynamic NFC redirects to payment platforms.

## 🚀 Features

- **Dynamic Token Redirects**: Redirect users to payment pages via NFC tokens
- **Payment Platform Support**: Cash App, PayPal, Venmo, Zelle, and custom URLs
- **Admin Console**: Complete management interface for tags and users
- **Rate Limiting**: Built-in protection against abuse
- **Audit Logging**: Track all actions and changes
- **CSV Import/Export**: Bulk tag management
- **Email Notifications**: Confirmation emails for activations
- **Security**: CSRF protection, input validation, secure headers

## 📋 Requirements

- Python 3.11+
- PostgreSQL 12+ (production) or SQLite (development)
- Redis (optional, falls back to in-memory)
- Docker & Docker Compose (for containerized deployment)

## 🛠️ Quick Start

### Development Setup

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd givsimple
   cp env.example .env
   # Edit .env with your configuration
   ```

2. **Install dependencies**:
   ```bash
   make install
   # or: pip install -r requirements.txt
   ```

3. **Initialize database**:
   ```bash
   make init-db
   # or: flask db init && flask db migrate && flask db upgrade
   ```

4. **Run the application**:
   ```bash
   make run
   # or: flask run --host=0.0.0.0 --port=8000
   ```

5. **Access the application**:
   - Main app: http://localhost:8000
   - Admin console: http://localhost:8000/admin
   - Default admin: admin@givsimple.com / admin123

### Docker Setup

1. **Start all services**:
   ```bash
   docker-compose up -d
   ```

2. **Initialize database**:
   ```bash
   docker-compose exec web flask db upgrade
   ```

3. **Access the application**:
   - Main app: http://localhost:8000
   - Admin console: http://localhost:8000/admin
   - MailDev (dev): http://localhost:1080

## 📖 API Documentation

### Public Endpoints

#### `GET /t/<token>`
Redirects based on token status:
- **Active tag**: 301 redirect to target URL
- **Unassigned tag**: 302 redirect to activation page
- **Blocked/Invalid**: 404

#### `GET /activate?token=<token>`
Shows activation form for unassigned tokens.

#### `POST /api/activate`
Activates a token with user information.

**Request Body**:
```json
{
  "token": "ABC123",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "payment_handle": "$johndoe"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Token activated successfully",
  "redirect_url": "https://cash.app/$johndoe"
}
```

### Admin Endpoints

All admin endpoints require authentication at `/admin/login`.

- `GET /admin` - Dashboard
- `GET /admin/tags` - Tag management
- `GET /admin/tags/<id>` - Tag details
- `POST /admin/import` - CSV import
- `GET /admin/export` - CSV export

## 💳 Payment Platform Support

### Cash App
- **Format**: `$username` or `username`
- **Normalized**: `https://cash.app/$username`

### PayPal
- **Format**: `paypal.me/username` or `username`
- **Normalized**: `https://paypal.me/username`

### Venmo
- **Format**: `@username` or `username`
- **Normalized**: `https://venmo.com/u/username`

### Zelle
- **Format**: `zelle` (requires email/phone)
- **Normalized**: `https://givsimple.com/pay-by-zelle?email=...&phone=...`

### Custom URLs
- **Format**: Any HTTPS URL
- **Validation**: Must match allowed domains

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment (development/production) | `development` |
| `SECRET_KEY` | Flask secret key | `dev-secret-key` |
| `DATABASE_URL` | Database connection string | `sqlite:///givsimple.db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `MAIL_HOST` | SMTP server host | `localhost` |
| `MAIL_PORT` | SMTP server port | `587` |
| `MAIL_USERNAME` | SMTP username | - |
| `MAIL_PASSWORD` | SMTP password | - |
| `ADMIN_EMAIL` | Default admin email | `admin@givsimple.com` |
| `ADMIN_PASSWORD` | Default admin password | `admin123` |

### Payment Domains
Configure allowed payment domains in `app/config.py`:
```python
ALLOWED_PAYMENT_DOMAINS = [
    'cash.app',
    'paypal.me', 
    'venmo.com',
    'givsimple.com'
]
```

## 📊 Database Schema

### Tags
- `id`: Primary key
- `token`: Unique 8-16 character alphanumeric token
- `status`: unassigned/registered/active/blocked
- `target_url`: Redirect destination
- `buyer_user_id`: Associated user
- `created_at`, `updated_at`: Timestamps

### Users
- `id`: Primary key
- `name`: User's full name
- `email`: Unique email address
- `phone`: Optional phone number
- `created_at`: Registration timestamp

### Activations
- `id`: Primary key
- `tag_id`: Foreign key to tags
- `user_id`: Foreign key to users
- `payment_provider`: cashapp/paypal/venmo/zelle/generic
- `payment_handle_or_url`: Original payment handle
- `resolved_target_url`: Normalized payment URL
- `created_at`: Activation timestamp

### Audit Logs
- `id`: Primary key
- `actor`: Who performed the action
- `action`: Action description
- `tag_id`: Associated tag (optional)
- `meta`: JSON metadata
- `created_at`: Timestamp

## 🧪 Testing

### Run Tests
```bash
make test
# or: pytest -v --cov=app tests/
```

### Test Coverage
```bash
make test-html
# Opens htmlcov/index.html in browser
```

### Linting
```bash
make lint
# or: flake8 app/ tests/ && black --check app/ tests/
```

## 🐳 Docker Deployment

### Production Deployment

1. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with production values
   ```

2. **Deploy with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

3. **Initialize database**:
   ```bash
   docker-compose exec web flask db upgrade
   ```

### Docker Commands

```bash
# Build and start
docker-compose up --build

# View logs
docker-compose logs -f

# Access container shell
docker-compose exec web bash

# Database shell
docker-compose exec db psql -U givsimple -d givsimple

# Stop services
docker-compose down
```

## 📁 Project Structure

```
givsimple/
├── app/                    # Flask application
│   ├── __init__.py        # App factory
│   ├── config.py          # Configuration
│   ├── models.py          # Database models
│   ├── schemas.py         # Form schemas
│   ├── auth.py            # Authentication
│   ├── email.py           # Email functionality
│   ├── views/             # Route handlers
│   │   ├── public.py      # Public endpoints
│   │   ├── api.py         # API endpoints
│   │   └── admin.py       # Admin endpoints
│   ├── utils/             # Utilities
│   │   ├── normalize.py   # Payment normalization
│   │   └── security.py     # Security helpers
│   └── templates/         # HTML templates
├── tests/                 # Test suite
├── scripts/               # Management scripts
├── migrations/            # Database migrations
├── Dockerfile            # Container definition
├── docker-compose.yml    # Multi-service setup
├── requirements.txt       # Python dependencies
├── Makefile              # Development commands
└── README.md             # This file
```

## 🔒 Security Features

- **CSRF Protection**: All forms protected
- **Rate Limiting**: Per-IP and global limits
- **Input Validation**: Server-side validation for all inputs
- **SQL Injection Protection**: SQLAlchemy ORM
- **XSS Protection**: Template auto-escaping
- **Secure Headers**: CSP, HSTS, etc.
- **Password Hashing**: Werkzeug security
- **Audit Logging**: All actions tracked

## 📈 Monitoring & Logging

### Health Checks
- `GET /api/health` - Application health status
- Docker health checks configured

### Audit Logging
All actions are logged with:
- Actor (system/admin/user)
- Action description
- Timestamp
- Metadata (JSON)

### Rate Limiting
- Global: 100 requests/minute
- Per-IP: 10 requests/minute
- Configurable via environment

## 🚀 Production Deployment

### Recommended Setup

1. **Reverse Proxy**: Nginx or Apache
2. **SSL/TLS**: Let's Encrypt or commercial certificate
3. **Database**: PostgreSQL with backups
4. **Redis**: For rate limiting and caching
5. **Monitoring**: Application and infrastructure monitoring
6. **Backups**: Regular database backups

### Environment Variables for Production

```bash
FLASK_ENV=production
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port/db
MAIL_HOST=<smtp-server>
MAIL_USERNAME=<smtp-user>
MAIL_PASSWORD=<smtp-pass>
ADMIN_EMAIL=<admin-email>
ADMIN_PASSWORD=<strong-password>
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `make ci`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the test cases for usage examples

## 🔄 Changelog

### v1.0.0
- Initial release
- Core redirect functionality
- Admin console
- Payment platform support
- Docker deployment
- Comprehensive testing
- CI/CD pipeline
