# Migrations

This project uses Alembic for PostgreSQL schema migrations.

Typical workflow for local development:

```bash
cd backend
.venv\Scripts\activate
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

If the database has not been created yet:

1. Start the Docker services.
2. Make sure `.env` points to the local database.
3. Run `alembic upgrade head`.

Do not edit existing migration files by hand unless you understand the implications.
