release: python -m alembic upgrade head
web: python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT