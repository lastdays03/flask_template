# Flask Production REST API Template

Production-ready Flask REST API backend template with JWT authentication, Celery async tasks, and Docker deployment.

## Features

- **Flask 3.x** with Application Factory pattern
- **Flask-RESTX** for automatic Swagger/OpenAPI documentation
- **JWT Authentication** with access and refresh tokens
- **SQLAlchemy ORM** with MySQL support
- **Celery** for asynchronous task processing
- **Redis** for caching and task queue
- **Rate Limiting** with Flask-Limiter
- **CORS** configuration
- **Structured JSON logging**
- **Docker & Docker Compose** for easy deployment
- **pytest** test suite with fixtures
- **Blueprint-based** modular architecture

## Tech Stack

- **Web Framework**: Flask 3.0.3, Flask-RESTX 1.3.0
- **Database**: MySQL 8.0 with SQLAlchemy ORM
- **Authentication**: Flask-JWT-Extended with bcrypt
- **Task Queue**: Celery 5.3 with Redis broker
- **Cache/Queue**: Redis 7
- **WSGI Server**: Gunicorn
- **Reverse Proxy**: Nginx
- **Testing**: pytest, pytest-flask

## Project Structure

```
flask_template/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Configuration
│   ├── extensions.py        # Flask extensions
│   ├── models/              # Database models
│   ├── api/                 # API endpoints
│   ├── schemas/             # Request/response schemas
│   ├── services/            # Business logic
│   ├── tasks/               # Celery tasks
│   └── utils/               # Utilities
├── tests/                   # Test suite
├── docker/                  # Docker configuration
├── logs/                    # Application logs
├── migrations/              # Database migrations
├── docker-compose.yml       # Docker services
├── requirements.txt         # Python dependencies
└── wsgi.py                  # WSGI entry point
```

## Quick Start

### Local Development

1. **Clone and setup**

```bash
git clone <repository-url>
cd flask_template
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
```

2. **Configure environment**

```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Start services with Docker**

```bash
docker-compose up -d mysql redis
```

4. **Initialize database**

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

5. **Run development server**

```bash
flask run
```

6. **Run Celery worker** (in separate terminal)

```bash
celery -A celery_worker.celery worker --loglevel=info
```

### Docker Deployment

```bash
# Build and start all services
docker-compose up --build -d

# Run migrations
docker-compose exec app flask db upgrade

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## API Documentation

Once the application is running, visit:

- **Swagger UI**: http://localhost:5000/api/docs
- **Health Check**: http://localhost:5000/api/health

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get tokens
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info

### Users

- `GET /api/users` - List users (paginated)
- `GET /api/users/<id>` - Get user by ID
- `PUT /api/users/<id>` - Update user
- `DELETE /api/users/<id>` - Delete user (soft delete)

### Health

- `GET /api/health` - Service health check

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html tests/

# Run specific test file
pytest tests/test_auth.py -v
```

## Environment Variables

Required environment variables (see `.env.example`):

```bash
# Flask
FLASK_APP=wsgi.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# Database
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/flask_app

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Rate Limiting
RATELIMIT_STORAGE_URL=redis://localhost:6379/2
```

## Development

### Code Formatting

```bash
black app/ tests/
flake8 app/ tests/
```

### Database Migrations

```bash
# Create migration
flask db migrate -m "Description"

# Apply migration
flask db upgrade

# Rollback migration
flask db downgrade
```

### Adding New Endpoints

1. Create schema in `app/schemas/`
2. Create service in `app/services/`
3. Create API endpoint in `app/api/`
4. Register namespace in `app/__init__.py`
5. Add tests in `tests/`

## Production Deployment

1. Set `FLASK_ENV=production` in `.env`
2. Generate strong `SECRET_KEY` and `JWT_SECRET_KEY`
3. Configure production database URL
4. Set proper `CORS_ORIGINS`
5. Use `docker-compose up -d` for deployment
6. Set up SSL/TLS with Let's Encrypt
7. Configure log aggregation (ELK, Datadog, etc.)
8. Set up monitoring (Prometheus, Grafana, etc.)

## Security

- JWT tokens with configurable expiration
- Password hashing with bcrypt
- Rate limiting on authentication endpoints
- CORS configuration
- SQL injection protection via SQLAlchemy ORM
- Input validation with Flask-RESTX

## License

MIT License

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request
